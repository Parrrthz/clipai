import os
import yt_dlp
import whisper
import subprocess
from groq import Groq

# Your Groq API Key
GROQ_API_KEY = "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"

# Setup Groq
client = Groq(api_key=GROQ_API_KEY)

# Download YouTube Video
def download_video(url):
    print("⬇️ Downloading video...")
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print("✅ Video downloaded!")

# Transcribe Video to Text
def transcribe_video():
    print("🎙️ Transcribing video...")
    model = whisper.load_model("base")
    result = model.transcribe("video.mp4")
    print("✅ Transcription done!")
    return result

# Find Best Moments using Groq AI
def find_best_moments(transcript):
    print("🧠 Finding best moments...")
    text = transcript["text"]
    prompt = f"""
    You are a viral video expert.
    Below is a transcript of a motivational video.
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
    print("✅ Best moments found!")
    return response.choices[0].message.content

# Cut Video into Clips
def cut_clips(groq_output):
    print("✂️ Cutting clips...")
    lines = groq_output.strip().split("\n")
    clip_num = 1
    for line in lines:
        if line.startswith("CLIP"):
            parts = line.split()
            start = None
            end = None
            for part in parts:
                if part.startswith("start="):
                    start = part.split("=")[1]
                if part.startswith("end="):
                    end = part.split("=")[1]
            if start and end:
                output_file = f"clip{clip_num}.mp4"
                cmd = f"ffmpeg -i video.mp4 -ss {start} -to {end} -c copy {output_file} -y"
                subprocess.run(cmd, shell=True)
                print(f"✅ clip{clip_num}.mp4 saved!")
                clip_num += 1

# Run
video_url = "https://youtu.be/HTvJl71zmf4?si=Lw3G8AyqOqfKdM75"
download_video(video_url)
transcript = transcribe_video()
groq_output = find_best_moments(transcript)
print(groq_output)
cut_clips(groq_output)
print("🎉 All clips ready!")