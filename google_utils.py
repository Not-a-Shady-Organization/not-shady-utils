import os
import io
import logging
from ffmpeg_utils import get_media_length

from utils import makedir

from google.cloud import storage
from google.cloud import language, speech_v1p1beta1
from google.cloud.language import enums, types
from google_images_download import google_images_download

from LogDecorator import LogDecorator


class MissingAPIKeyError(Exception):
    pass

# Check if API key file is loaded
api_key_filepath = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
if not os.path.exists(api_key_filepath):
    raise MissingAPIKeyError()




@LogDecorator()
def download_image(query, output_directory, image_directory):
    makedir(f'{output_directory}/{image_directory}')
    files = os.listdir(f'{output_directory}/{image_directory}')

    while files == []:
        response = google_images_download.googleimagesdownload()
        arguments = {
            "output_directory": output_directory,
            "image_directory": image_directory,
            "keywords": query,
            "format": "jpg",
            "limit": 1,
            # TODO: Drop exact sizing
#            "exact_size": "1920,1080",
             "size": "medium",
             "silent_mode": True
         }
        response.download(arguments)
        files = os.listdir(f'{output_directory}/{image_directory}')


    return f'{query}/{files[0]}'




@LogDecorator()
def upload_file_to_bucket(bucket_name, source_file_name, destination_blob_name, metadata=None):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)

    blob.metadata = metadata
    blob.patch()



@LogDecorator()
def upload_string_to_bucket(bucket_name, string, destination_blob_name, metadata=None):
    """Uploads a string to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(string)

    blob.metadata = metadata
    blob.patch()


@LogDecorator()
def download_as_string(bucket_name, blob_name):
    """Uploads a string to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_string().decode("utf-8")

@LogDecorator()
def list_blobs(bucket_name, bucket_dir_path=''):
    """Lists all the blobs in the bucket."""
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name)
    return [blob for blob in blobs if bucket_dir_path in blob.name]

@LogDecorator()
def get_blob(bucket_path):
    client = storage.Client()
    bucket = client.get_bucket('craig-the-poet')
    return storage.Blob(bucket_path, bucket)


# Find entities in text and return in order of occurance
@LogDecorator()
def find_entities(text):
    # Instantiates a client
    client = language.LanguageServiceClient()

    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT
    )
    response = client.analyze_entities(document=document)
    entities = response.entities

    # Sort the entities by occurance in the source text
    by_occurance = sorted(entities, key=lambda e: text.index(e.mentions[0].text.content))
    return by_occurance



@LogDecorator()
def transcribe_audio(audio_filepath, **kwargs):
    client = speech_v1p1beta1.SpeechClient()
    enable_word_time_offsets = True
    enable_word_confidence = True
    config = {
        "enable_word_confidence": enable_word_confidence,
        "enable_word_time_offsets": enable_word_time_offsets,
        "language_code": 'en-US' if 'language_code' not in kwargs else kwargs['language_code'],
    }
    with io.open(audio_filepath, "rb") as f:
        content = f.read()
    audio = {"content": content}
    audio_length = get_media_length(audio_filepath)

    #If audio length is greater than a min, upload to bucket, use longrunningresponse call api
    if audio_length > 45:
        storage_client = storage.Client()

        #deal with audio path names
        upload_file_to_bucket("craig-the-poet", audio_filepath, "temp_long_file")
        audio['uri'] = "gs://craig-the-poet/temp_long_file"
        operation = client.long_running_recognize(config, audio)
        response = operation.result(timeout=10000)

        word_dict = {}

        for result in response.results:
            alternative = result.alternatives[0]
            words = alternative.words
            for word in words:
                if str(word.word) in word_dict.keys():
                    word_dict[str(word.word).lower()].append(word)
                else:
                    word_dict[str(word.word).lower()] = [word]
        bucket = storage_client.bucket("craig-the-poet")
        blob = bucket.blob("temp_long_file")
        blob.delete()
        return word_dict

    response = client.recognize(config, audio)

    # TODO: We throw out alternatives and only use the first one.. they may be helpful
    # The first result includes start and end time word offsets
    try:
        result = response.results[0]
    except:
        return None

    logging.debug(response)
    logging.debug(result)

    # First alternative is the most probable result
    alternative = result.alternatives[0]
    return alternative


@LogDecorator()
def interval_of(word, transcription):
    if type(transcription) is dict:
        if word.lower() not in transcription.keys():
            return None

        if len(transcription[word.lower()]) > 1:
            entry = transcription[word.lower()].pop(0)
        else:
            entry = transcription[word.lower()][0]
        start_time = float(str(entry.start_time.seconds) + '.' + str(entry.start_time.nanos))
        end_time = float(str(entry.end_time.seconds) + '.' + str(entry.end_time.nanos))
        return(start_time, end_time)

    transcibed_words = [w for w in transcription.words]
    if word.lower() not in [w.word.lower() for w in transcibed_words]:
        return None

    for w in transcibed_words:
        if w.word.lower() == word.lower():
            start_time = float(str(w.start_time.seconds) + '.' + str(w.start_time.nanos))
            end_time = float(str(w.end_time.seconds) + '.' + str(w.end_time.nanos))
            return (start_time, end_time)


@LogDecorator()
def synthesize_text(text, output_filepath, tts_params):
    """Synthesizes speech from the input string of text."""
    from google.cloud import texttospeech
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.types.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.types.VoiceSelectionParams(
        language_code='en-US',
        #ssml_gender=texttospeech.enums.SsmlVoiceGender.FEMALE
#        name='en-US-Wavenet-A'
#        name='en-AU-Wavenet-B',
        name='en-IN-Wavenet-C' if 'name' not in tts_params else tts_params['name'],
    )

    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3,
        speaking_rate=1. if 'speaking_rate' not in tts_params else tts_params['speaking_rate'],
        pitch=0 if 'pitch' not in tts_params else tts_params['pitch']
    )

    response = client.synthesize_speech(input_text, voice, audio_config)

    # The response's audio_content is binary.
    with open(output_filepath, 'wb') as out:
        out.write(response.audio_content)



# [START tts_synthesize_ssml]
@LogDecorator()
def synthesize_ssml(ssml):
    """Synthesizes speech from the input string of ssml.
    Note: ssml must be well-formed according to:
        https://www.w3.org/TR/speech-synthesis/
    Example: <speak>Hello there.</speak>
    """
    from google.cloud import texttospeech
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.types.SynthesisInput(ssml=ssml)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.types.VoiceSelectionParams(
        language_code='en-US',
        ssml_gender=texttospeech.enums.SsmlVoiceGender.FEMALE)

    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    response = client.synthesize_speech(input_text, voice, audio_config)

    # The response's audio_content is binary.
    with open('output.mp3', 'wb') as out:
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')
# [END tts_synthesize_ssml]
