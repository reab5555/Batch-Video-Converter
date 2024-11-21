import gradio as gr
import os
from pathlib import Path
from datetime import datetime
from converter_fw import VideoConverter
import tempfile
import shutil


class VideoConverterGUI:
    def __init__(self):
        self.converter = VideoConverter()
        self.current_progress = 0
        self.status_message = ""
        self.output_dir = os.path.join(os.getcwd(), "converted_videos")
        os.makedirs(self.output_dir, exist_ok=True)

        # Define video extensions
        self.video_extensions = [
            ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".mpeg",
            ".MP4", ".AVI", ".MKV", ".MOV", ".WMV", ".FLV", ".MPEG"
        ]

    def generate_output_filename(self, input_filename, output_format):
        name = Path(input_filename).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{name}_{timestamp}.{output_format.lower()}"

    def update_video_display(self, files):
        """Update the video preview"""
        if not files or len(files) == 0:
            return None
        return files[0]

    def create_temp_copy(self, file_path):
        """Create a temporary copy of the input file"""
        file_ext = os.path.splitext(file_path)[1]
        temp_file = tempfile.NamedTemporaryFile(suffix=file_ext, delete=False)
        temp_path = temp_file.name
        temp_file.close()
        shutil.copy2(file_path, temp_path)
        return temp_path

    def is_valid_video(self, file_path):
        """Check if file has a valid video extension"""
        return any(file_path.lower().endswith(ext.lower()) for ext in self.video_extensions)

    def convert_videos(self, files, output_format, codec, resolution, bitrate, bitrate_unit, fps, progress=gr.Progress()):
        if not files:
            return "Please upload video files.", []

        results = []
        output_files = []
        temp_files = []

        # Filter valid video files
        valid_files = [f for f in files if self.is_valid_video(f.name)]

        if not valid_files:
            return "No valid video files found. Please upload video files.", []

        total_files = len(valid_files)
        file_weight = 1.0 / total_files

        # Process bitrate input
        if bitrate.strip().lower() != "auto" and bitrate.strip() != "":
            try:
                bitrate_value = float(bitrate)
                if bitrate_unit == "kbps":
                    bitrate_value = f"{bitrate_value}k"
                elif bitrate_unit == "Mbps":
                    bitrate_value = f"{bitrate_value}M"
                else:
                    return "Invalid bitrate unit selected.", []
            except ValueError:
                return f"Invalid bitrate value: {bitrate}. Please enter a numeric value.", []
        else:
            bitrate_value = "auto"

        try:
            for i, file in enumerate(valid_files):
                try:
                    base_progress = i * file_weight

                    # Create a temporary copy of the input file
                    temp_input_path = self.create_temp_copy(file.name)
                    temp_files.append(temp_input_path)

                    original_filename = os.path.basename(file.name)
                    progress(base_progress, desc=f"Converting {original_filename}")

                    def progress_callback(file_progress):
                        total_progress = base_progress + (file_progress * file_weight)
                        progress(total_progress)

                    output_filename = self.generate_output_filename(original_filename, output_format)

                    print(f"Converting {temp_input_path} to {output_filename}")  # Debug print

                    success, message = self.converter.convert_video(
                        temp_input_path,
                        output_format,
                        codec,
                        self.output_dir,
                        progress_callback,
                        output_filename,
                        resolution,
                        bitrate_value,
                        fps
                    )

                    if success:
                        output_path = os.path.join(self.output_dir, output_filename)
                        if os.path.exists(output_path):
                            output_files.append(output_path)
                    results.append(message)

                except Exception as e:
                    print(f"Detailed error for {file.name}: {str(e)}")  # Debug print
                    results.append(f"Error processing {os.path.basename(file.name)}: {str(e)}")

        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    print(f"Error cleaning up {temp_file}: {str(e)}")

        success_count = sum(1 for msg in results if "Successfully" in msg)
        report = f"Conversion completed: {success_count}/{total_files} files converted successfully\n\n"
        report += "\n".join(results)

        return report, output_files if output_files else None

    def create_ui(self):
        with gr.Blocks() as app:
            gr.Markdown(f"""
            # Batch Video Converter
            GPU Acceleration: {"Available" if self.converter.gpu_available else "Not Available"}
            """)

            with gr.Column():
                # Input Settings Section
                gr.Markdown("### Input Settings")
                with gr.Row():
                    with gr.Column(scale=1):
                        input_videos = gr.Files(
                            label="Upload Videos",
                            file_count="multiple",
                            file_types=["video"],
                            type="filepath"
                        )
                with gr.Row():
                    preview = gr.Video(
                        label="Video Preview",
                        format="mp4",
                        visible=True,
                        interactive=False
                     )

                # Conversion Settings Section
                gr.Markdown("### Conversion Settings")
                with gr.Row():
                    format_dropdown = gr.Dropdown(
                        choices=self.converter.formats,
                        value="MP4",
                        label="Output Format"
                    )
                    codec_dropdown = gr.Dropdown(
                        choices=self.converter.codecs,
                        value="H.264",
                        label="Codec"
                    )
                # Add output resolution, bitrate, and fps options
                with gr.Row():
                    resolution_dropdown = gr.Dropdown(
                        choices=[
                            "Same as input",
                            "3840x2160 (4K)",
                            "2560x1440 (1440p)",
                            "1920x1080 (1080p)",
                            "1280x720 (720p)",
                            "854x480 (480p)"
                        ],
                        value="Same as input",
                        label="Output Resolution"
                    )
                with gr.Row():
                    bitrate_input = gr.Textbox(
                        label="Output Bitrate",
                        placeholder="Enter value or leave blank for auto",
                        value=""
                    )
                    bitrate_unit = gr.Dropdown(
                        choices=["kbps", "Mbps"],
                        value="Mbps",
                        label="Bitrate Unit"
                    )
                with gr.Row():
                    fps_dropdown = gr.Dropdown(
                        choices=[
                            "Same as input",
                            "23.97",
                            "24",
                            "25",
                            "29.97",
                            "30",
                            "60"
                        ],
                        value="Same as input",
                        label="Output FPS"
                    )

                # Conversion Button and Progress Section
                convert_btn = gr.Button(
                    "Convert Videos",
                    variant="primary",
                    size="lg"
                )
                gr.Markdown("### Conversion Progress")
                output_text = gr.Textbox(
                    label="Status",
                    lines=10,
                    show_copy_button=True
                )

                # Download Section
                gr.Markdown("### Download Converted Videos")
                output_files = gr.Files(
                    label="Converted Videos (Click to download)",
                    interactive=False
                )

            # Event handlers
            input_videos.change(
                fn=self.update_video_display,
                inputs=[input_videos],
                outputs=[preview]
            )

            convert_btn.click(
                fn=self.convert_videos,
                inputs=[
                    input_videos,
                    format_dropdown,
                    codec_dropdown,
                    resolution_dropdown,
                    bitrate_input,
                    bitrate_unit,
                    fps_dropdown
                ],
                outputs=[
                    output_text,
                    output_files
                ]
            )

        return app

    def main(self):
        gui = VideoConverterGUI()
        app = gui.create_ui()
        app.launch()

if __name__ == "__main__":
    VideoConverterGUI().main()
