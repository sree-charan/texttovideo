import requests
import pyttsx3
from pydub import AudioSegment
import subprocess
import os
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import cv2
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip, TextClip
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:/Program Files/ImageMagick-7.1.1-Q16-HDRI/magick.exe"})



def request_text_from_api(question, suffix=""):
    try:
        api_url = "https://chat.sreecharan.in/?q="
        full_question = f"{suffix}{question}"
        full_url = api_url + full_question
        response = requests.get(full_url)
        response.raise_for_status()  # Raise exception for non-2xx status codes
        api_response = response.json()  # Parse response as JSON

        if api_response:
            response_text = api_response[0]['response']['response']
            response_text = response_text.replace("Answer: ", "")  # Remove prefix
            response_text = f"{response_text}"
            return response_text
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def download_and_crop_videos(keyword, per_page, output_folder):
    # Pexels API parameters
    API_KEY = "YJyuRKxYYKsFxPfwiKS6gcWrOFQ1zjbXYFhYYa658rLxcwYHoarew0Ww"

    # API endpoint
    url = f"https://api.pexels.com/videos/search?query={keyword}&per_page={per_page}"  # Add orientation parameter &orientation=portrait
    headers = {"Authorization": API_KEY}

    # Send API request
    response = requests.get(url, headers=headers)
    data = response.json()

    # Create folder to save the videos
    os.makedirs(output_folder, exist_ok=True)

    # Download and crop videos
    cropped_video_files = []
    i = 1

    for video in data["videos"]:
        # Download video
        video_url = video["video_files"][0]["link"]
        response = requests.get(video_url)
        video_path = os.path.join(output_folder, f"{i}.mp4")
        with open(video_path, 'wb') as f:
            f.write(response.content)

        # Crop video
        start_time = 0  # Start time of the clip
        end_time = 5  # End time of the clip
        output_path = os.path.join(output_folder, f"cropped_video_{video['id']}.mp4")
        ffmpeg_extract_subclip(video_path, start_time, end_time, targetname=output_path)
        cropped_video_files.append(output_path)

        # Delete original downloaded video
        os.remove(video_path)

        i += 1

    print("Videos downloaded, cropped, and original files deleted.")
    return cropped_video_files


def crop_videos_in_directory(folder_path):

    # List to store video files
    video_files = []

    # Iterate over files in the current directory
    for filename in os.listdir(folder_path):
        if filename.endswith('.mp4') and filename.startswith('cropped_'):
            file_path = os.path.join(folder_path, filename)
            video_files.append(file_path)

    # Crop each video file using OpenCV
    for video_file in video_files:
        output_file = f"resized_{os.path.basename(video_file)}"
        
        # Open the video file
        cap = cv2.VideoCapture(video_file)
        
        # Get the original video's width and height
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Calculate the desired width and height for a portrait orientation
        if width > height:
            desired_height = height
            desired_width = int(height * 9 / 16)  # Assuming 9:16 aspect ratio
        else:
            desired_width = width
            desired_height = int(width * 16 / 9)  # Assuming 9:16 aspect ratio

        # Calculate the x and y coordinates for cropping
        x_start = int((width - desired_width) / 2)
        x_end = x_start + desired_width
        y_start = int((height - desired_height) / 2)
        y_end = y_start + desired_height

        # Create a VideoWriter object to save the cropped video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_file, fourcc, 30.0, (desired_width, desired_height))

        # Read and crop each frame, then write it to the output video
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Crop the frame
            cropped_frame = frame[y_start:y_end, x_start:x_end]

            # Write the cropped frame to the output video
            out.write(cropped_frame)

        # Release the VideoCapture and VideoWriter objects
        cap.release()
        out.release()

        # Delete the original "cropped_" video file
        os.remove(video_file)

        print(f"Cropped video saved as {output_file} and original video deleted.")



