import streamlit as st
import subprocess
import uuid
from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

# Load environment variables
load_dotenv(dotenv_path="../env_file/.env")
client = OpenAI()

# Function to log usage
def log_usage(video_url, summary_type, status="success"):
    try:
        requests.post("https://webhook.site/42e8bf51-3e8b-4549-b251-21ceb38d2c7a", json={
            "timestamp": datetime.utcnow().isoformat(),
            "video_url": video_url,
            "summary_type": summary_type,
            "status": status
        })
    except Exception as e:
        print(f"Usage logging failed: {e}")

# Initialize session state variables
if 'transcript_text' not in st.session_state:
    st.session_state['transcript_text'] = ""
if 'summary' not in st.session_state:
    st.session_state['summary'] = ""
if 'summary_type' not in st.session_state:
    st.session_state['summary_type'] = "basic"
if 'transcript_segments' not in st.session_state:
    st.session_state['transcript_segments'] = []

st.title("YouTube Summarizer for Busy Folk")
st.write("Paste a YouTube URL below and choose a summary style.")

# Create a form for user inputs
with st.form(key='input_form'):
    url = st.text_input("Enter YouTube URL:")
    summary_options = ["basic", "bullets", "quotes", "insights", "controversial"]
    selected_type = st.selectbox("Choose summary style:", summary_options)
    submit_button = st.form_submit_button(label='Generate Summary')

# Process inputs after form submission
if submit_button and url:
    st.session_state['summary_type'] = selected_type
    st.session_state['summary'] = ""
    st.session_state['transcript_text'] = ""
    st.session_state['transcript_segments'] = []

    st.success(f"Received URL: {url}")
    st.write("Downloading audio...")

    audio_filename = f"downloaded_{uuid.uuid4().hex}.mp3"
    command = [
        'yt-dlp',
        '-f', 'bestaudio',
        '--extract-audio',
        '--audio-format', 'mp3',
        '--output', audio_filename,
        url
    ]

    try:
        subprocess.run(command, check=True)
        st.success("Audio downloaded successfully.")
    except Exception as e:
        st.error(f"Error downloading audio: {e}")
        st.stop()

    # Transcribe audio
    st.write("Transcribing...")
    try:
        with open(audio_filename, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json"
            )
        st.session_state['transcript_segments'] = transcript.segments
        st.session_state['transcript_text'] = " ".join([seg.text for seg in transcript.segments])
        st.success("Transcription complete.")
        log_usage(url, "transcription", status="success")
    except Exception as e:
        st.error(f"Error during transcription: {e}")
        st.stop()

# Display transcript
if st.session_state['transcript_text']:
    st.subheader("Transcript Preview")
    st.markdown(st.session_state['transcript_text'][:1000] + "...")

# Generate summary
if st.session_state['transcript_text'] and st.session_state['summary_type']:
    try:
        transcript_text = st.session_state['transcript_text']
        segments = st.session_state['transcript_segments']
        summary_type = st.session_state['summary_type']

        summary_prompt = {
            "basic": (
                f"Summarize the following transcript:\n\n{transcript_text}"
            ),
            "bullets": (
                "Distill the transcript below into the 5–7 most important, non-redundant insights. "
                "Avoid restating general ideas — instead, capture only the most essential takeaways "
                "that would be valuable for someone skimming for key points.\n\n"
                f"{transcript_text}"
            ),
            "quotes": (
                "Extract 5–10 of the most compelling or insightful quotes from this transcript. "
                "Include timestamps with each quote:\n\n" +
                "\n".join([f"[{int(seg.start)//60}:{int(seg.start)%60:02d}] {seg.text}" for seg in segments])
            ),
            "insights": (
                "Extract and explain 5–7 key lessons or strategic insights from the transcript below.\n\n"
                "Format each insight exactly like this:\n\n"
                "**Insight Title Goes Here**\n\n"
                "Insight explanation in 2–3 sentences.\n\n"
                "Use a double newline between the title and explanation, and between insights. Do not bold the explanation — only the title.\n\n"
                f"{transcript_text}"
            ),
            "controversial": (
                "Identify 3–5 controversial, provocative, or contrarian statements made or implied in this transcript.\n\n"
                "These may include ideas that challenge social norms, question common beliefs, or spark strong disagreement. "
                "Summarize each take in 1–2 sentences. If possible, explain why it might be viewed as controversial:\n\n"
                f"{transcript_text}"
            )
        }

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": summary_prompt[summary_type]}],
            temperature=0.7,
            max_tokens=700
        )

        st.subheader("Summary")
        st.session_state['summary'] = response.choices[0].message.content.strip()
        st.write(st.session_state['summary'])
        log_usage(url, summary_type, status="success")

    except Exception as e:
        st.error(f"Error generating summary: {e}")
        log_usage(url, summary_type, status="error")