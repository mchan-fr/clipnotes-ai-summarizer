from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        query = parse_qs(parsed_url.query)
        return query.get('v', [None])[0]
    return None

def fetch_transcript(video_id, lang='en'):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
        return transcript
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

if __name__ == "__main__":
    url = input("Enter YouTube URL: ")
    video_id = extract_video_id(url)
    if not video_id:
        print("Invalid YouTube URL.")
    else:
        transcript = fetch_transcript(video_id)
        if transcript:
            for entry in transcript:
                print(f"[{entry['start']:.2f}s] {entry['text']}")
        else:
            print("No transcript available.")