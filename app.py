from flask import Flask, render_template, request, jsonify
import requests
import os
import traceback
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

# ----------- CONFIG -----------
INVIDIOUS_INSTANCES = [
    "https://invidious.snopyta.org",
    "https://yewtu.be",
    "https://inv.nadeko.net",
]
TIMEOUT = 8


# ----------- HELPERS -----------
def extract_video_id(url: str):
    """Extract the YouTube video ID from a given URL."""
    parsed = urlparse(url)
    if 'youtube' in parsed.netloc or 'youtu.be' in parsed.netloc:
        if parsed.netloc == "youtu.be":
            return parsed.path.strip("/")
        query = parse_qs(parsed.query)
        return query.get("v", [parsed.path.strip("/")])[-1]
    return url  # fallback if not recognized


def fetch_from_invidious(video_id: str):
    """Try fetching video info from multiple Invidious instances."""
    last_error = None
    for base_url in INVIDIOUS_INSTANCES:
        try:
            api_url = f"{base_url}/api/v1/videos/{video_id}"
            resp = requests.get(api_url, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            last_error = e
            continue
    raise Exception(f"All Invidious instances failed: {last_error}")


# ----------- ROUTES -----------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/validate', methods=['POST'])
def validate():
    """Validate a YouTube URL and return metadata + formats."""
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        video_id = extract_video_id(url)
        data = fetch_from_invidious(video_id)

        # Extract metadata and available formats
        info = {
            "title": data.get("title"),
            "author": data.get("author"),
            "thumbnail": data.get("videoThumbnails", [{}])[0].get("url"),
            "formats": []
        }

        # Gather adaptive formats (video/audio)
        for f in data.get("adaptiveFormats", []) + data.get("formatStreams", []):
            # Skip broken or DRM formats
            if not f.get("url"):
                continue
            fmt = {
                "itag": f.get("itag"),
                "type": f.get("type") or f.get("mimeType"),
                "quality": f.get("qualityLabel") or f.get("quality"),
                "bitrate": f.get("bitrate"),
                "size": f.get("size") or f.get("contentLength"),
            }
            info["formats"].append(fmt)

        return jsonify(info)

    except Exception as e:
        print("Error in /validate:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/download_link', methods=['GET'])
def download_link():
    """Get the direct URL of a specific format."""
    url = request.args.get('url')
    format_id = request.args.get('format')

    if not url or not format_id:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        video_id = extract_video_id(url)
        data = fetch_from_invidious(video_id)
        formats = data.get("adaptiveFormats", []) + data.get("formatStreams", [])

        selected = next((f for f in formats if str(f.get("itag")) == str(format_id)), None)
        if not selected:
            return jsonify({'error': 'Format not found'}), 404

        return jsonify({
            "url": selected.get("url"),
            "mimeType": selected.get("type") or selected.get("mimeType"),
            "quality": selected.get("qualityLabel") or selected.get("quality"),
        })

    except Exception as e:
        print("Error in /download_link:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ----------- MAIN -----------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
