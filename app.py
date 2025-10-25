from flask import Flask, render_template, request, send_file, jsonify, after_this_request
import os
import traceback
import requests
from downloader import download_media, download_audio, get_media_info  # your existing downloader logic

app = Flask(__name__)

# ---------- CONFIG ----------
INVIDIOUS_INSTANCES = [
    "https://invidious.snopyta.org",
    "https://yewtu.be",
    "https://vid.puffyan.us",
    # Add more public instances if needed
]

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------- INDEX ----------
@app.route('/')
def index():
    return render_template('index.html')

# ---------- HELPER: FETCH VIDEO INFO ----------
def fetch_video_info(video_id):
    for instance in INVIDIOUS_INSTANCES:
        try:
            resp = requests.get(f"{instance}/api/v1/videos/{video_id}", timeout=5)
            if resp.status_code == 200:
                print(f"Invidious succeeded: {instance}")
                return resp.json()
        except Exception as e:
            print(f"Invidious instance failed: {instance} -> {e}")
    raise Exception("All Invidious instances failed.")

# ---------- VALIDATE ----------
@app.route('/validate', methods=['POST'])
def validate():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # Extract video ID
        if "watch?v=" in url:
            video_id = url.split("watch?v=")[-1].split("&")[0]
        else:
            video_id = url.split("/")[-1]

        try:
            # First try Invidious
            data = fetch_video_info(video_id)
            info = {
                "title": data.get("title"),
                "author": data.get("author"),
                "thumbnail": data.get("videoThumbnails")[0]["url"] if data.get("videoThumbnails") else None,
                "formats": data.get("adaptiveFormats") or data.get("videoFormats") or [],
            }
            return jsonify(info)
        except Exception:
            print("All Invidious instances failed. Falling back to yt-dlp.")
            info = get_media_info(url)  # yt-dlp fallback
            return jsonify(info)

    except Exception as e:
        print("Error (validate):", e)
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch video info'}), 500

# ---------- DOWNLOAD VIDEO ----------
@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    format_id = request.args.get('format')
    if not url or not format_id:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        file_path = download_media(url, format_id)  # from downloader.py

        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        @after_this_request
        def cleanup(response):
            try:
                os.remove(file_path)
                print(f"Deleted temporary file: {file_path}")
            except Exception as e:
                print("Cleanup error:", e)
                traceback.print_exc()
            return response

        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path),
            mimetype='application/octet-stream'
        )
    except Exception as e:
        print("Error (download video):", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ---------- DOWNLOAD AUDIO ----------
@app.route('/download_mp3', methods=['GET'])
def download_mp3():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    try:
        file_path = download_audio(url)  # from downloader.py

        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        @after_this_request
        def cleanup(response):
            try:
                os.remove(file_path)
                print(f"Deleted temporary file: {file_path}")
            except Exception as e:
                print("Cleanup error:", e)
                traceback.print_exc()
            return response

        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path),
            mimetype='audio/mpeg'
        )
    except Exception as e:
        print("Error (download audio):", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
