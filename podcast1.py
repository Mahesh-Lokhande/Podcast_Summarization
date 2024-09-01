import time
import requests
from transformers import BartTokenizer, BartForConditionalGeneration
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

# Load BART model and tokenizer
bart_tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')
bart_model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')

def get_episode_audio_url(episode_id):
    url = Listennotees_episode_endpoint + '/' + episode_id
    response = requests.request('GET', url, headers=headers_listennotes)
    data = response.json()

    if 'audio' in data:
        audio = data['audio']
    else:
        audio = None

    return audio

def transcribe(audio_url, auto_chapters=False):
    transcript_request = {
        'audio_url': audio_url,
        'auto_chapters': 'True' if auto_chapters else 'False'
    }

    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers_assemblyai)
    return transcript_response.json()['id']

def summarize_transcript(transcript_text):
    # Prepare input for BART model
    input_ids = bart_tokenizer.encode("summarize: " + transcript_text, return_tensors="pt", max_length=1024, truncation=True)
    attention_mask = bart_tokenizer.encode("summarize: " + transcript_text, return_tensors="pt", max_length=1024, truncation=True, return_attention_mask=True)['attention_mask']

    # Generate summary using BART model
    summary_ids = bart_model.generate(input_ids, attention_mask=attention_mask, num_beams=4, max_length=150, early_stopping=True)
    summary = bart_tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    return summary

def pipeline(episode_id):
    audio_url = get_episode_audio_url(episode_id)
    if audio_url:
        transcribe_id = transcribe(audio_url, auto_chapters=True)

        while True:
            polling_endpoint = transcript_endpoint + '/' + transcribe_id
            polling_response = requests.get(polling_endpoint, headers=headers_assemblyai)

            if polling_response.json()['status'] == 'completed':
                with open(transcribe_id + '.txt', 'w') as f:
                    f.write(polling_response.json()['text'])
                with open(transcribe_id + '.txt', 'r') as f:
                    transcript_text = f.read()
                    summary = summarize_transcript(transcript_text)
                    print("Summary:", summary)
                break
            print("waiting for 60 sec")
            time.sleep(60)
    else:
        print("Error: Unable to retrieve audio URL for the episode.")

if __name__ == "__main__":
    pipeline("20bf194224434ebbba8462ea8136cc3d")