from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import whisper
import subprocess
import os
import glob
import threading
from groq import Groq

app = Flask(__name__)

GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

status = {"message": "Ready!", "done": False, "clips": []}

def process_video(url):
    global status
    try:
        status["message"] = "🗑️ Cleaning old clips..."
        status["clips"] = []
        for f in glob.glob("/home/babu/clipai/clip*.mp4"):
            os.remove(f)
        if os.path.exists("/home/babu/clipai/video.mp4"):
            os.remove("/home/babu/clipai/video.mp4")

        status["message"] = "⬇️ Downloading video..."
        ydl_opts = {'format': 'best', 'outtmpl': '/home/babu/clipai/video.mp4'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        status["message"] = "🎙️ Transcribing video..."
        model = whisper.load_model("base")
        result = model.transcribe("/home/babu/clipai/video.mp4")
        text = result["text"]

        status["message"] = "🧠 Finding best moments..."
        prompt = f"""
        You are a viral video expert.
        Find the 3 most powerful moments for short clips under 60 seconds each.
        For each moment give ONLY this format:
        CLIP 1: start=10 end=60 reason=Powerful message
        CLIP 2: start=80 end=140 reason=Emotional moment
        CLIP 3: start=160 end=220 reason=Strong ending
        Transcript:
        {text}
        """
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        groq_output = response.choices[0].message.content

        status["message"] = "✂️ Cutting clips..."
        lines = groq_output.strip().split("\n")
        clip_num = 1
        clips = []
        for line in lines:
            if line.startswith("CLIP"):
                parts = line.split()
                start = end = None
                for part in parts:
                    if part.startswith("start="):
                        start = part.split("=")[1]
                    if part.startswith("end="):
                        end = part.split("=")[1]
                if start and end:
                    output_file = f"/home/babu/clipai/clip{clip_num}.mp4"
                    cmd = f"ffmpeg -i /home/babu/clipai/video.mp4 -ss {start} -to {end} -c copy {output_file} -y"
                    subprocess.run(cmd, shell=True)
                    clips.append(f"clip{clip_num}.mp4")
                    clip_num += 1

        status["message"] = "🎉 All clips ready!"
        status["done"] = True
        status["clips"] = clips

    except Exception as e:
        status["message"] = f"❌ Error: {str(e)}"
        status["done"] = True

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    global status
    url = request.json.get("url")
    status = {"message": "Starting...", "done": False, "clips": []}
    thread = threading.Thread(target=process_video, args=(url,))
    thread.start()
    return jsonify({"message": "Started!"})

@app.route("/status")
def get_status():
    return jsonify(status)

@app.route("/download/<filename>")
def download(filename):
    return send_file(f"/home/babu/clipai/{filename}", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)