import os
import re
import subprocess
import torch
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
import platform

class VideoConverter:
    def __init__(self):
        # Check the operating system
        if platform.system() == 'Windows':
            # Windows-specific FFmpeg path
            self.ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")
        else:
            # On Linux, assume FFmpeg is installed and available in PATH
            self.ffmpeg_path = "ffmpeg"
        self.gpu_available = torch.cuda.is_available()
        self.formats = ["MP4", "MKV", "AVI", "MOV", "WMV", "FLV", "MPEG"]
        self.codecs = [
            "H.264",
            "HEVC (H.265)",
            "MPEG-4 (Part 2)",
            "MPEG-2",
            "ProRes Proxy",
            "ProRes Light",
            "ProRes Standard",
            "ProRes HQ"
        ]

    def get_codec_params(self, codec: str) -> List[str]:
        codec_params = {
            "H.264": ["-c:v", "libx264", "-preset", "medium"],
            "HEVC (H.265)": ["-c:v", "libx265", "-preset", "medium"],
            "MPEG-4 (Part 2)": ["-c:v", "mpeg4"],
            "MPEG-2": ["-c:v", "mpeg2video"],
            "ProRes Proxy": ["-c:v", "prores_ks", "-profile:v", "0"],
            "ProRes Light": ["-c:v", "prores_ks", "-profile:v", "1"],
            "ProRes Standard": ["-c:v", "prores_ks", "-profile:v", "2"],
            "ProRes HQ": ["-c:v", "prores_ks", "-profile:v", "3"]
        }
        return codec_params.get(codec, ["-c:v", "libx264", "-preset", "medium"])

    def get_video_duration(self, input_path: str) -> float:
        cmd = [
            self.ffmpeg_path,
            "-i",
            input_path
        ]
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            for line in output.split('\n'):
                if "Duration" in line:
                    time_str = line.split("Duration: ")[1].split(",")[0]
                    h, m, s = time_str.split(':')
                    return float(h) * 3600 + float(m) * 60 + float(s)
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return 0

    def convert_video(
            self,
            input_path: str,
            output_format: str,
            codec: str,
            output_dir: str,
            progress_callback: Optional[callable] = None,
            output_filename: Optional[str] = None,
            output_resolution: str = "Same as input",
            output_bitrate: str = "auto",
            output_fps: str = "Same as input"
    ) -> Tuple[bool, str]:
        try:
            if not os.path.exists(input_path):
                return False, f"Input file does not exist: {Path(input_path).name}"

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            output_path = os.path.join(output_dir, output_filename)

            # Base FFmpeg command
            cmd = [
                self.ffmpeg_path,
                "-y"
            ]

            # Add GPU acceleration if available
            if self.gpu_available:
                if codec in ["H.264", "HEVC (H.265)"]:
                    cmd.extend(["-hwaccel", "cuda"])

            # Add input file
            cmd.extend([
                "-i", input_path
            ])

            # Add codec parameters
            cmd.extend(self.get_codec_params(codec))

            # Add scaling if necessary
            if output_resolution != "Same as input":
                resolution_map = {
                    "3840x2160 (4K)": "3840:2160",
                    "2560x1440 (1440p)": "2560:1440",
                    "1920x1080 (1080p)": "1920:1080",
                    "1280x720 (720p)": "1280:720",
                    "854x480 (480p)": "854:480"
                }
                scale = resolution_map.get(output_resolution)
                if scale:
                    cmd.extend(["-vf", f"scale={scale}"])

            # Add FPS if specified
            if output_fps != "Same as input":
                cmd.extend(["-r", output_fps])

            # Add bitrate or CRF settings
            if output_bitrate.lower() != "auto":
                cmd.extend(["-b:v", output_bitrate])
            else:
                # Use a default CRF value for quality
                cmd.extend(["-crf", "23"])

            # Optionally, you can add audio codec settings
            # cmd.extend(["-c:a", "aac", "-b:a", "128k"])

            # Add output file
            cmd.append(output_path)

            # Print the FFmpeg command for debugging
            print("FFmpeg command:", ' '.join(cmd))

            duration = self.get_video_duration(input_path)
            print(f"Video duration: {duration} seconds")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr into stdout
                universal_newlines=True
            )

            while True:
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    continue

                # Print the line for debugging
                print("FFmpeg output:", line.strip())

                if "frame=" in line and progress_callback and duration > 0:
                    # Extract time from the output
                    match = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                    if match:
                        time_str = match.group(1)
                        h, m, s = time_str.split(':')
                        current_time = float(h) * 3600 + float(m) * 60 + float(s)
                        progress = current_time / duration
                        progress_callback(progress)

            process.wait()

            if process.returncode == 0:
                return True, f"Successfully converted: {output_filename}"
            else:
                error_output = process.stdout.read()
                return False, f"Error converting {Path(input_path).name}: FFmpeg error code {process.returncode}\n{error_output}"

        except Exception as e:
            return False, f"Error converting {Path(input_path).name}: {str(e)}"
