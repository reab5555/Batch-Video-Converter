# Batch Video Converter

A simple and user-friendly GUI-based batch video converter designed to make video conversions to different formats. This tool uses `Gradio` for an intuitive interface and `FFmpeg` for robust video processing. GPU acceleration is supported for faster performance when available.

---

## Features

This tool enables batch video conversion with support for popular formats like MP4, MKV, AVI, and MOV. It offers advanced codec options such as H.264, HEVC (H.265), and ProRes, ensuring compatibility with various needs.  

You can customize output settings like resolution (4K, 1080p, 720p, etc.), bitrate (manual or auto), and frame rate (same as input or specific values like 30 or 60 FPS). 

The interface provides real-time conversion progress updates and makes downloading results straightforward. GPU acceleration is available to significantly speed up processing.

---

## How It Works

1. **Upload Videos**: Drag and drop one or multiple video files.
2. **Set Preferences**: Choose output format, codec, resolution, bitrate, and frame rate.
3. **Preview**: Check the video preview if needed.
4. **Convert**: Click the "Convert Videos" button to start the process.
5. **Download**: Retrieve your converted videos directly from the interface.

---

## System Requirements

The tool works on Windows and Linux systems. You need Python 3.8 or higher, `Gradio` for the GUI, and `FFmpeg` installed on your machine. If a CUDA-enabled GPU is present, the tool can use it for faster conversion.

---

## Example Usage

Run the application:
```bash
python app.py
