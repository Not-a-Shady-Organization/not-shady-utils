from LogDecorator import LogDecorator
import os


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
