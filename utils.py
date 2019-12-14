from LogDecorator import LogDecorator



@LogDecorator
def seconds_to_timecode(seconds):
    remainder = seconds
    h = int(remainder) // 3600
    remainder = remainder - (h*3600)
    m = int(remainder) // 60
    remainder = remainder - (m*60)
    s = remainder % 60
    return f'{h}:{m}:{s}'


@LogDecorator
def timecode_to_seconds(timecode):
    h, m, seconds = timecode[1:-1].split(':')
    s, ms = seconds.split('.')
    return int(h)*60*60 + int(m)*60 + int(s) + float(ms)/1000
