
import os
import subprocess
import uuid
import openai
import whisper
from flask import Flask, request, jsonify

app = Flask(__name__)

OPENAI_API_KEY = "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"

# Load Whisper model locally
whisper_model = whisper.load_model("base")  # Options: "base", "small", "medium", "large"

# Directory for temporary audio storage
AUDIO_DIR = "audio_files"
os.makedirs(AUDIO_DIR, exist_ok=True)

def download_audio(video_url):
    """Downloads YouTube video as audio using yt-dlp with a unique filename."""
    unique_id = uuid.uuid4().hex
    audio_path = os.path.join(AUDIO_DIR, f"audio_{unique_id}.mp3")
    try:
        command = [
            "yt-dlp",
            "--force-overwrites",
            "--extract-audio",
            "--audio-format", "mp3",
            "-o", audio_path,
            video_url
        ]
        subprocess.run(command, check=True)
        return audio_path
    except Exception as e:
        return str(e)

def transcribe_audio(audio_path):
    """Transcribes audio using local Whisper model."""
    result = whisper_model.transcribe(audio_path)
    return result.get("text", "")

def summarize_text(text):
    """Summarizes text using OpenAI's GPT model."""
    if not text.strip():
        return "Transcription returned empty text. Unable to summarize."

    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)  # Pass API key

        response = client.chat.completions.create(
            model= "gpt-4o-mini",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                {"role": "user", "content": f"Summarize the following text:\n{text}"}
            ],
            temperature=0.5,
            max_tokens=300
        )
        summary = response.choices[0].message.content
        return summary.strip()
    except Exception as e:
        return f"Summarization failed: {str(e)}"

@app.route("/summary", methods=["GET"])
def summary_api():
    video_url = request.args.get("url")
    if not video_url:
        return jsonify({"error": "No YouTube URL provided"}), 400

    try:
        audio_path = download_audio(video_url)
        if "error" in audio_path:
            return jsonify({"error": audio_path}), 500

        transcript = transcribe_audio(audio_path)

        summary = summarize_text(transcript)

        if os.path.exists(audio_path):
            os.remove(audio_path)

        return jsonify({"summary": summary}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
