from subprocess import check_output
import youtube_dl
from LogDecorator import LogDecorator
import os
from async_utils import handle_requests
import json
from utils import get_datastore_credential


@LogDecorator()
def refresh_access_token(filepath):
    youtube_client_id = get_datastore_credential('YOUTUBE_CLIENT_ID')
    youtube_client_secret = get_datastore_credential('YOUTUBE_CLIENT_SECRET')
    youtube_refresh_token = get_datastore_credential('YOUTUBE_REFRESH_TOKEN')

    if not youtube_client_id or not youtube_client_secret or not youtube_refresh_token:
        raise ValueError(f'CLIENT_ID, CLIENT_SECRET, and REFRESH_TOKEN must be defined on GCP Datastore to enable YouTube uploads')

    # Load the template oauth2.json file with our credentials
    with open('youtube-oauth2.json.example', 'r') as f:
        oauth_dict = json.loads(f.read())

    # Use the refresh token to request a new access token
    requests = [{
        'method': 'POST',
        'url': 'https://accounts.google.com/o/oauth2/token',
        'json': {
            'client_id': youtube_client_id,
            'client_secret': youtube_client_secret,
            'refresh_token': youtube_refresh_token,
            'grant_type': 'refresh_token'
          }
    }]
    response = eval(handle_requests(requests)[0].decode('utf-8'))

    # Sub in new access token over the old
    oauth_dict['token_response'] = response

    # Write to file
    with open(filepath, 'w') as f:
        f.write(json.dumps(oauth_dict))





@LogDecorator()
def download_captions(video_code):
    video_url = 'https://www.youtube.com/watch?v=' + video_code

    # Define the Youtube extractor to only grab english subtitles
    ydl = youtube_dl.YoutubeDL({
        'outtmpl': 'captions/' + video_code,
        'skip_download': True,
        'noplaylist': True,
        'subtitleslangs': ['en'],
        'subtitlesformat': 'vtt',
        'writesubtitles': True,
        'writeautomaticsub': True
    })

    # Download
    with ydl:
        result = ydl.extract_info(video_url)

@LogDecorator()
def video_code_to_url(video_code):
    url = f'https://www.youtube.com/watch?v={video_code}'
    command = f'youtube-dl -g {url}'
    response = check_output(command, shell=True).decode().split('\n')[:-1]
    return response
