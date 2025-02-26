import logging
import gradio as gr
from yt_dlp import YoutubeDL
import os
from dotenv import load_dotenv
from pathlib import Path
import time
from tqdm import tqdm
import tempfile

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('youtube_downloader')

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def cookies_to_env(cookie_file_path: str) -> str:
    """Convert cookie file content to environment variable format"""
    try:
        with open(cookie_file_path, 'r') as f:
            lines = f.readlines()
            
        header = [line.strip() for line in lines if line.startswith('#')]
        cookies = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        
        content = '\\n'.join(header + [''] + cookies) 
        
        return f'FIREFOX_COOKIES="{content}"'
    
    except Exception as e:
        raise ValueError(f"Error converting cookie file: {str(e)}")

def env_to_cookies(env_content: str, output_file: str) -> None:
    """Convert environment variable content back to cookie file"""
    try:
        if '="' not in env_content:
            raise ValueError("Invalid env content format")
            
        content = env_content.split('="', 1)[1].strip('"')
        
        cookie_content = content.replace('\\n', '\n')
        
        with open(output_file, 'w') as f:
            f.write(cookie_content)
            
    except Exception as e:
        raise ValueError(f"Error converting to cookie file: {str(e)}")

def save_to_env_file(env_content: str, env_file: str = '.env') -> None:
    """Save environment variable content to .env file"""
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
    except Exception as e:
        raise ValueError(f"Error saving to env file: {str(e)}")

def env_to_cookies_from_env(output_file: str) -> None:
    """Convert environment variable from .env file to cookie file"""
    try:
        load_dotenv()
        env_content = os.getenv('FIREFOX_COOKIES', "")
        if not env_content:
            raise ValueError("FIREFOX_COOKIES not found in .env file")
            
        env_to_cookies(f'FIREFOX_COOKIES="{env_content}"', output_file)
    except Exception as e:
        raise ValueError(f"Error converting to cookie file: {str(e)}")

def get_cookies():
    """Get cookies from environment variable"""
    load_dotenv()
    cookie_content = os.getenv('FIREFOX_COOKIES', "")
    if not cookie_content:
        raise ValueError("FIREFOX_COOKIES environment variable not set")
    return cookie_content

def create_temp_cookie_file():
    """Create temporary cookie file from environment variable"""
    temp_cookie = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt')
    try:
        cookie_content = get_cookies()
        cookie_content = cookie_content.replace('\\n', '\n')
        temp_cookie.write(cookie_content)
        temp_cookie.flush()
        return Path(temp_cookie.name)
    finally:
        temp_cookie.close()

