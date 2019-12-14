from subprocess import check_output
import youtube_dl
from LogDecorator import LogDecorator

@LogDecorator
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

@LogDecorator
def video_code_to_url(video_code):
    url = f'https://www.youtube.com/watch?v={video_code}'
    command = f'youtube-dl -g {url}'
    response = check_output(command, shell=True).decode().split('\n')[:-1]
    return response