def merge_videos(video_folder, output_file):
    # Get a list of video files in the folder
    video_files = [f for f in os.listdir(video_folder) if f.endswith('.mp4')]

    # Generate a list of input file paths
    input_files = [os.path.join(video_folder, video_file) for video_file in video_files]

    # Create a FFmpeg filter string to resize videos
    filter_string = ""
    for i in range(len(input_files)):
        filter_string += f"[{i}:v]scale=720:1280,setsar=1[v{i}];"
    filter_string += "".join(f"[v{i}]" for i in range(len(input_files)))
    filter_string += f"concat=n={len(input_files)}:v=1:a=0[outv]"

    # Run FFmpeg to concatenate and resize videos
    command = ['ffmpeg', '-y']
    for i in range(len(input_files)):
        command.extend(['-i', input_files[i]])
    command.extend(['-filter_complex', filter_string, '-map', '[outv]', output_file])

    subprocess.run(command)

    print(f"Videos merged successfully. Output file: {output_file}")
    # Delete the original "resized_" video files
    for video_file in video_files:
        os.remove(video_file)

def add_yellow_captions(video_path, captions, audio_duration, output_path):
    try:
        # Load the video clip
        video_clip = VideoFileClip(video_path)

        # Calculate the duration for each caption based on the audio duration
        num_captions = len(captions.split()) 
        duration_per_caption = audio_duration / num_captions

        # Split the captions into words
        words = captions.split()

        # Create a list to hold the caption clips
        caption_clips = []

        # Iterate over the words and create captions
        for i in range(0, len(words), 3):
            # Get three words for the current caption
            caption_word = words[i:i+3]
            print(caption_word)
            print(i)
            i+=3
            caption_str = " ".join(caption_word)
            print(caption_str)

            # Create a TextClip with yellow color for the caption
            caption_clip = TextClip(caption_str, fontsize=44, color='yellow', font='Arial-Bold')

            # Set the duration for the caption clip
            caption_clip = caption_clip.set_duration(duration_per_caption*3)

            # Add the caption clip to the list
            caption_clips.append(caption_clip)

        # Concatenate all the caption clips together
        final_clip = concatenate_videoclips(caption_clips)

        # Set the duration of the final clip to match the video duration
        final_clip = final_clip.set_duration(video_clip.duration)

        # Overlay the captions on the video
        final_clip = final_clip.set_position(("center", "center"))

        # Composite the captioned clip with the original video
        final_clip = CompositeVideoClip([video_clip.set_opacity(0.7), final_clip])

        # Write the output video file with the captions
        final_clip.write_videofile(output_path, codec="libx264")

        os.remove(video_path)

        print(f"Yellow captions added to the video. Output video saved as {output_path}.")

    except IndexError:
        print("Captions are smaller than the video duration. Continuing with next steps.")
        video_clip.close()
        # Deleting the Audio video file
        os.remove(video_path)
        print("Audio video file deleted successfully.")
        # Deleting the temp Audio file
        os.remove("final_videoTEMP_MPY_wvf_snd.mp3")

# def add_yellow_captions(video_path, captions, audio_duration, output_path):
#     # Load the video clip
#     video_clip = VideoFileClip(video_path)

#     # Calculate the duration for each caption based on the audio duration
#     num_captions = len(captions.split()) 
#     duration_per_caption = audio_duration / num_captions

#     # Split the captions into words
#     words = captions.split()

#     # Create a list to hold the caption clips
#     caption_clips = []

#     # Iterate over the words and create captions
#     for i in range(0, len(words), 3):
#         # Get three words for the current caption
#         caption_word = words[i:i+3]
#         print(caption_word)
#         print(i)
#         i+=3
#         caption_str = " ".join(caption_word)
#         print(caption_str)
        

#         # Create a TextClip with yellow color for the caption
#         caption_clip = TextClip(caption_str, fontsize=44, color='yellow', font='Arial-Bold')

#         # Set the duration for the caption clip
#         caption_clip = caption_clip.set_duration(duration_per_caption*3)

#         # Add the caption clip to the list
#         caption_clips.append(caption_clip)

#     # Concatenate all the caption clips together
#     final_clip = concatenate_videoclips(caption_clips)

#     # Set the duration of the final clip to match the video duration
#     final_clip = final_clip.set_duration(video_clip.duration)

#     # Overlay the captions on the video
#     final_clip = final_clip.set_position(("center", "center"))

