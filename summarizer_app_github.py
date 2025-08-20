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
import tempfile
import shutil

# Try to load API key from Streamlit secrets
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    # Fallback for local development
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Initialize tokenizer
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")


# Hash function for caching
def url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()


# More aggressive audio download function
def download_audio_aggressive(url, output_filename):
    """
    Download audio with the most effective anti-blocking strategies
    """
    commands_to_try = [
        # Strategy 1: Use cookies file simulation and newest user agent
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--user-agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "--add-header",
            "Accept-Language:en-US,en;q=0.9",
            "--add-header",
            "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "--sleep-interval",
            "1",
            "--max-sleep-interval",
            "3",
            "--output",
            output_filename,
            url,
        ],
        # Strategy 2: Simulate mobile browser
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--user-agent",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "--add-header",
            "Accept-Language:en-US,en;q=0.9",
            "--sleep-interval",
            "2",
            "--output",
            output_filename,
            url,
        ],
        # Strategy 3: Use very basic approach with delay
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--sleep-interval",
            "3",
            "--max-sleep-interval",
            "5",
            "--retries",
            "3",
            "--output",
            output_filename,
            url,
        ],
        # Strategy 4: Try with format selection
        [
            "yt-dlp",
            "-f",
            "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio",
            "-x",
            "--audio-format",
            "mp3",
            "--output",
            output_filename,
            url,
        ],
        # Strategy 5: Force IPv4 with delays
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--force-ipv4",
            "--sleep-interval",
            "2",
            "--socket-timeout",
            "30",
            "--output",
            output_filename,
            url,
        ],
    ]

    for i, command in enumerate(commands_to_try):
        try:
            st.write(f"🔄 Trying download strategy {i+1}/{len(commands_to_try)}...")

            # Run with timeout and capture output
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=240,  # 4 minute timeout per attempt
            )

            if result.returncode == 0:
                st.success(f"✅ Audio downloaded successfully using strategy {i+1}")
                return True
            else:
                st.warning(f"❌ Strategy {i+1} failed (code {result.returncode})")
                if result.stderr:
                    error_preview = (
                        result.stderr[:150] + "..."
                        if len(result.stderr) > 150
                        else result.stderr
                    )
                    st.text(f"Error: {error_preview}")

        except subprocess.TimeoutExpired:
            st.warning(f"⏱️ Strategy {i+1} timed out after 4 minutes")
        except Exception as e:
            st.warning(f"❌ Strategy {i+1} exception: {str(e)}")

    return False


# Improved compression function
def compress_audio(input_file, output_file):
    """
    Compress audio file for transcription with error handling
    """
    ffmpeg_commands = [
        # Primary command with aggressive compression
        [
            "ffmpeg",
            "-y",
            "-i",
            input_file,
            "-ar",
            "16000",
            "-ac",
            "1",
            "-ab",
            "32k",  # Low bitrate
            "-f",
            "mp3",
            output_file,
        ],
        # Fallback command
        ["ffmpeg", "-y", "-i", input_file, "-ar", "16000", "-ac", "1", output_file],
    ]

    for i, command in enumerate(ffmpeg_commands):
        try:
            st.write(f"🔄 Compressing audio (method {i+1})...")
            result = subprocess.run(
                command, check=False, capture_output=True, text=True, timeout=90
            )

            if result.returncode == 0:
                st.success(f"✅ Audio compressed successfully")
                return True
            else:
                st.warning(f"Compression method {i+1} failed")

        except subprocess.TimeoutExpired:
            st.error("Audio compression timed out")
        except FileNotFoundError:
            st.error("❌ ffmpeg not found. This tool requires ffmpeg to be installed.")
            return False
        except Exception as e:
            st.warning(f"Compression method {i+1} failed: {str(e)}")

    return False


