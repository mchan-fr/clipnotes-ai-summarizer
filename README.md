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

### 💻 Local Setup
1. Clone this repo.
2. Create a `.env` file in the root of the project:
3. Run the app:
```bash
streamlit run summarizer_app_github.py
```

### 👋 Personal Note
This project was built by [Marcus Chan](https://www.linkedin.com/in/marcuslowchan/) to explore the intersection of generative AI and applied editorial innovation. It reflects an ongoing journey to blend storytelling expertise with growing AI fluency.