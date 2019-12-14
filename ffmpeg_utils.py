from subprocess import check_output
from LogDecorator import LogDecorator

@LogDecorator()
def create_slideshow(concat_filepath, output_filepath):
    slideshow_command = f"ffmpeg -y -safe 0 -i {concat_filepath} -c:v libx264 -crf 23 -pix_fmt yuv420p {output_filepath}"
    check_output(slideshow_command, shell=True)

@LogDecorator()
def add_audio_to_video(video_filepath, audio_filepath, output_filepath):
    add_audio_command = f'ffmpeg -y -i {video_filepath} -i {audio_filepath} -c:v libx264 -c:a aac {output_filepath}'
    check_output(add_audio_command, shell=True)

@LogDecorator()
def change_audio_speed(audio_filepath, multiplier, output_filepath):
    command = f'ffmpeg -y -i {audio_filepath} -filter:a "atempo={str(multiplier)}" -vn {output_filepath}'
    check_output(command, shell=True)