#     # Composite the captioned clip with the original video
#     final_clip = CompositeVideoClip([video_clip.set_opacity(0.7), final_clip])

#     # Write the output video file with the captions
#     final_clip.write_videofile(output_path, codec="libx264")

#     os.remove(video_path)

#     print(f"Yellow captions added to the video. Output video saved as {output_path}.")

def generate_mp3(text, output_filename):
    # Initialize the text-to-speech engine
    engine = pyttsx3.init()

    # Configure the audio settings
    engine.setProperty("voice", "en-us")  # Set the desired voice (optional)
    engine.setProperty("rate", 140)  # Set the desired speech rate (optional)

    # Generate the speech as a WAV file
    output_path_wav = output_filename + ".wav"
    engine.save_to_file(text, output_path_wav)
    engine.runAndWait()

    # Convert the WAV file to MP3
    output_path_mp3 = output_filename
    audio = AudioSegment.from_wav(output_path_wav)
    audio.export(output_path_mp3, format="mp3")

    # Remove the temporary WAV file
    os.remove(output_path_wav)

    print(f"MP3 file saved as: {output_path_mp3}")

# def generate_mp3(text, output_filename):
#     # Initialize the text-to-speech engine
#     engine = pyttsx3.init()

#     # Configure the audio settings
#     engine.setProperty("voice", "en-us")  # Set the desired voice (optional)

#     # Set the desired speech rate (optional)
#     engine.setProperty("rate", 140)  # Adjust the value as needed

#     # Get the current working directory
#     project_dir = os.getcwd()

#     # Construct the output file path in the project directory
#     output_path = os.path.join(project_dir, output_filename)

#     # Save the speech to the output path
#     engine.save_to_file(text, output_path)

#     # Run the text-to-speech conversion
#     engine.runAndWait()

def get_audio_duration(audio_path):
    # Load the audio clip
    audio_clip = AudioFileClip(audio_path)

    # Get the duration of the audio clip
    duration = audio_clip.duration

    # Close the audio clip
    audio_clip.close()

    return duration

def add_audio_to_video(video_path, audio_path, output_path):
    # Load the video clip
    video_clip = VideoFileClip(video_path)

    # Mute the video clip
    video_clip = video_clip.set_audio(None)

    # Load the audio clip
    audio_clip = AudioFileClip(audio_path)

    # Set the audio of the video clip to the loaded audio clip
    video_clip = video_clip.set_audio(audio_clip)

    # Generate the output video file
    video_clip.write_videofile(output_path, codec="libx264")

    # Delete the original video file
    os.remove(video_path)
    
    # Delete the original audio file
    os.remove(audio_path)

    print(f"Audio added to the video. Output video saved as {output_path}, and the original video and audio files has been deleted.")


def usage(user_question, keyword, suffix, per_page, output_folder, merged_video, audio_filename, audio_video, final_output_file):
    
    # Get the response from the API
    api_response = request_text_from_api(suffix, user_question)

    if api_response:
        print("API response:")
        print(api_response)

    # Download and crop videos
    print("Downloading videos...")
    cropped_videos = download_and_crop_videos(keyword, per_page, output_folder)
    print("Cropped video files:", cropped_videos)

    # Call the function to crop videos in the current directory
    crop_videos_in_directory(output_folder)

    # Call the function by providing the folder path and output file path
    merge_videos(output_folder, merged_video)

    # Generate the MP3 file
    print("Generating MP3 file...")
    generate_mp3(api_response, audio_filename)
    print("MP3 file generated successfully!")

    # Get the duration of the generated audio
    print("Getting the duration of the audio...")
    audio_duration = get_audio_duration(audio_filename)
    print(f"Audio duration: {audio_duration} seconds.")

    # Add the audio to the video
    print("Adding audio to the video...")
    add_audio_to_video(merged_video, audio_filename, audio_video)
    print("Audio added successfully.")

    # Add yellow captions to the video with the synchronized audio
    print("Adding yellow captions to the video...")
    add_yellow_captions(audio_video, api_response, audio_duration, final_output_file)
    print("Yellow captions added successfully.")



