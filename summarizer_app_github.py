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

# Previous code: client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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


# Improved audio download function with better error handling
def download_audio(url, output_filename):
    """
    Download audio from YouTube URL with multiple fallback strategies
    """
    commands_to_try = [
        # Strategy 1: Use latest working approach with tv_embedded client
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--extractor-args",
            "youtube:player_client=tv_embedded",
            "--no-check-certificate",
            "--output",
            output_filename,
            url,
        ],
        # Strategy 2: Use mediaconnect client (often bypasses restrictions)
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--extractor-args",
            "youtube:player_client=mediaconnect",
            "--output",
            output_filename,
            url,
        ],
        # Strategy 3: Use web client with embed bypass
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--extractor-args",
            "youtube:player_client=web_embedded",
            "--output",
            output_filename,
            url,
        ],
        # Strategy 4: Try with cookies simulation
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--extractor-args",
            "youtube:player_client=web",
            "--add-header",
            "Cookie: CONSENT=YES+cb",
            "--user-agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "--output",
            output_filename,
            url,
        ],
        # Strategy 5: Use android_testsuite (sometimes works)
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--extractor-args",
            "youtube:player_client=android_testsuite",
            "--output",
            output_filename,
            url,
        ],
        # Strategy 6: Try basic web with different user agent
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--user-agent",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "--output",
            output_filename,
            url,
        ],
        # Strategy 7: Use mweb client (mobile web)
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--extractor-args",
            "youtube:player_client=mweb",
            "--output",
            output_filename,
            url,
        ],
        # Strategy 8: Last resort - basic command
        ["yt-dlp", "-x", "--audio-format", "mp3", "--output", output_filename, url],
    ]

    for i, command in enumerate(commands_to_try):
        try:
            st.write(f"Attempting download method {i+1}/{len(commands_to_try)}...")
            st.code(
                " ".join(command), language="bash"
            )  # Show the actual command being run

            # Run with timeout and capture output
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                st.success(f"Audio downloaded successfully using method {i+1}")
                return True
            else:
                st.warning(f"Method {i+1} failed with return code {result.returncode}")
                if result.stderr:
                    st.text(f"STDERR: {result.stderr[:300]}...")
                if result.stdout:
                    st.text(f"STDOUT: {result.stdout[:300]}...")

        except subprocess.TimeoutExpired:
            st.error(
                "Download timed out (5 minutes). The video might be too long or connection is slow."
            )
        except subprocess.CalledProcessError as e:
            st.warning(f"Method {i+1} failed with error code {e.returncode}")
        except FileNotFoundError:
            st.error(
                "yt-dlp not found. Please ensure it's installed: pip install yt-dlp"
            )
            return False
        except Exception as e:
            st.warning(f"Method {i+1} failed with exception: {str(e)}")

    return False


# Improved compression function
def compress_audio(input_file, output_file):
    """
    Compress audio file for transcription with error handling
    """
    ffmpeg_commands = [
        # Primary command
        [
            "ffmpeg",
            "-y",  # -y to overwrite output files
            "-i",
            input_file,
            "-ar",
            "16000",
            "-ac",
            "1",
            "-q:a",
            "9",  # Lower quality for smaller file
            output_file,
        ],
        # Fallback without quality setting
        ["ffmpeg", "-y", "-i", input_file, "-ar", "16000", "-ac", "1", output_file],
    ]

    for i, command in enumerate(ffmpeg_commands):
        try:
            st.write(f"Attempting compression method {i+1}/{len(ffmpeg_commands)}...")
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
            )

            if result.returncode == 0:
                st.success(f"Audio compressed successfully using method {i+1}")
                return True
            else:
                st.warning(f"Compression method {i+1} failed: {result.stderr[:200]}...")

        except subprocess.TimeoutExpired:
            st.error("Audio compression timed out")
        except FileNotFoundError:
            st.error("ffmpeg not found. Please ensure it's installed.")
            return False
        except Exception as e:
            st.warning(f"Compression method {i+1} failed: {str(e)}")

    return False


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
    <p style='margin-top: 0;'>Paste a YouTube URL below, pick a summary style, select a processing speed (or leave it on the default) and hit generate. Run time will largely depend on how long the video is (I've had a 20-minute video take 2 minutes to process, while a 2-hour video took 20 minutes; your mileage may vary). Also:</p>

    <ul style='margin-top: 0.5em;'>
        <li>✅&nbsp;&nbsp;Use standard YouTube videos (Shorts may not work)</li>
        <li>❌&nbsp;&nbsp;Don't input music videos or similar that may have DRM locks</li>
        <li>🔍&nbsp;&nbsp;For additional context or timestamps, search the transcript at the bottom</li>
        <li>🎭&nbsp;&nbsp;Tool doesn't differentiate between voices, which can affect results</li>
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

        # Use temporary files to avoid conflicts
        audio_filename = f"downloaded_{uuid.uuid4().hex}.%(ext)s"

        # Try to download audio
        if not download_audio(url, audio_filename):
            st.error(
                "Failed to download audio after trying multiple methods. This could be due to:"
            )
            st.markdown(
                """
            - **YouTube's enhanced anti-bot measures** (most common cause)
            - Video is age-restricted or region-blocked
            - Video has download restrictions
            - Your hosting platform's IP is blocked by YouTube
            - Network connectivity issues
            
            **Potential solutions:**
            - Try a different video to test if the issue is video-specific
            - Wait 30-60 minutes and try again (temporary IP blocking)
            - Use a VPN if testing locally
            - Consider using YouTube's official API for transcripts (limited availability)
            """
            )

            # Offer alternative: YouTube API transcript extraction
            st.info(
                "💡 **Alternative:** Some videos have auto-generated captions that can be extracted without downloading audio."
            )
            if st.button("Try YouTube Transcript API (if available)"):
                try:
                    # This would require youtube-transcript-api package
                    st.warning(
                        "This feature requires the youtube-transcript-api package. Add it to requirements.txt to enable this fallback."
                    )
                except:
                    pass
            log_usage(url, selected_type, status="download_failed")
            st.stop()

        # Find the actual downloaded file (yt-dlp adds extension)
        downloaded_files = [
            f for f in os.listdir(".") if f.startswith(f"downloaded_{uid}")
        ]
        if not downloaded_files:
            # Fallback: look for files with the UUID
            downloaded_files = [
                f
                for f in os.listdir(".")
                if uuid.uuid4().hex in f and f.startswith("downloaded_")
            ]

        if not downloaded_files:
            st.error("Could not find downloaded audio file")
            st.stop()

        actual_audio_file = downloaded_files[0]
        st.success("Audio downloaded successfully.")

        st.write("Compressing audio for transcription...")
        compressed_filename = f"compressed_{uuid.uuid4().hex}.mp3"

        if not compress_audio(actual_audio_file, compressed_filename):
            st.error("Failed to compress audio. Trying to use original file...")
            compressed_filename = actual_audio_file

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

            # Clean up temporary files
            try:
                if os.path.exists(actual_audio_file):
                    os.remove(actual_audio_file)
                if (
                    os.path.exists(compressed_filename)
                    and compressed_filename != actual_audio_file
                ):
                    os.remove(compressed_filename)
            except Exception as e:
                print(f"Cleanup error: {e}")

        except Exception as e:
            st.error(f"Error during transcription: {e}")
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
