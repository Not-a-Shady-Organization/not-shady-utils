from LogDecorator import LogDecorator
import os
import requests
import shutil
from subprocess import check_output
from datetime import datetime, timedelta


class BadOptionsError(Exception):
    pass




@LogDecorator()
def convert_to_date(s):
    if s == 'today':
        return datetime.now()
    if s == 'yesterday':
        return datetime.now() - timedelta(days=1)
    try:
        return datetime.strptime(s, "%m-%d-%Y")
    except ValueError:
        raise ValueError(f"Not a valid date: {s}")

@LogDecorator()
def download_image_from_url(url, output_filepath):
    resp = requests.get(url, stream=True)
    with open(output_filepath, 'wb') as f:
        resp.raw.decode_content = True
        shutil.copyfileobj(resp.raw, f)

@LogDecorator()
def text_to_image(text, output_filepath, font='BrushScriptI', font_size=240, font_color='white', background='black'):
    command = f'convert -background {background} -fill {font_color} -font {font} -pointsize {font_size} label:"{text}" {output_filepath}'
    check_output(command, shell=True)

@LogDecorator()
def seconds_to_timecode(seconds):
    remainder = seconds
    h = int(remainder) // 3600
    remainder = remainder - (h*3600)
    m = int(remainder) // 60
    remainder = remainder - (m*60)
    s = remainder % 60
    return f'{h}:{m}:{s}'

def makedir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

@LogDecorator()
def timecode_to_seconds(timecode):
    h, m, seconds = timecode[1:-1].split(':')
    s, ms = seconds.split('.')
    return int(h)*60*60 + int(m)*60 + int(s) + float(ms)/1000


# TODO: Make this cleaning function accessible across projects (often used)
@LogDecorator()
def clean_word(word):
    return ''.join([c for c in word.lower().replace(' ', '-') if c.isalpha() or c.isdigit() or c == '-']).rstrip()
