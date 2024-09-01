import json
import time
import requests
import pprint
from secrets import API_KEY_LISTENNOTES,API_KEY_ASSEMBLYAI
from transformers import pipeline

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

  if 'thumbnail' in data:
    thumbnail = data['thumbnail']
  else:
    thumbnail = None

  if 'audio' in data:
    audio = data['audio']
  else:
    audio = None

  return audio, thumbnail, podcast_title, episode_title

def transcribe(audio_url, auto_chapters=False):
    transcript_request = {
      'audio_url': audio_url,
      'auto_chapters': 'True' if auto_chapters else 'False'
    }

    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers_assemblyai)
    pprint.pprint(transcript_response.json())
    return transcript_response.json()['id']

def poll(transcript_id, **kwargs):
  polling_endpoint = transcript_endpoint + '/' + transcript_id
  polling_response = requests.get(polling_endpoint, headers=headers_assemblyai)

  if polling_response.json()['status'] == 'completed':
    filename = transcript_id + '.txt'
    with open(filename, 'w') as f:
      f.write(polling_response.json()['text'])

    filename = transcript_id + '_chapters.json'
    with open(filename, 'w') as f:
      chapters = polling_response.json()['chapters']
      data = {'chapters': chapters}
      for key, value in kwargs.items():
        data[key] = value
      json.dump(data, f, indent=4)

    print('Transcript saved')
    return  True
  return False

def summarize(text):
  summarization_pipeline = pipeline('summarization')
  summary = summarization_pipeline(text, max_length=120, min_length=30, do_sample=False)
  return summary[0]['summary_text']

def pipeline(episode_id):
  audio, thumbnail, podcast_title, episode_title = get_episode_audio_url(episode_id)
  transcribe_id = transcribe(audio, auto_chapters=True)

  while True:
    result = poll(transcribe_id, audio=audio, thumbnail=thumbnail, podcast_title=podcast_title,
                episode_title=episode_title)
    if result:
      with open(transcribe_id + '.txt', 'r') as f:
        transcript = f.read()
      summary = summarize(transcript)
      print('Summary:', summary)
      break
    print("waiting for 60 sec")
    time.sleep(60)

if __name__ == "__main__":
  pipeline("20bf194224434ebbba8462ea8136cc3d")