import streamlit as st
import subprocess
import uuid
from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Logging function
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

# Title and instructions
st.title("ClipNotes: AI Summarizer for YouTube Videos")
st.write("When the video is too long or complex, use this tool to get the gist — fast.")
st.write("Paste a YouTube URL below, hit return, then choose a summary style and hit generate.")

# Create form for inputs
with st.form(key='input_form'):
    url = st.text_input("Enter YouTube URL:")
    summary_labels = {
        "basic": "Basic — quick summary in 5–7 sentences",
        "bullets": "Bullets — list of 5–10 key points",
        "quotes": "Quotes — 5–10 compelling lines with timestamps",
        "insights": "Insights — strategic takeaways with explanations",
        "newbie": "Newbie — explain main points like I'm new to the topic"
    }
    label_to_key = {v: k for k, v in summary_labels.items()}
    selected_label = st.selectbox("Choose summary style:", list(summary_labels.values()))
    selected_type = label_to_key[selected_label]
    submit_button = st.form_submit_button(label='Generate Summary')

# Process form submission
if submit_button and url:
    st.session_state['show_summary'] = False

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

    # Transcribe
    st.write("Transcribing...")
    try:
        with open(audio_filename, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json"
            )
        transcript_text = " ".join([seg.text for seg in transcript.segments])
        st.session_state['transcript_text'] = transcript_text
        st.session_state['transcript_segments'] = transcript.segments
        st.success("Transcription complete.")
        log_usage(url, selected_type, status="success")
    except Exception as e:
        st.error(f"Error during transcription: {e}")
        st.stop()

    # Prepare summary prompt
    transcript_text = st.session_state['transcript_text']
    segments = st.session_state['transcript_segments']

    if selected_type == "quotes":
        quotes_block = "\n".join([
            f"<span style='color:#00bcd4'><strong>[{int(seg.start)//60}:{int(seg.start)%60:02d}]</strong></span> {seg.text.strip()}"
            for seg in segments if seg.text.strip().endswith((".", "?", "!"))
        ])
    else:
        quotes_block = ""

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
            "Extract 5–10 of the most compelling and insightful quotes from this transcript.\n\n"
            "Each quote should:\n"
            "- Be a complete and self-contained idea.\n"
            "- Include enough context so it makes sense on its own.\n"
            "- Often require 1–2 sentences if needed for clarity.\n"
            "- Begin with a timestamp in this format: [minutes:seconds]\n\n"
            "Use this formatting for each quote:\n"
            "<span style='color:#00bcd4'><strong>[timestamp]</strong></span> \"Quote here.\"\n\n"
            "Examples:\n"
            "<span style='color:#00bcd4'><strong>[0:42]</strong></span> \"Create a state in the mind where it can absorb new perspectives and unlearn old trauma patterns.\"\n"
            "<span style='color:#00bcd4'><strong>[1:15]</strong></span> \"People don't just want to be heard — they want to feel safe while being heard.\"\n\n"
            "Now extract the quotes from the transcript:\n\n"
            + "\n".join([f"[{int(seg.start)//60}:{int(seg.start)%60:02d}] {seg.text}" for seg in segments])
),
        "insights": (
            "Extract and explain 5–7 key lessons or strategic insights from the transcript below.\n\n"
            "Format each insight exactly like this:\n\n"
            "**Insight Title Goes Here**\n\n"
            "Insight explanation in 2–3 sentences.\n\n"
            "Use a double newline between the title and explanation, and between insights. "
            "Do not bold the explanation — only the title.\n\n"
            f"{transcript_text}"
        ),
        "newbie": (
            "Explain 5–7 main ideas in this transcript as if you're talking to someone completely new to the topic. "
            "Use simple, clear language and helpful examples. Avoid jargon. Assume no prior knowledge but genuine curiosity.\n\n"
            f"{transcript_text}"
        )
    }

    try:
        temperature_by_style = {
            "basic": 0.6,
            "bullets": 0.6,
            "quotes": 0.7,
            "insights": 0.8,
            "newbie": 0.8,
        }
        temperature = temperature_by_style.get(selected_type, 0.7)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": summary_prompt[selected_type]}],
            temperature=temperature,
            max_tokens=900
        )
        st.session_state['summary'] = response.choices[0].message.content.strip()
        st.session_state['show_summary'] = True
    except Exception as e:
        st.error(f"Error generating summary: {e}")

# Show summary and full transcript toggle
if st.session_state.get('show_summary'):
    st.subheader("Summary")
    st.markdown(st.session_state['summary'], unsafe_allow_html=True)

    if st.button("Show Full Transcript"):
        st.subheader("Full Transcript")
        transcript_lines = ""
        current_text = ""
        current_start = None
        segments = st.session_state['transcript_segments']

        for i, seg in enumerate(segments):
            if current_start is None:
                current_start = int(seg.start)

            current_text += seg.text.strip() + " "

            if seg.text.strip().endswith((".", "?", "!")) or i == len(segments) - 1:
                minutes = current_start // 60
                seconds = current_start % 60
                timestamp = f"[{minutes}:{seconds:02d}]"
                transcript_lines += f"<p><span style='color:#00bcd4'><strong>{timestamp}</strong></span> {current_text.strip()}</p>"
                current_text = ""
                current_start = None

        st.markdown(
            f"""
            <div style='height: 450px; overflow-y: scroll; border: 1px solid gray; padding: 10px;
                background-color: rgba(0, 0, 0, 0.7); color: white; border-radius: 5px;'>
                {transcript_lines}
            </div>
            """,
            unsafe_allow_html=True
        )