from subprocess import check_output
from LogDecorator import LogDecorator
import ffmpeg
import os

# Source for verbosity fix https://superuser.com/questions/326629/how-can-i-make-ffmpeg-be-quieter-less-verbose

@LogDecorator()
def create_slideshow(concat_filepath, output_filepath):
    slideshow_command = f'ffmpeg -y -hide_banner -loglevel panic -safe 0 -protocol_whitelist file,http,https,tcp,tls -i "{concat_filepath}" -c:v libx264 -crf 23 -pix_fmt yuv420p "{output_filepath}"'
    check_output(slideshow_command, shell=True)


@LogDecorator()
def resize_image(input_filepath, width, height, output_filepath):
    resize_command = f'ffmpeg -y -hide_banner -loglevel panic -i "{input_filepath}" -vf "scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2" "{output_filepath}"'
    check_output(resize_command, shell=True)


# TODO: If you start to close to the beginning of a video, we fail for lookahead
@LogDecorator()
def download_video(url_one, url_two, start_time, end_time, output, safety_buffer=5, lookahead=10):
    clip_length = end_time - start_time + (2 * safety_buffer)
    ffmpeg_command = f'ffmpeg -y -hide_banner -loglevel panic -ss {seconds_to_timecode(start_time - lookahead)} -i "{url_one}" -ss {seconds_to_timecode(start_time - lookahead)} -i "{url_two}" -map 0:v -map 1:a -ss {lookahead - safety_buffer} -t {seconds_to_timecode(clip_length)} -c:v libx264 -c:a aac {output}'
    check_output(ffmpeg_command, shell=True)



@LogDecorator()
def concat_images(frames_information, output_filepath, **kwargs):
#    slideshow_command = f"ffmpeg -y -hide_banner -loglevel panic -safe 0 -protocol_whitelist file,http,https,tcp,tls -i {concat_filepath} -c:v libx264 -crf 23 -pix_fmt yuv420p {output_filepath}"
#    check_output(slideshow_command, shell=True)
#    ins = [ffmpeg.input('frame/%1d.jpg').filter('setdar', '16/9') for f in frames_information]
#    ffmpeg.concat(*ins, v=1, **{'-ts_from_file': 1})\
#    ffmpeg.input('frame/%1d.jpg')\
#    .output(output_filepath, **kwargs)\
#    .run()
    with open('.tmp-concat.txt', 'w') as f:
        f.write('ffconcat version 1.0\n')
        for frame_information in frames_information:
            f.write(f'file {frame_information["image_filepath"]}\n')
            f.write(f'duration {frame_information["length"]}\n')
        f.write(f'file {frame_information["image_filepath"]}\n')

    slideshow_command = f'ffmpeg -y -hide_banner -loglevel panic -safe 0 -protocol_whitelist file,http,https,tcp,tls -i .tmp-concat.txt -c:v libx264 -crf 23 -pix_fmt yuv420p "{output_filepath}"'
    check_output(slideshow_command, shell=True)
    os.remove('.tmp-concat.txt')


@LogDecorator()
def fade_in_fade_out(video_filepath, fade_in_time, fade_out_time, output_filepath, **kwargs):
    length = get_media_length(video_filepath)

    i = ffmpeg.input(video_filepath)
    v = i.video\
    .filter('fade', **{'type': 'in', 'duration': fade_in_time})\
    .filter('fade', **{'type': 'out', 'duration': fade_out_time, 'start_time': length-fade_out_time-.1})\
    a = i.audio

    ffmpeg.output(a, v, output_filepath, **kwargs)\
    .run()


@LogDecorator()
def resize_video(input_filepath, output_filepath, width=1920, height=1080, ratio='16/9', **kwargs):
    i = ffmpeg.input(input_filepath)

    v = i.video\
    .filter('setdar', f'{ratio}')\
    .filter('scale', f'{width}x{height}')
    a = i.audio

    ffmpeg.output(a, v, output_filepath, **kwargs)\
    .run()


@LogDecorator()
def concat_videos(input_filepaths, output_filepath, **kwargs):
    ins = [ffmpeg.input(filepath) for filepath in input_filepaths]

    outs = []
    for i in ins:
        outs.append(i.video)
        outs.append(i.audio)

    ffmpeg.concat(*outs, a=1, v=1)\
    .output(output_filepath, **kwargs)\
    .run()

@LogDecorator()
def get_media_length(filepath):
    ffmpeg_command = f'ffprobe -i {filepath} -show_entries format=duration -v quiet -of csv="p=0"'
    length = check_output(ffmpeg_command, shell=True)
    return float(length)

@LogDecorator()
def change_video_speed(input_video_filepath, multiplier, output_filepath, **kwargs):
    ffmpeg.input(input_video_filepath).video\
    .filter('setpts', f'{1/multiplier}*PTS')\
    .output(output_filepath, **kwargs)\
    .run()


@LogDecorator()
def change_audio_speed(input_audio_filepath, multiplier, output_filepath, **kwargs):
    ffmpeg.input(input_audio_filepath).audio\
    .filter('atempo', multiplier)\
    .output(output_filepath, **kwargs)\
    .run()


@LogDecorator()
def add_audio_to_video(input_audio_filepath, input_video_filepath, output_filepath, **kwargs):
    # Common option used is --shortest which trims the output to the length of the shortest input
    a = ffmpeg.input(input_audio_filepath).audio
    v = ffmpeg.input(input_video_filepath).video
    ffmpeg.output(a, v, output_filepath, **kwargs)\
    .run()


@LogDecorator()
def media_to_mono_flac(input_filepath, output_filepath, **kwargs):
    if '.flac' != output_filepath[-5:]:
        raise ValueError(f'Output filename {output_filepath} does not end in ".flac"')

    a = ffmpeg.input(input_filepath).audio
    ffmpeg.output(a, output_filepath, ac=1, **kwargs)\
    .run()
