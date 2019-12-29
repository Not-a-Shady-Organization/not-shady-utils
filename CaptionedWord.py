import os
from google.cloud import datastore

# TODO: Rename file as this is no longer class based
# TODO: Breakout into datastore_utils
# TODO: Make utils more modular with their package dependencies

PROJECT_ID = os.environ.get('PROJECT_ID', 'ccblender')

def add_captioned_words(captioned_words):
    client = datastore.Client(PROJECT_ID)
    batch = client.batch()
    batch.begin()

    for captioned_word_obj in captioned_words:
        # Create an instance of a Captioned Word key
        key = client.key('Captioned Word')

        # Create a value for the key
        captioned_word = datastore.Entity(
            key,
            exclude_from_indexes=[
                'start_time',
                'end_time'
            ]
        )

        # Give the value meaning
        captioned_word.update({
            'word': captioned_word_obj['word'],
            'video_code': captioned_word_obj['video_code'],
            'start_time': captioned_word_obj['start_time'],
            'end_time': captioned_word_obj['end_time']
        })

        batch.put(captioned_word)
    batch.commit()



def list_instances_of_word(word):
    client = datastore.Client(PROJECT_ID)
    query = client.query(kind='Captioned Word')
    query.add_filter('word', '=', word)
    return list(query.fetch())


def list_video_codes():
    client = datastore.Client(PROJECT_ID)
    query = client.query(kind='Captioned Word')
    query.distinct_on = ['video_code']
    query.projection = ['video_code']

    response_list = list(query.fetch())
    video_codes = [response['video_code'] for response in response_list]

    return video_codes
