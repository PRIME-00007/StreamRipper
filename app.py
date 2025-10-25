from flask import Flask, render_template, request, send_file, jsonify, after_this_request
from downloader import download_media, get_media_info, download_audio
import os
import traceback

app = Flask(__name__)

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
        info = get_media_info(url)
        return jsonify(info)
    except Exception as e:
        print("YT-DLP Error (validate):", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ---------- DOWNLOAD VIDEO ----------
@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    format_id = request.args.get('format')

    if not url or not format_id:
        return "Missing parameters", 400

    try:
        file_path = download_media(url, format_id)

        if not os.path.exists(file_path):
            return "File not found", 404

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
        print("YT-DLP Error (download video):", e)
        traceback.print_exc()
        return str(e), 500

# ---------- DOWNLOAD AUDIO ----------
@app.route('/download_mp3', methods=['GET'])
def download_mp3():
    url = request.args.get('url')
    if not url:
        return "Missing URL", 400

    try:
        file_path = download_audio(url)

        if not os.path.exists(file_path):
            return "File not found", 404

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
        print("YT-DLP Error (download audio):", e)
        traceback.print_exc()
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT via env variable
    app.run(host="0.0.0.0", port=port, debug=True)
