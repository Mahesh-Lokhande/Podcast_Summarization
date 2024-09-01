import json
import time
import requests
from transformers import pipeline
from secrets import API_KEY_LISTENNOTES, API_KEY_ASSEMBLYAI

Listennotees_episode_endpoint = 'https://listen-api.listennotes.com/api/v2/episodes'
headers_listennotes = {
    'X-ListenAPI-Key': API_KEY_LISTENNOTES
}

transcript_endpoint = 'https://api.assemblyai.com/v2/transcript'
headers_assemblyai = {
    "authorization": API_KEY_ASSEMBLYAI,
    "content-type": "application/json"
}

def get_episode_audio_url(episode_id):
    url = Listennotees_episode_endpoint + '/' + episode_id
    response = requests.request('GET', url, headers=headers_listennotes)
    data = response.json()

    if 'podcast' in data:
        podcast_title = data["podcast"]['title']
    else:
        podcast_title = None

    if 'title' in data:
        episode_title = data['title']
    else:
        episode_title = None

    if 'audio' in data:
        audio = data['audio']
    else:
        audio = None

    return audio, podcast_title, episode_title

def transcribe(audio_url, auto_chapters=False):
    transcript_request = {
        'audio_url': audio_url,
        'auto_chapters': 'True' if auto_chapters else 'False'
    }

    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers_assemblyai)
    return transcript_response.json()['id']

def summarize_text(text, model_name):
    summarization = pipeline("summarization", model=model_name)
    summary = summarization(text, max_length=120, min_length=30, do_sample=False)
    return summary[0]['summary_text']

def execute_pipeline(episode_id):
    audio, podcast_title, episode_title = get_episode_audio_url(episode_id)
    transcribe_id = transcribe(audio, auto_chapters=True)

    while True:
        result = poll(transcribe_id, audio=audio, podcast_title=podcast_title,
                    episode_title=episode_title)
        if result:
            with open(f"{transcribe_id}_chapters.json", "r") as f:
                data = json.load(f)
                text = data['chapters'][0]['text']  # assuming the first chapter contains the text to summarize
                bart_summary = summarize_text(text, "facebook/bart-large-cnn")
                bert_summary = summarize_text(text, "bert-base-uncased")
                print("BART Summary:")
                print(bart_summary)
                print("BERT Summary:")
                print(bert_summary)
            break
        print("waiting for 60 sec")
        time.sleep(60)

if __name__ == "__main__":
    execute_pipeline("20bf194224434ebbba8462ea8136cc3d")