def download_for_browser(url, mode='audio', quality='high', audio_format='mp3', video_format='mp4'):
    if not url:
        return None, "Please enter a valid URL"
    logger.info(f"Downloading {url} in {mode} mode with {quality} quality, audio format {audio_format}, video format {video_format}")

    try:
        pbar = tqdm(unit='B', unit_scale=True, unit_divisor=1024, miniters=1, desc=url.split("watch?v=")[-1] if "watch?v=" in url else "Download")

        def progress_hook(d):
            if d['status'] == 'downloading':
                if 'total_bytes' in d:
                    pbar.total = d['total_bytes']
                pbar.update(d['downloaded_bytes'] - pbar.n)
            if d['status'] == 'finished':
                pbar.close()
            if d['status'] == 'error':
                pbar.close()
                logger.error(f"Download error: {d['error']}")

        opts = {
            'format': 'bestaudio/best' if mode == 'audio' else 'bestvideo+bestaudio/best',
            'outtmpl': str(OUTPUT_DIR / '%(title)s.%(ext)s'),
            'restrictfilenames': True,
            'windowsfilenames': True,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [progress_hook],
        }
        
        if mode == 'audio':
            opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                    'preferredquality': '320' if quality == 'high' else '192',
                }],
                'prefer_ffmpeg': True,
                'keepvideo': False
            })
        else:
            if video_format == 'mp4':
                format_spec = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            elif video_format == 'webm':
                format_spec = 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best'
            else:
                format_spec = 'bestvideo+bestaudio/best'
                
            opts.update({
                'format': format_spec,
                'merge_output_format': video_format,
                'postprocessor_args': ['-c:v', 'copy', '-c:a', 'copy'],
                'prefer_ffmpeg': True
            })

        load_dotenv()
        USE_FIREFOX_COOKIES = os.getenv("USE_FIREFOX_COOKIES", "False")
        if USE_FIREFOX_COOKIES == "True":
            cookiefile = "firefox-cookies.txt"
            env_to_cookies_from_env("firefox-cookies.txt")

            logger.info(f"Using Firefox cookies: {USE_FIREFOX_COOKIES}")
            opts["cookiefile"] = "firefox-cookies.txt"
        else:
            opts["no_cookies"] = True  

        logger.info(f"Downloading {url} with options: {opts}")
        start_time = time.time()
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"Download started at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
        logger.info(f"Download completed at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        logger.info(f"Download time: {elapsed_time:.2f} seconds")

        files = list(OUTPUT_DIR.glob('*'))
        if not files:
            return None, "Download failed - no files found in output directory"

        download_file = None
        for file in files:
            if file.name.startswith(info['title']):
                if download_file is None or file.stat().st_mtime > download_file.stat().st_mtime:
                    download_file = file

        if download_file is None or not download_file.exists():
            return None, "File download in output directory failed"

        logger.info(f"Downloaded file: {download_file.name}")
        return f"Successfully converted: {download_file.name} saved to outputs folder", None

    except Exception as e:
        error_msg = str(e)
        if "ERROR: [youtube]" in error_msg:
            error_msg = error_msg.split("ERROR: [youtube]")[1].strip()
        logger.error(f"Download error: {error_msg}")
        return None, error_msg

def create_browser_ui():
    
    with gr.Blocks(
        title="YouTube Downloader",
        theme=gr.themes.Soft(primary_hue="red", secondary_hue="indigo"),
        css="""
        .container { max-width: 900px; margin: 0 auto; }
        .header-img { margin-bottom: 1rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .download-btn { min-height: 60px !important; font-size: 1.2em !important; }
        .status-box { min-height: 100px; }
        footer { text-align: center; margin-top: 2rem; padding: 1rem; border-top: 1px solid #eee; }
        """
    ) as demo:

        gr.Markdown("""
        <div style='text-align: center;'>
            <div style='background: linear-gradient(135deg, #ff0000 0%, #ff5500 100%); padding: 20px; border-radius: 15px; margin-bottom: 20px;'>
                <h1 style='display: flex; align-items: center; justify-content: center; gap: 15px; margin: 0;'>
                    <img src='https://cdn-icons-png.flaticon.com/512/1384/1384060.png' width='60' style='filter: drop-shadow(0 2px 5px rgba(0,0,0,0.2));'/> 
                    <span style='font-size: 2.5em; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>YouTube Downloader</span>
                </h1>
                <p style='font-size: 1.3em; color: white; margin-top: 10px; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);'>
                    Download your favorite YouTube videos and audio with ease!
                </p>
            </div>
        </div>
        """)
        
        with gr.Row(equal_height=True):
            with gr.Column(scale=2):
                url_input = gr.Textbox(
                    label="YouTube URL",
                    placeholder="Enter YouTube URL here (e.g., https://youtube.com/watch?v=...)",
                    scale=2,
                    elem_id="url_input",
                    container=False,
                )
                
                with gr.Row():
                    with gr.Column(scale=1):
                        mode_input = gr.Radio(
                            choices=["audio", "video"],
                            value="audio",
                            label="Format",
                            elem_id="mode_input",
                            container=True,
                            interactive=True,
                        )
                    
                    with gr.Column(scale=1):
                        quality_input = gr.Radio(
                            choices=["high", "medium"],
                            value="high",
                            label="Quality",
                            elem_id="quality_input",
                            container=True,
                        )
                
                with gr.Row():
                    with gr.Column():
                        audio_format_input = gr.Dropdown(
                            choices=["mp3", "wav", "m4a", "flac", "opus"],
                            value="mp3",
                            label="Audio Format",
                            visible=True,
                            elem_id="audio_format_input",
                            container=True,
                        )
                        
                        video_format_input = gr.Dropdown(
                            choices=["mp4", "webm", "mkv"],
                            value="mp4",
                            label="Video Format",
                            visible=False,
                            elem_id="video_format_input",
                            container=True,
                        )
                
                with gr.Row():
                    download_button = gr.Button(
                        "⬇️ Download Now", 
                        variant="primary", 
                        elem_id="download_button",
                        elem_classes="download-btn",
                        size="lg",
                    )

            with gr.Column(scale=1):
                status_text = gr.Textbox(
                    label="Download Status",
                    interactive=False,
                    elem_id="status_text",
                    elem_classes="status-box",
                    lines=4,
                )
                
                gr.Markdown("""
                <div style='background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); padding: 15px; border-radius: 10px; margin-top: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>
                    <h3 style='margin-top: 0; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);'>📋 Instructions</h3>
                    <ol style='margin-bottom: 0; padding-left: 20px; color: white;'>
                        <li>Paste a YouTube URL</li>
                        <li>Select format (audio/video)</li>
                        <li>Choose quality</li>
                        <li>Click Download</li>
                    </ol>
                </div>
                """)
                
        gr.Markdown("""
        <footer>
            <p>Files are saved to the outputs folder. Powered by yt-dlp and FFmpeg.</p>
        </footer>
        """)
                
        def update_format_visibility(mode):
            return [
                gr.Dropdown(visible=mode == "audio"),  
                gr.Dropdown(visible=mode == "video")   
            ]

        mode_input.change(
            update_format_visibility,
            inputs=[mode_input],
            outputs=[audio_format_input, video_format_input]
        )

        download_button.click(
            fn=download_for_browser,
            inputs=[url_input, mode_input, quality_input, audio_format_input, video_format_input],
            outputs=[status_text]
        )

    return demo

demo = create_browser_ui()
demo.launch(
    share=False,
    debug=False,
    show_error=False
)