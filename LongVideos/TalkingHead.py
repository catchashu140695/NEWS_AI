import eel
import os
import uuid
from gtts import gTTS
import subprocess
import base64
import shutil
import wx


# Define the directories for storing files
TALKING_HEADS_FOLDER = './TalkingHeads'
VIDEO_OUTPUT_FOLDER = './Web/TalkingHeadProjects'

# Ensure that the directories exist
os.makedirs(TALKING_HEADS_FOLDER, exist_ok=True)
os.makedirs(VIDEO_OUTPUT_FOLDER, exist_ok=True)

@eel.expose
def generate_talking_head_from_text(text, image_data):
    try:
        image_path = save_image_file(image_data)
        audio_path = os.path.join(TALKING_HEADS_FOLDER, f"{uuid.uuid4()}_audio.wav")
        
        convert_text_to_audio(text, audio_path)
        eel.update_progress_bar(50)  # Update the progress bar to 50%
        
        start_sadtalker_process(image_path, audio_path)
        eel.update_progress_bar(100)  # Update the progress bar to 100%
        
        eel.refresh_video_library()  # Refresh the video library after generation
    except Exception as e:
        print(f"Error: {e}")
        eel.show_error_alert('Failed to generate Talking Head!')

@eel.expose
def generate_talking_head_from_audio(audio_data, image_data):
    try:
        image_path = image_data
        audio_path = audio_data
        
        eel.update_progress_bar(50)  # Update the progress bar to 50%
        start_sadtalker_process(image_path, audio_path)
        eel.update_progress_bar(100)  # Update the progress bar to 100%
        
        eel.refresh_video_library()  # Refresh the video library after generation
    except Exception as e:
        print(f"Error: {e}")
        eel.show_error_alert('Failed to generate Talking Head!')

def save_image_file(image_data):
    if isinstance(image_data, dict):
        image_data = image_data['image_data']  # Access the correct key in the dictionary
    image_data = image_data.split(',')[1]  # Remove the data URL prefix
    image_bytes = base64.b64decode(image_data)
    file_name = f"{uuid.uuid4()}.png"
    file_path = os.path.join(TALKING_HEADS_FOLDER, file_name)
    
    with open(file_path, 'wb') as image_file:
        image_file.write(image_bytes)
    return file_path

def save_audio_file(audio_data):
    if isinstance(audio_data, dict):
        audio_data = audio_data['audio_data']  # Access the correct key in the dictionary
    audio_file_path = os.path.join(TALKING_HEADS_FOLDER, f"{uuid.uuid4()}_audio.wav")
    with open(audio_file_path, 'wb') as audio_file:
        audio_file.write(audio_data)
    return audio_file_path

def convert_text_to_audio(text, audio_path):
    tts = gTTS(text=text, lang='en')
    tts.save(audio_path)

def start_sadtalker_process(image_path, audio_path):
    command = f"python SadTalker/inference.py --driven_audio {audio_path} --source_image {image_path} --result_dir {VIDEO_OUTPUT_FOLDER} --preprocess full"
    subprocess.run(command, shell=True)
    if os.path.exists("TalkingHeads"):
            shutil.rmtree("TalkingHeads")

def convert_video_to_mp4(input_file, output_file):
    try:
        # FFmpeg command to convert the video to the H.264 codec with AAC audio
        command = [
            'ffmpeg', '-i', input_file,
            '-c:v', 'libx264',  # H.264 video codec
            '-c:a', 'aac',      # AAC audio codec
            '-strict', 'experimental',
            '-movflags', '+faststart',
            output_file
        ]
        subprocess.run(command, check=True)
        print(f"Conversion successful: {output_file}")
        
        # Delete the original file after conversion
        os.remove(input_file)
        print(f"Deleted original file: {input_file}")
        
        return True
    except subprocess.CalledProcessError:
        print(f"Error converting file: {input_file}")
        return False
    except OSError as e:
        print(f"Error deleting file: {input_file} - {e}")
        return False

def get_all_video_paths():
    video_paths = []
    for root, dirs, files in os.walk(VIDEO_OUTPUT_FOLDER):
        for file in files:
            if file.endswith('.mp4'):
                input_file_path = os.path.join(root, file)
                uuid_filename = f"{uuid.uuid4()}.mp4"  # Generate a UUID filename with .mp4 extension
                converted_file_path = os.path.join(root, uuid_filename)

                # Convert the video if necessary and only add the properly formatted file
                if not os.path.exists(converted_file_path):
                    conversion_result = convert_video_to_mp4(input_file_path, converted_file_path)
                    if conversion_result:
                        video_paths.append(converted_file_path)  # Add converted file path
                    else:
                        video_paths.append(input_file_path)  # Add original if conversion fails
                else:
                    video_paths.append(converted_file_path)
    print("Video_paths:" + str(video_paths))
    return video_paths

@eel.expose
def refresh_video_library():
    video_paths = get_all_video_paths()
    return video_paths

@eel.expose
def copy_file(path):
    # Ensure the path is a string before proceeding
    if isinstance(path, list):
        path = path[0]  # Use the first file in the list for simplicity

    destination_folder = os.path.join("Web", "TalkingHeadProjects")
    
    # Ensure the destination directory exists
    os.makedirs(destination_folder, exist_ok=True)

    # Generate a UUID for the new file name
    video_uuid = str(uuid.uuid4())
    
    # Define the new destination file name using the UUID
    file_extension = os.path.splitext(path)[1]  # Get file extension (e.g., .mp4)
    new_file_name = video_uuid + file_extension
    
    # Define the full destination path for the file
    destination_path = os.path.join(destination_folder, new_file_name)

    try:
        # Copy the file to the destination path with the new UUID-based name
        shutil.copy(path, destination_path)
        print(f"Copied {path} to {destination_path}")
        
        return destination_path  # Return the destination path
    
    except FileNotFoundError:
        print(f"File not found: {path}")
        return None
    except PermissionError:
        print(f"Permission denied: {path}")
        return None
    except Exception as e:
        print(f"Error copying {path}: {e}")
        return None

    
@eel.expose
def pythonFunction1(wildcard="*.mp3;*.wav"):
    app = wx.App(None)
    style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE
    dialog = wx.FileDialog(None, 'Open Audio Files', wildcard=wildcard, style=style)

    if dialog.ShowModal() == wx.ID_OK:
        paths = dialog.GetPaths()
    else:
        paths = []

    dialog.Destroy()
    return paths

@eel.expose
def pythonFunction2(wildcard="*.jpg;*.png;*.jpeg"):
    app = wx.App(None)
    style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE
    dialog = wx.FileDialog(None, 'Open Audio Files', wildcard=wildcard, style=style)

    if dialog.ShowModal() == wx.ID_OK:
        paths = dialog.GetPaths()
    else:
        paths = []

    dialog.Destroy()
    return paths


