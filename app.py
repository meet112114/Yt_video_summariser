import os
import subprocess
import uuid
from flask import Flask, request, jsonify
import whisper
from transformers import pipeline

app = Flask(__name__)

# Load Whisper model
whisper_model = whisper.load_model("small")  # Options: "base", "small", "medium", "large"

# Load Summarization model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

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
            "-f", "bestaudio",
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
    """Transcribes audio using Whisper."""
    result = whisper_model.transcribe(audio_path)
    return result.get("text", "")

def chunk_text(text, max_words=500):
    """Splits text into chunks of max_words words."""
    words = text.split()
    return [' '.join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

def summarize_text(text):
    if not text.strip():
        return "Transcription returned empty text. Unable to summarize."

    words = text.split()
    max_words = 500  # Define maximum words per chunk

    # If the text is short enough, summarize directly.
    if len(words) <= max_words:
        try:
            results = summarizer(text, max_length=150, min_length=50, do_sample=False, truncation=True)
            if not results or not isinstance(results, list) or len(results) == 0:
                raise ValueError("Summarization failed: no results produced.")
            summary_text = results[0].get("summary_text", None)
            if not summary_text:
                raise ValueError("Summarization output does not contain 'summary_text'.")
            return summary_text
        except Exception as e:
            raise ValueError("Summarization failed: " + str(e))
    else:

        chunks = chunk_text(text, max_words)
        chunk_summaries = []
        for chunk in chunks:
            try:
                result = summarizer(chunk, max_length=150, min_length=50, do_sample=False, truncation=True)
                if result and isinstance(result, list) and len(result) > 0:
                    summary_text = result[0].get("summary_text", "")
                    chunk_summaries.append(summary_text)
                else:
                    chunk_summaries.append(chunk)
            except Exception as e:
                chunk_summaries.append(chunk)


        combined_summary = " ".join(chunk_summaries)


        try:
            final_result = summarizer(combined_summary, max_length=350, min_length=150, do_sample=False, truncation=True)
            if final_result and isinstance(final_result, list) and len(final_result) > 0:
                final_summary = final_result[0].get("summary_text", combined_summary)
                return final_summary
            else:
                return combined_summary
        except Exception as e:
            return combined_summary

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
