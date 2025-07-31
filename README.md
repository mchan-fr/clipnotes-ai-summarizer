### 🎬 ClipNotes: AI Summarizer for YouTube Videos

A lightweight Streamlit app that transforms long YouTube videos into clear, concise summaries — powered by OpenAI’s Whisper and GPT-4.

ClipNotes is ideal for interviews, lectures, podcasts, or any spoken-word video you don’t have time to watch in full. Just paste a link, choose a summary format, and get the gist — fast.

---

### 📝 Summary Formats

Choose from five distinct summary styles:

- **Basic** — a short 5–7 sentence recap  
- **Bullets** — 5–10 key points  
- **Quotes** — 5–10 compelling pull-quotes  
- **Insights** — strategic takeaways with brief explanations  
- **Newbie** — simplified breakdowns for curious beginners

---

### ✅ Use Cases

- Skim long content before meetings or research  
- Extract key moments for newsletters or social posts  
- Get simplified explanations of complex topics  
- Highlight strategic lessons from expert interviews
- Preview expert conversations before watching in full

---

### 🚀 What’s New (v2)

- ✅ Chunking added to allow for videos of any length  
- ✅ Chunk-by-chunk detail added alongside overall summary  
- ✅ Clearer error messages for failed downloads/transcripts  
- ✅ UI update with usage notes and styling polish  

---

### 🧠 Powered By

- [`Whisper`](https://platform.openai.com/docs/guides/speech-to-text) for transcription  
- [`gpt-4`](https://platform.openai.com/docs/guides/gpt) for summarization  
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) for YouTube audio extraction  
- [`ffmpeg`](https://ffmpeg.org/) for audio compression  
- [`streamlit`](https://streamlit.io/) for the frontend

### 🛠️ How to Run Locally (for macOS/Linux/Windows)

Follow these steps to clone and run the app locally:

1. Clone the repo

```bash
git clone https://github.com/mchan-fr/clipnotes-ai-summarizer.git
cd clipnotes-ai-summarizer
```

2. Create a virtual environment and activate it

- **macOS/Linux**:

```bash
python3 -m venv venv
source venv/bin/activate
```

- **Windows**:

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Add your OpenAI API key

ClipNotes supports both local and Streamlit Cloud environments.

For local use, create a .env file in the root directory (if it doesn’t exist) and add:

```env
OPENAI_API_KEY=your_actual_api_key_here
```

For Streamlit Cloud, go to your app → Settings → Secrets, and add:

```bash
OPENAI_API_KEY = your_actual_api_key_here
```

The app will automatically detect the correct environment and use the appropriate API key. No code changes needed.

5. Run the app

```bash
streamlit run summarizer_app_github.py
```

The app will open in your default browser.

### ⚠️ Limitations
	•	Tool doesn't distinguish between voices, so quality of results could be affected by number of speakers
	•	English audio only
	•	YouTube Shorts or DRM-restricted videos may not work

### 👋 Personal Note
This project was built by [Marcus Chan](https://www.linkedin.com/in/marcuslowchan/) — editorial leader turned GenAI builder — as part of an ongoing journey to fuse content strategy with practical, AI-powered tools.