# Logging function
def log_usage(video_url, summary_type, status="success", method=""):
    try:
        requests.post(
            "https://webhook.site/42e8bf51-3e8b-4549-b251-21ceb38d2c7a",
            json={
                "timestamp": datetime.utcnow().isoformat(),
                "video_url": video_url,
                "summary_type": summary_type,
                "status": status,
                "method": method,
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
    "YouTube is the richest resource of long-form explainers, interviews and prognostications from thought leaders, experts and critics. And if you're like me, you feel the need to stay on top of what's being said.",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <h3 style='margin-bottom: 0.2em; font-weight: 700;'>The problem</h3>
    <p style='margin-top: 0;'>There aren't enough hours in the day to watch these videos. It's a missed opportunity to gain key insights.</p>
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
    <p style='margin-top: 0;'>Paste a YouTube URL below, pick a summary style and hit generate. The tool uses advanced techniques to bypass YouTube's download restrictions. Processing time depends on video length and current blocking intensity.</p>

    <ul style='margin-top: 0.5em;'>
        <li>✅&nbsp;&nbsp;Use standard YouTube videos (Shorts may not work reliably)</li>
        <li>❌&nbsp;&nbsp;Don't input music videos or content with heavy DRM restrictions</li>
        <li>🔍&nbsp;&nbsp;For additional context or timestamps, search the transcript at the bottom</li>
        <li>🎭&nbsp;&nbsp;Tool doesn't differentiate between voices, which can affect results</li>
        <li>🛠️&nbsp;&nbsp;Currently supports English audio only</li>
        <li>⚡&nbsp;&nbsp;Uses multiple download strategies to overcome restrictions</li>
        <li>🔄&nbsp;&nbsp;If one method fails, automatically tries alternatives</li>
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

    submit_button = st.form_submit_button(label="Generate Summary")

if submit_button and url:
    st.session_state["show_summary"] = False
    uid = url_hash(url)

    if (
        st.session_state.get("transcript_url") == uid
        and "transcript_text" in st.session_state
        and "transcript_segments" in st.session_state
    ):
        st.info("📋 Transcript already cached — skipping download and transcription.")
        transcript_text = st.session_state["transcript_text"]
        segments = st.session_state["transcript_segments"]
    else:
        st.success(f"📥 Processing URL: {url}")

        st.info(
            "🔄 **Starting download process...** This may take a few minutes due to YouTube's anti-bot measures. The tool will try multiple strategies automatically."
        )

        # Use more unique filename
        audio_filename = f"downloaded_{uid}.%(ext)s"

        # Try to download audio with aggressive strategies
        if not download_audio_aggressive(url, audio_filename):
            st.error("❌ **All download strategies failed.**")
            st.markdown(
                """
            **This could be due to:**
            - YouTube's enhanced anti-bot measures (most common)
            - Video is private, age-restricted, or region-blocked  
            - Video has specific download restrictions
            - Your hosting platform's IP range is blocked by YouTube
            - Temporary network issues
            
            **Suggestions:**
            - Try a different, more popular video (popular videos are often less restricted)
            - Wait 30-60 minutes and try again (temporary IP blocking)
            - Try a video that's educational content, interviews, or talks (less likely to be restricted)
            - Check if the video URL is correct and publicly accessible
            """
            )
            log_usage(url, selected_type, status="all_download_methods_failed")
            st.stop()

        # Find the actual downloaded file
        downloaded_files = [
            f for f in os.listdir(".") if f.startswith(f"downloaded_{uid}")
        ]
        if not downloaded_files:
            # Broader search
            downloaded_files = [
                f
                for f in os.listdir(".")
                if "downloaded_" in f and f.endswith((".mp3", ".m4a", ".webm", ".mp4"))
            ]

        if not downloaded_files:
            st.error("❌ Could not find downloaded audio file")
            st.stop()

        actual_audio_file = downloaded_files[0]
        st.success(f"✅ Audio file ready: {actual_audio_file}")

        # Compress audio for transcription
        compressed_filename = f"compressed_{uid}.mp3"

        if not compress_audio(actual_audio_file, compressed_filename):
            st.warning("⚠️ Compression failed, using original file...")
            compressed_filename = actual_audio_file

        # Transcription with Whisper
        st.write("🎤 Transcribing audio with OpenAI Whisper...")
        try:
            with open(compressed_filename, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=f, response_format="verbose_json"
                )

            transcript_text = " ".join([seg.text for seg in transcript.segments])
            segments = transcript.segments

            # Cache the results
            st.session_state["transcript_text"] = transcript_text
            st.session_state["transcript_segments"] = segments
            st.session_state["transcript_url"] = uid

            st.success("✅ Transcription completed successfully!")
            log_usage(url, selected_type, status="success", method="whisper")

            # Clean up temporary files
            try:
                if os.path.exists(actual_audio_file):
                    os.remove(actual_audio_file)
                if (
                    os.path.exists(compressed_filename)
                    and compressed_filename != actual_audio_file
                ):
                    os.remove(compressed_filename)
                st.info("🧹 Temporary files cleaned up")
            except Exception as e:
                print(f"Cleanup error: {e}")

        except Exception as e:
            st.error(f"❌ Transcription failed: {e}")
            log_usage(url, selected_type, status="transcription_failed")

            # Clean up files on error
            try:
                if os.path.exists(actual_audio_file):
                    os.remove(actual_audio_file)
                if (
                    os.path.exists(compressed_filename)
                    and compressed_filename != actual_audio_file
                ):
                    os.remove(compressed_filename)
            except:
                pass
            st.stop()

    # Show transcript info
    estimated_tokens = len(tokenizer.encode(transcript_text))
    st.info(
        f"📊 Transcript ready: ~{estimated_tokens} tokens | Method: Whisper Audio Transcription"
    )

    # Prepare summary prompts
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

    # Handle long transcripts with chunking
    if estimated_tokens + 900 > max_tokens:
        st.warning(
            "📝 Transcript is long — using intelligent chunking for better results."
        )
        chunks = chunk_transcript(transcript_text)
        for i, chunk in enumerate(chunks):
            st.write(f"🧠 Analyzing chunk {i+1} of {len(chunks)}...")
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

    # Generate final summary
    if chunked:
        st.write("🔄 Synthesizing final summary from all chunks...")
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
        st.write("🧠 Generating summary...")
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

# Display results
if st.session_state.get("show_summary"):
    st.subheader("🧠 Overall Summary")
    st.markdown(st.session_state["summary"], unsafe_allow_html=True)

    if "chunk_summaries" in st.session_state:
        st.subheader("🧩 Chunk Summaries")
        for i, chunk in enumerate(st.session_state["chunk_summaries"]):
            with st.expander(f"View Part {i+1} Summary"):
                st.markdown(chunk, unsafe_allow_html=True)

    if st.button("Show Full Transcript"):
        st.subheader("📜 Full Transcript")
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
