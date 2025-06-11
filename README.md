# ClipNotes: AI Summarizer for YouTube Videos

A lightweight Streamlit app that uses OpenAI’s Whisper and GPT-4 to generate a variety of summaries for YouTube videos. When the video is too long or complex, use ClipNotes to get the gist — fast.

Ideal for lectures, interviews, podcasts, or talks — especially when the topic is dense or nuanced.

### 🔍 Summary Styles
Choose from five formats to suit your needs:

- **Basic** — a summary in 5 or so sentences  
- **Bullets** — 5–10 key points  
- **Quotes** — 5–10 compelling quotes with timestamps  
- **Insights** — strategic takeaways with brief explanations  
- **Newbie** — explains the core ideas as if you're new to the topic

### ✅ Use Cases
- Save time by skimming key points instead of watching the entire video  
- Extract quotes or highlights for articles, newsletters, or research  
- Understand complex topics in simplified language  
- Capture takeaways for strategic or editorial decision-making

### 🧠 Powered By
- `openai.Whisper` for transcription  
- `gpt-4` for summary generation  
- `yt-dlp` for audio extraction from YouTube  
- `streamlit` for the user interface

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

### 👋 Personal Note
This project was built by [Marcus Chan](https://www.linkedin.com/in/marcuslowchan/) to explore the intersection of generative AI and applied editorial innovation. It reflects an ongoing journey to blend storytelling expertise with growing AI fluency.