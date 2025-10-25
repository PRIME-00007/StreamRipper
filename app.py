from flask import Flask, render_template, request, jsonify
import requests
import os
import traceback

app = Flask(__name__)

# You can pick a public Invidious instance. Example:
INVIDIOUS_INSTANCE = "https://invidious.snopyta.org"  # free public instance
# see https://github.com/iv-org/invidious/wiki/Invidious-Instances for more

# ---------- INDEX ----------
@app.route('/')
def index():
    return render_template('index.html')

# ---------- VALIDATE ----------
@app.route('/validate', methods=['POST'])
def validate():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # Extract video ID from URL
        if "watch?v=" in url:
            video_id = url.split("watch?v=")[-1].split("&")[0]
        else:
            video_id = url.split("/")[-1]

        api_url = f"{INVIDIOUS_INSTANCE}/api/v1/videos/{video_id}"
        resp = requests.get(api_url, timeout=10)

        if resp.status_code != 200:
            return jsonify({'error': f"Failed to fetch video info ({resp.status_code})"}), 500

        data = resp.json()

        # Return essential info + formats
        info = {
            "title": data.get("title"),
            "author": data.get("author"),
            "thumbnail": data.get("videoThumbnails")[0]["url"] if data.get("videoThumbnails") else None,
            "formats": data.get("adaptiveFormats") or data.get("videoFormats") or [],
        }

        return jsonify(info)
    except Exception as e:
        print("Invidious Error (validate):", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ---------- GET DOWNLOAD LINK ----------
@app.route('/download_link', methods=['GET'])
def download_link():
    url = request.args.get('url')
    format_id = request.args.get('format')
    if not url or not format_id:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        # Extract video ID from URL
        if "watch?v=" in url:
            video_id = url.split("watch?v=")[-1].split("&")[0]
        else:
            video_id = url.split("/")[-1]

        api_url = f"{INVIDIOUS_INSTANCE}/api/v1/videos/{video_id}"
        resp = requests.get(api_url, timeout=10)
        if resp.status_code != 200:
            return jsonify({'error': f"Failed to fetch video info ({resp.status_code})"}), 500

        data = resp.json()
        formats = data.get("adaptiveFormats") or data.get("videoFormats") or []

        # Find the selected format
        selected = None
        for f in formats:
            if str(f.get("itag")) == str(format_id):
                selected = f
                break

        if not selected:
            return jsonify({'error': 'Format not found'}), 404

        return jsonify({
            "url": selected.get("url"),
            "mimeType": selected.get("mimeType"),
            "quality": selected.get("qualityLabel") or selected.get("quality"),
        })

    except Exception as e:
        print("Invidious Error (download link):", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
