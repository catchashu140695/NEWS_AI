import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import shutil
import uuid
import eel
import wx
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip
import yt_dlp as ytdl


def send_emails(subject, message, attachment_path):
    email_from="bennyunsigned@gmail.com"
    email_list=["bennyunsigned@gmail.com"]
    pswd="weksdijljmpuuvpd"
    for email_to in email_list:
        try:
            # Set up the email content
            msg = MIMEMultipart()
            msg['From'] = email_from
            msg['To'] = email_to
            msg['Subject'] = subject

            # Attach the message body (HTML format)
            msg.attach(MIMEText(message, 'html'))

            # Attach the file
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attachment_path.split('/')[-1]}",
                )
                msg.attach(part)

            # Send the email
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(email_from, "weksdijljmpuuvpd")
            text = msg.as_string()
            server.sendmail(email_from, email_to, text)
            server.quit()
            print(f"Email sent to {email_to}")
        except Exception as e:
            print(f"Failed to send email to {email_to}: {e}")
            
def copy_files(source_folder, destination_folder):
    # Ensure destination folder exists, create if not
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    # Get list of all files in the source folder
    for filename in os.listdir(source_folder):
        source_file = os.path.join(source_folder, filename)
        
        # Check if it's a file and copy it
        if os.path.isfile(source_file):
            shutil.copy(source_file, destination_folder)
            print(f"Copied: {filename}")
        else:
            print(f"Skipped (not a file): {filename}")
            
# Utility function to move files from one folder to another
def move_files(source_folder, destination_folder):
    # Ensure destination folder exists, create if not
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    # Get list of all files in the source folder
    for filename in os.listdir(source_folder):
        source_file = os.path.join(source_folder, filename)
        
        # Check if it's a file and move it
        if os.path.isfile(source_file):
            shutil.move(source_file, destination_folder)
            print(f"Moved: {filename}")
        else:
            print(f"Skipped (not a file): {filename}")
            
def rename_first_mp4(directory, new_name):
    # Ensure the new name has .mp4 extension
    if not new_name.endswith(".mp4"):
        new_name += ".mp4"

    # Get list of all files in the directory
    files = os.listdir(directory)
    
    # Find the first MP4 file in the directory
    for file in files:
        if file.endswith(".mp4"):
            old_file_path = os.path.join(directory, file)
            new_file_path = os.path.join(directory, new_name)
            
            # Rename the file
            os.rename(old_file_path, new_file_path)
            print(f"Renamed '{file}' to '{new_name}'")
            return new_file_path

    print("No MP4 file found in the directory.")
    return None

def break_into_sentences(text):
    """Break text into smaller sentences using '।' as delimiter."""
    return text.split("। ")


@eel.expose  # Expose this function to JavaScript
def select_and_save_video():
    app = wx.App(False)
    frame = wx.Frame(None, wx.ID_ANY, "File Selector")
    
    with wx.FileDialog(frame, "Select a video file", wildcard="Video files (*.mp4)|*.mp4",
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return None  # User canceled the dialog

        video_path = fileDialog.GetPath()
        save_directory = 'Web/Videos'
        os.makedirs(save_directory, exist_ok=True)
        saved_path = os.path.join(save_directory, os.path.basename(video_path))
        shutil.copy(video_path, saved_path)  # Copy the file to the Web/Videos directory
        return saved_path


@eel.expose
def trim_video(video_path, segments):    
    try:
        video_clip = VideoFileClip(video_path)
        trimmed_clips = []
        trimmed_clip_paths = []

        for i, segment in enumerate(segments):
            start_time = segment['start']
            end_time = segment['end']
            trimmed_clip = video_clip.subclip(start_time, end_time)

            # Create black strips
            width, height = trimmed_clip.size
            top_strip = ColorClip(size=(width, 180), color=(0, 0, 0), duration=trimmed_clip.duration)
            bottom_strip = ColorClip(size=(width, 180), color=(0, 0, 0), duration=trimmed_clip.duration)
            bottom_strip = bottom_strip.set_position(("center", height-180))  # Position at the bottom

            # Composite the video with the black strips
            final_clip = CompositeVideoClip([trimmed_clip, top_strip.set_position(("center", 0)), bottom_strip])
            trimmed_clips.append(final_clip)

            save_directory = 'web/TrimmedVideos'
            os.makedirs(save_directory, exist_ok=True)
            # Save the trimmed clip
            trimmed_clip_path = f"web/TrimmedVideos/trimmed_segment_{i}.mp4"
            final_clip.write_videofile(trimmed_clip_path, codec="libx264")

            # Add the path to the list of trimmed clip paths
            trimmed_clip_paths.append(trimmed_clip_path)

        # Return the list of download links for all trimmed segments
        return {"success": True, "download_links": trimmed_clip_paths}

    except Exception as e:
        return {"success": False, "error": str(e)}


@eel.expose
def get_available_formats(url):
    try:
        ydl_opts = {}
        with ytdl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            format_list = [{"format_id": fmt["format_id"], "resolution": fmt.get("resolution", "N/A"), "ext": fmt["ext"]} for fmt in formats]
            return format_list
    except Exception as e:
        return f"Error: {str(e)}"

@eel.expose
def download_video(url, format_id):
    try:
        # Generate a UUID for the file name
        unique_filename = str(uuid.uuid4())

        ydl_opts = {
            'format': f'{format_id}+bestaudio/best',  # Download video and best available audio
            'outtmpl': f'web/YTDownloads/{unique_filename}.%(ext)s',  # Save to 'YTDownloads' folder with UUID as filename
            'merge_output_format': 'mp4'  # Ensure the output file is in mp4 format
        }

        with ytdl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return "Video downloaded successfully!"
    except Exception as e:
        return f"Error: {str(e)}"


@eel.expose
def get_yt_downloaded_videos():
    download_path = 'web/YTDownloads'
    if not os.path.exists(download_path):
        return []

    return [f for f in os.listdir(download_path) if f.endswith(('.mp4', '.mkv', '.webm'))]