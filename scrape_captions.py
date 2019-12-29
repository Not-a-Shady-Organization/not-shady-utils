import argparse
from youtube_utils import download_captions
from utils import timecode_to_seconds
import os
from utils import BadOptionsError, clean_word
from CaptionedWord import add_captioned_words, list_video_codes


# Bucket dirs
BUCKET_NAME = 'videograms'
VOCABULARY_BUCKET_DIR = 'vocabulary'

# Local dirs
CAPTIONS_DIR = 'captions'

MAX_DATASTORE_BATCH = 500


def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip(*args)


def scrape_captions(video_code):
    # Validate options
    if not video_code:
        raise BadOptionsError('Must specify a video code')

    # This is where captions will always be downloaded (extension if hardcoded by youtube-dl)
    filepath = f'{CAPTIONS_DIR}/{video_code}.en.vtt'

    # Raise an error if the video is already in our data
    if video_code in list_video_codes():
        raise ValueError(f'Video code {video_code} already exists in the datastore')

    # Download the captions to local disk
    download_captions(video_code)

    # Grab every words' time interval and write to Datastore
    ret = atomize_captions(video_code, filepath)
    return ret


def atomize_captions(video_code, caption_filepath):
    '''Finds start and end time of all words in .vtt caption file and writes to vocabulary.'''

    master_cue_list = []

    with open(caption_filepath) as f:
        saw_line_timing = False
        line_start = None
        line_end = None

        for line in f.readlines():
            if '-->' in line:
                if saw_line_timing:
                    master_cue_list += [line_start, line_end]

                saw_line_timing = True
                start = f'<{line.split()[0]}>'
                end = f'<{line.split()[2]}>'
                master_cue_list += [start]
                line_start = start
                line_end = end

            if '<c>' in line:
                saw_line_timing = False
                cue_line_list = line.replace('<c>', '').replace('</c>', '').replace('<', ' <').split()
                master_cue_list += cue_line_list
                master_cue_list += [line_end]


    for i, entry in enumerate(master_cue_list):
        if '<' in entry:
            seconds = timecode_to_seconds(entry)
            master_cue_list[i] = seconds

    # The master_cue_list is just all the times as floats and the words as strings
    # They all live in order, but next to each other

    captioned_words = []
    for i, entry in enumerate(master_cue_list):
        if type(entry) == str:
            captioned_words.append({
                'word': clean_word(entry),  # By using clean word, we map many written variations on a word to one value
                'start_time': master_cue_list[i-1],
                'end_time': master_cue_list[i+1],
                'video_code': video_code
            })

    for captioned_words_batch in grouper(MAX_DATASTORE_BATCH, captioned_words):
        add_captioned_words(captioned_words_batch)

    return {'captioned_words': len(captioned_words)}



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--video-code')
    args = parser.parse_args()

    print(scrape_captions(**vars(args)))
