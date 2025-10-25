import yt_dlp
import os

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_media_info(url):
    """Get all available video/audio formats for a URL using yt-dlp."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        formats = []
        for f in info.get('formats', []):
            if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                label = f"{f.get('height', 'Audio')}p" if f.get('vcodec') != 'none' else "Audio only"
                size = f.get('filesize') or f.get('filesize_approx')
                if size:
                    label += f" ({round(size / (1024 * 1024), 2)} MB)"
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
    """Download selected video/audio format."""
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'format': format_id,
        'noplaylist': True,
        'merge_output_format': 'mp4',  # video+audio merged
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        return file_path


def download_audio(url):
    """Download best audio as mp3."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = os.path.splitext(ydl.prepare_filename(info))[0] + '.mp3'
        return filename
