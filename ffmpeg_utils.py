from subprocess import check_output
from LogDecorator import LogDecorator

@LogDecorator()
def create_slideshow(concat_filepath, output_filepath):
    slideshow_command = f"ffmpeg -y -safe 0 -protocol_whitelist file,http,https,tcp,tls -i {concat_filepath} -c:v libx264 -crf 23 -pix_fmt yuv420p {output_filepath}"
    check_output(slideshow_command, shell=True)

@LogDecorator()
def fade_in_fade_out(video_filepath, fade_time, output_filepath):
    fade_in_fade_out_command = f'ffmpeg -y -i {video_filepath} -filter_complex "fade=d={fade_time}, reverse, fade=d={fade_time}, reverse" {output_filepath}'
    check_output(fade_in_fade_out_command, shell=True)

@LogDecorator()
def resize_image(input_filepath, width, height, output_filepath):
    resize_command = f'ffmpeg -y -i {input_filepath} -vf "scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2" {output_filepath}'
    check_output(resize_command, shell=True)

@LogDecorator()
def add_audio_to_video(video_filepath, audio_filepath, output_filepath):
    add_audio_command = f'ffmpeg -y -i {video_filepath} -i {audio_filepath} -c:v libx264 -c:a aac {output_filepath}'
    check_output(add_audio_command, shell=True)

@LogDecorator()
def change_audio_speed(audio_filepath, multiplier, output_filepath):
    command = f'ffmpeg -y -i {audio_filepath} -filter:a "atempo={str(multiplier)}" -vn {output_filepath}'
    check_output(command, shell=True)

@LogDecorator()
def change_video_speed(video_filepath, multiplier, output_filepath):
    command = f'ffmpeg -y -i {video_filepath} -filter_complex "[0:v]setpts={str(float(1/multiplier))}*PTS[v];[0:a]atempo={str(multiplier)}[a]" -map "[v]" -map "[a]" {output_filepath}'
    check_output(command, shell=True, stderr=log)

@LogDecorator()
def media_to_mono_flac(media_filepath, mono_filepath):
    flac_to_mono_flac_command = f'ffmpeg -y -i {media_filepath} -c:a flac -ac 1 {mono_filepath}'
    check_output(flac_to_mono_flac_command, shell=True)

# TODO: If you start to close to the beginning of a video, we fail for lookahead
@LogDecorator()
def download_video(url_one, url_two, start_time, end_time, output, safety_buffer=5, lookahead=10):
    clip_length = end_time - start_time + (2 * safety_buffer)
    ffmpeg_command = f'ffmpeg -y -ss {seconds_to_timecode(start_time - lookahead)} -i "{url_one}" -ss {seconds_to_timecode(start_time - lookahead)} -i "{url_two}" -map 0:v -map 1:a -ss {lookahead - safety_buffer} -t {seconds_to_timecode(clip_length)} -c:v libx264 -c:a aac {output}'
    check_output(ffmpeg_command, shell=True)

@LogDecorator()
def get_audio_length(audio_filepath):
    ffmpeg_command = f'ffprobe -i {audio_filepath} -show_entries format=duration -v quiet -of csv="p=0"'
    length = check_output(ffmpeg_command, shell=True)
    return float(length)
