# -*- coding: utf-8 -*-
import streamlit as st
import subprocess
import uuid
from openai import OpenAI
import os
import math
from dotenv import load_dotenv
import requests
from datetime import datetime
from transformers import GPT2TokenizerFast
from pathlib import Path
import hashlib

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize tokenizer
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")


# Hash function for caching
def url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()


# Logging function
def log_usage(video_url, summary_type, status="success"):
    try:
        requests.post(
            "https://webhook.site/42e8bf51-3e8b-4549-b251-21ceb38d2c7a",
            json={
                "timestamp": datetime.utcnow().isoformat(),
                "video_url": video_url,
                "summary_type": summary_type,
                "status": status,
            },
        )
    except Exception as e:
        print(f"Usage logging failed: {e}")


# Chunking function
def chunk_transcript(text, max_tokens=3000):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        token_count = len(tokenizer.encode(" ".join(current_chunk)))

        if token_count >= max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# Title and instructions

st.markdown(
    """
<div style='line-height: 1.15; margin-bottom: 1.2em;'>
  <div style='font-size: 1.9em; font-weight: 700; color: #FFD60A; margin-bottom: 0.6em;'>ClipNotes</div>
  <div style='font-size: 2.9em; font-weight: 800; margin-top: 0;'>
    Get AI to 'Watch' <span style='color: #FF0000;'>YouTube</span> for You
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    "YouTube is the richest resource of long-form explainers, interviews and prognostications from thought leaders, experts and critics. And if you’re like me, you feel the need to stay on top of what's being said.",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <h3 style='margin-bottom: 0.2em; font-weight: 700;'>The problem</h3>
    <p style='margin-top: 0;'>There aren’t enough hours in the day to watch these videos. It's a missed opportunity to gain key insights.</p>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <h3 style='margin-bottom: 0.2em; font-weight: 700;'>A solution</h3>
    <p style='margin-top: 0;'>ClipNotes summarizes the main points of a video in as little as one-tenth the time it would take to watch it. This AI tool is ideal for lectures, interviews, talks or any video centered around someone speaking.</p>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <h3 style='margin-bottom: 0.2em; font-weight: 700;'>How to use</h3>
    <p style='margin-top: 0;'>Paste a YouTube URL below, pick a summary style, select a processing speed (or leave it on the default) and hit generate. Run time will largely depend on how long the video is (I’ve had a 20-minute video take 2 minutes to process, while a 2-hour video took 20 minutes; your mileage may vary). Also:</p>

    <ul style='margin-top: 0.5em;'>
        <li>✅&nbsp;&nbsp;Use standard YouTube videos <em>(Shorts may not work)</em></li>
        <li>❌&nbsp;&nbsp;Don't input music videos or similar that may have DRM locks</li>
        <li>🔍&nbsp;&nbsp;For additional context or timestamps, search the transcript at the bottom</li>
        <li>🎭&nbsp;&nbsp;Tool doesn’t differentiate between voices, which can affect results</li>
        <li>🛠️&nbsp;&nbsp;Currently supports English audio only</li>
    </ul>
    <div style='margin-bottom: 1.9em;'></div>
    """,
    unsafe_allow_html=True,
)
# Create form for inputs
with st.form(key="input_form"):
    url = st.text_input("Enter YouTube URL:")
    summary_labels = {
        "basic": "Basic — quick summary in 5–7 sentences",
        "bullets": "Bullets — list of 5–10 key points",
        "quotes": "Quotes — 5–10 compelling lines",
        "insights": "Insights — strategic takeaways with explanations",
        "newbie": "Newbie — explain main points like I'm new to the topic",
    }
    label_to_key = {v: k for k, v in summary_labels.items()}
    selected_label = st.selectbox(
        "Choose summary style:", list(summary_labels.values())
    )
    selected_type = label_to_key[selected_label]

    summary_scope = st.radio(
        "Choose a processing speed (for short videos — less than 15 minutes):",
        [
            "⚡ Quick (fast, but light context)",
            "🐢 Less Quick (slower, but deeper context)",
        ],
        index=1,
        horizontal=True,
    )

    submit_button = st.form_submit_button(label="Generate Summary")

