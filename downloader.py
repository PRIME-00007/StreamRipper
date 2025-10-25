import os
import requests

# Directory for downloads
OUTPUT_DIR = "downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Choose a free Invidious instance
INVIDIOUS_BASE = "https://invidious.snopyta.org"


def get_video_id(url):
    """Extract YouTube video ID from URL."""
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL")


def get_media_info(url):
    """Fetch video info using Invidious API."""
    video_id = get_video_id(url)
    api_url = f"{INVIDIOUS_BASE}/api/v1/videos/{video_id}"
    resp = requests.get(api_url)
    if resp.status_code != 200:
        raise Exception("Failed to fetch video info from Invidious")

    data = resp.json()
    formats = []

    # adaptiveFormats contains direct video/audio URLs
    for f in data.get("adaptiveFormats", []):
        # Only include streams with a URL
        if not f.get("url"):
            continue

        if f.get("videoQuality"):
            label = f"{f['videoQuality']}"
        else:
            label = "Audio only"

        filesize = f.get("contentLength")
        if filesize:
            size_mb = round(int(filesize) / (1024 * 1024), 2)
            label += f" ({size_mb} MB)"

        formats.append({
            "format_id": f.get("itag"),
            "ext": f.get("mimeType", "").split("/")[1],
            "resolution": label,
            "url": f.get("url")
        })

    return {
        "title": data.get("title"),
        "thumbnail": data.get("videoThumbnails")[0]["url"] if data.get("videoThumbnails") else None,
        "formats": formats
    }


def download_media(url, format_id):
    """Download selected video/audio by fetching the direct URL."""
    info = get_media_info(url)
    stream = next((f for f in info["formats"] if str(f["format_id"]) == str(format_id)), None)
    if not stream:
        raise Exception("Format ID not found")

    filename = os.path.join(OUTPUT_DIR, f"{info['title']}.{stream['ext']}")
    # Download the file
    with requests.get(stream["url"], stream=True) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return filename


def download_audio(url):
    """Download best audio as mp3."""
    info = get_media_info(url)
    # Choose first audio-only stream
    stream = next((f for f in info["formats"] if "audio" in f["ext"]), None)
    if not stream:
        raise Exception("No audio stream found")

    filename = os.path.join(OUTPUT_DIR, f"{info['title']}.mp3")
    with requests.get(stream["url"], stream=True) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return filename
