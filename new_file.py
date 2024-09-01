import json
import time
import requests
import pprint
from secrets import API_KEY_LISTENNOTES, API_KEY_ASSEMBLYAI
from transformers import pipeline as transformers_pipeline

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

    podcast_title = data.get("podcast", {}).get('title')
    episode_title = data.get('title')
    thumbnail = data.get('thumbnail')
    audio = data.get('audio')

    return audio, thumbnail, podcast_title, episode_title

def transcribe(audio_url, auto_chapters=False):
    transcript_request = {
      'audio_url': audio_url,
      'auto_chapters': 'True' if auto_chapters else 'False'
    }

    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers_assemblyai)
    pprint.pprint(transcript_response.json())
    return transcript_response.json()['id']

def summarize_text(text, model_name="facebook/bart-large-cnn"):
    summarizer = transformers_pipeline("summarization", model=model_name)
    summary = summarizer(text, max_length=150, min_length=40, do_sample=False)
    return summary[0]['summary_text']

def poll(transcript_id, **kwargs):
    polling_endpoint = transcript_endpoint + '/' + transcript_id
    polling_response = requests.get(polling_endpoint, headers=headers_assemblyai)

    if polling_response.json()['status'] == 'completed':
        transcript_text = polling_response.json()['text']

        filename = transcript_id + '.txt'
        with open(filename, 'w') as f:
            f.write(transcript_text)

        chapters = polling_response.json().get('chapters', [])
        data = {
            'chapters': chapters,
            'transcript': transcript_text
        }
        for key, value in kwargs.items():
            data[key] = value

        # Summarize the transcript
        summary = summarize_text(transcript_text)
        data['summary'] = summary

        filename = transcript_id + '_chapters.json'
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

        print('Transcript and summary saved')
        return True
    return False

def pipeline(episode_id):
    audio, thumbnail, podcast_title, episode_title = get_episode_audio_url(episode_id)
    transcribe_id = transcribe(audio, auto_chapters=True)

    while True:
        result = poll(transcribe_id, audio=audio, thumbnail=thumbnail, podcast_title=podcast_title, episode_title=episode_title)
        if result:
            break
        print("waiting for 60 sec")
        time.sleep(60)

if __name__ == "__main__":
    pipeline("20bf194224434ebbba8462ea8136cc3d")