if submit_button and url:
    st.session_state["show_summary"] = False
    uid = url_hash(url)

    if (
        st.session_state.get("transcript_url") == uid
        and "transcript_text" in st.session_state
        and "transcript_segments" in st.session_state
    ):
        st.info("Transcript already cached — skipping download and transcription.")
        transcript_text = st.session_state["transcript_text"]
        segments = st.session_state["transcript_segments"]
    else:
        st.success(f"Received URL: {url}")
        st.write("Downloading audio...")

        audio_filename = f"downloaded_{uuid.uuid4().hex}.mp3"
        command = [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "0",
            "--output",
            audio_filename,
            url,
        ]

        try:
            subprocess.run(command, check=True)
            st.success("Audio downloaded successfully.")

            st.write("Compressing audio for transcription...")
            compressed_filename = f"compressed_{uuid.uuid4().hex}.mp3"
            ffmpeg_command = [
                "ffmpeg",
                "-i",
                audio_filename,
                "-ar",
                "16000",
                "-ac",
                "1",
                compressed_filename,
            ]
            subprocess.run(ffmpeg_command, check=True)
            st.success("Audio compressed successfully.")
        except Exception as e:
            st.error(f"Error downloading or compressing audio: {e}")
            st.stop()

        # Transcription
        st.write("Transcribing...")
        try:
            with open(compressed_filename, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=f, response_format="verbose_json"
                )
            transcript_text = " ".join([seg.text for seg in transcript.segments])
            segments = transcript.segments

            # Cache it
            st.session_state["transcript_text"] = transcript_text
            st.session_state["transcript_segments"] = segments
            st.session_state["transcript_url"] = uid

            st.success("Transcription complete.")
            log_usage(url, selected_type, status="success")
        except Exception as e:
            st.error(f"Error during transcription: {e}")
            st.stop()

    estimated_tokens = len(tokenizer.encode(transcript_text))
    st.info(f"Transcript token count (est.): {estimated_tokens} tokens")

    summary_prompt_templates = {
        "basic": "Summarize the following transcript in 5–7 clear sentences.\n\n{transcript}",
        "bullets": "Summarize the transcript in 5–10 key bullet points.\n\n{transcript}",
        "quotes": "Extract 5–10 powerful quotes that capture the speaker's ideas. Do not include timestamps.\n\n{transcript}",
        "insights": "List 5–7 strategic takeaways with explanations.\n\n{transcript}",
        "newbie": "Explain 5–7 key ideas in simple terms.\n\n{transcript}",
    }

    chunked = False
    chunk_summaries = []
    max_tokens = 8192

    if estimated_tokens + 900 > max_tokens or summary_scope.startswith("🐢"):
        st.warning("Transcript is long — using chunking.")
        chunks = chunk_transcript(transcript_text)
        for i, chunk in enumerate(chunks):
            st.write(f"Summarizing chunk {i+1} of {len(chunks)}...")
            prompt = summary_prompt_templates[selected_type].replace(
                "{transcript}", chunk
            )
            res = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=900,
            )
            chunk_summaries.append(res.choices[0].message.content.strip())
        st.session_state["chunk_summaries"] = chunk_summaries
        chunked = True

    if chunked:
        st.write("Condensing final summary...")
        condensed_prompt = {
            "basic": "Summarize the following multi-part summary into a cohesive paragraph:\n\n{combined}",
            "bullets": "Summarize the following multi-part summaries into a single cohesive bullet-point list (maximum 10 bullets):\n\n{combined}",
            "quotes": "From the following quotes, select the 5–10 most compelling. Do not add timestamps.\n\n{combined}",
            "insights": "Merge the following into 5–7 strategic insights:\n\n{combined}",
            "newbie": "Combine into a simple explanation for someone new to the topic:\n\n{combined}",
        }
        full_summary_prompt = condensed_prompt[selected_type].replace(
            "{combined}", "\n\n".join(chunk_summaries)
        )
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": full_summary_prompt}],
            temperature=0.7,
            max_tokens=900,
        )
        final_summary = res.choices[0].message.content.strip()
        st.session_state["summary"] = final_summary
        st.session_state["show_summary"] = True
    else:
        prompt = summary_prompt_templates[selected_type].replace(
            "{transcript}", transcript_text
        )
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=900,
        )
        st.session_state["summary"] = res.choices[0].message.content.strip()
        st.session_state["show_summary"] = True

if st.session_state.get("show_summary"):
    st.subheader("🧠 Overall Summary")
    st.markdown(st.session_state["summary"], unsafe_allow_html=True)

    if "chunk_summaries" in st.session_state:
        st.subheader("🧩 Chunk Summaries")
        for i, chunk in enumerate(st.session_state["chunk_summaries"]):
            with st.expander(f"View Part {i+1} Summary"):
                st.markdown(chunk, unsafe_allow_html=True)

    if st.button("Show Full Transcript"):
        st.subheader("Full Transcript")
        segments = st.session_state["transcript_segments"]
        transcript_lines = ""
        current_text = ""
        current_start = None

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
            unsafe_allow_html=True,
        )
st.markdown(
    """
    <hr style="margin-top: 3em; margin-bottom: 1em; border: none; border-top: 1px solid #444;" />
    <div style="text-align: center; font-size: 0.9em; color: gray;">
        Made with 🤖 by 
        <a href="https://www.linkedin.com/in/marcuslowchan" target="_blank" style="color: #f1c40f; text-decoration: none; font-weight: bold;">
            Marcus Chan
        </a> — exploring the future of GenAI + content strategy.
        
    </div>
    """,
    unsafe_allow_html=True,
)
