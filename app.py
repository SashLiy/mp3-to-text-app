import os
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory
import whisper

# Initialize the Flask app
app = Flask(__name__)

# Load the Whisper model
model = whisper.load_model("base")

# Ensure 'uploads' folder exists
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Allowed file types for upload
ALLOWED_EXTENSIONS = {'mp3'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for handling file uploads
@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            file_path = os.path.join("uploads", file.filename)
            file.save(file_path)

            if os.path.exists(file_path):
                result = model.transcribe(file_path)
                transcription_text = result['text']

                # Create a text file with the transcription
                txt_filename = file.filename.rsplit('.', 1)[0] + ".txt"
                txt_file_path = os.path.join("uploads", txt_filename)
                with open(txt_file_path, 'w') as txt_file:
                    txt_file.write(transcription_text)

                return jsonify({
                    "text": transcription_text,
                    "download_url": f"/download/{txt_filename}"
                }), 200
            else:
                return jsonify({"error": "File not found after saving"}), 400
        else:
            return jsonify({"error": "Invalid file format. Only MP3 allowed."}), 400
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# Route for handling URL input
@app.route("/transcribe-url", methods=["POST"])
def transcribe_url():
    try:
        url = request.json.get("url")
        if not url:
            return jsonify({"error": "No URL provided"}), 400

        file_name = os.path.join("uploads", "downloaded_audio.mp3")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(file_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        if os.path.exists(file_name):
            result = model.transcribe(file_name)
            transcription_text = result['text']

            # Create a text file with the transcription
            txt_filename = "downloaded_audio.txt"
            txt_file_path = os.path.join("uploads", txt_filename)
            with open(txt_file_path, 'w') as txt_file:
                txt_file.write(transcription_text)

            return jsonify({
                "text": transcription_text,
                "download_url": f"/download/{txt_filename}"
            }), 200
        else:
            return jsonify({"error": "Failed to download the audio file."}), 400

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# Route to serve the transcription .txt file for download
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory("uploads", filename)

if __name__ == "__main__":
    app.run(debug=True)
