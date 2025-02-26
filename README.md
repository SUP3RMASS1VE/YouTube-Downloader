# YouTube Downloader

## Overview
The YouTube Downloader is a web-based application that allows users to download YouTube videos and audio in various formats and qualities. It is powered by `yt-dlp` and `FFmpeg` and provides an easy-to-use interface for seamless downloading.

## Features
- Download YouTube videos in multiple formats (MP4, WebM, MKV)
- Extract audio from videos in various formats (MP3, WAV, M4A, FLAC, OPUS)
- Select between high and medium quality for downloads
- Supports cookies for authenticated downloads
- User-friendly UI built with Gradio

## Installation
### Prerequisites
Ensure you have the following installed:
- Python 3.8+
- `yt-dlp`
- `FFmpeg`
- `gradio`
- `tqdm`
- `python-dotenv`

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/youtube-downloader.git
   cd youtube-downloader
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the `.env` file (optional for cookies support):
   ```bash
   echo 'FIREFOX_COOKIES="your_cookie_content"' > .env
   ```

## Usage
Run the application using:
```bash
python app.py
```
Then, open the web interface and enter the YouTube URL, select your preferred format and quality, and download the file.

## UI Overview
- **YouTube URL**: Enter the URL of the video you want to download.
- **Format Selection**: Choose between "Audio" or "Video".
- **Quality Selection**: Select "High" or "Medium" quality.
- **Audio/Video Format**: Choose the desired file format for the download.
- **Download Button**: Click to start the download process.
- **Status Box**: Displays progress and status messages.

## File Storage
All downloaded files are saved in the `outputs/` directory inside the project folder.

## Troubleshooting
- If the download fails, ensure that `yt-dlp` and `FFmpeg` are properly installed.
- Check your internet connection.
- If authentication is required, use Firefox cookies by setting up the `.env` file.

## License
This project is licensed under the MIT License.

## Credits
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Gradio](https://www.gradio.app/)
- [FFmpeg](https://ffmpeg.org/)

