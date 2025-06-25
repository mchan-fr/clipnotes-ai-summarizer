### 🎬 ClipNotes: AI Summarizer for YouTube Videos

A lightweight Streamlit app that turns 25-minute YouTube videos into quick, high-value summaries using OpenAI’s Whisper and GPT-4.

ClipNotes is ideal for medium-length interviews, lectures, podcasts, or any spoken-word video you don’t have time to watch in full. Just paste a link, choose a summary format, and get the gist — fast.

---

### 📝 Summary Formats

Choose from five distinct summary styles:

- **Basic** — a short 5–7 sentence recap  
- **Bullets** — 5–10 key points  
- **Quotes** — timestamped excerpts (5–10 strong lines)  
- **Insights** — strategic takeaways with explanations  
- **Newbie** — simplified breakdowns for curious beginners

---

### ✅ Use Cases

- Skim content before watching or sharing  
- Extract key moments for newsletters or recaps  
- Get simplified explanations of complex topics  
- Highlight strategic lessons from expert interviews

---

### 🚀 What’s New (v1.1)

- ✅ Audio compression added to support longer videos  
- ✅ Token length safeguards to avoid GPT-4 errors  
- ✅ Clearer error messages for failed downloads/transcripts  
- ✅ UI update with usage notes and styling polish  
- ✅ Works on videos up to ~25 minutes (token safe zone)

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

Open the `.env` file included in the repo and replace the placeholder with your actual API key:

```env
OPENAI_API_KEY=your_actual_api_key_here
```

5. Run the app

```bash
streamlit run summarizer_app_github.py
```

The app will open in your default browser.

### ⚠️ Limitations
	•	Videos longer than 25 minutes may exceed GPT-4’s token limit
	•	English audio only
	•	YouTube Shorts or DRM-restricted videos may not work

### 👋 Personal Note
This project was built by [Marcus Chan](https://www.linkedin.com/in/marcuslowchan/) — editorial leader turned GenAI builder — as part of an ongoing journey to fuse content strategy with practical, AI-powered tools.