import yt_dlp
import os

# Explicit ffmpeg path
FFMPEG_PATH = r'C:\ffmpeg-8.0-essentials_build\ffmpeg-8.0-essentials_build\bin\ffmpeg.exe'

def get_media_info(url):
    """Get all available video/audio formats for a URL."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'ffmpeg_location': FFMPEG_PATH,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        formats = []
        for f in info.get('formats', []):
            # Include video or audio streams
            if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                # Build readable label
                if f.get('vcodec') != 'none':
                    label = f"{f.get('height', 'Unknown')}p"
                else:
                    label = "Audio only"

                # Format filesize
                size = f.get('filesize') or f.get('filesize_approx')
                if size:
                    size_mb = round(size / (1024 * 1024), 2)
                    label += f" ({size_mb} MB)"

                formats.append({
                    "format_id": f['format_id'],
                    "ext": f['ext'],
                    "resolution": label,
                })

        return {
            "title": info.get('title'),
            "thumbnail": info.get('thumbnail'),
            "formats": formats
        }


def download_media(url, format_id):
    """Download selected format (video or audio) and return file path."""
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': format_id,
        'noplaylist': True,
        'merge_output_format': 'mp4',  # video+audio will be merged
        'ffmpeg_location': FFMPEG_PATH,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        return file_path


def download_audio(url):
    """Download best audio as mp3."""
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_location': FFMPEG_PATH,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = os.path.splitext(ydl.prepare_filename(info))[0] + '.mp3'
        return filename
