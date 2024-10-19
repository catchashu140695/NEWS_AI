import os
import shutil
import sqlite3
from gtts import gTTS
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip,concatenate_videoclips, ColorClip, ImageClip
from pydub import AudioSegment
from pydub.silence import split_on_silence
import glob
import logging
from moviepy.config import change_settings
import tempfile
import eel
import sys
# Get the parent directory (project root)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Utilities import util
from datetime import datetime
import re
from pydub import effects


# Configure logging
logging.basicConfig(level=logging.INFO)

change_settings({"IMAGEMAGICK_BINARY": "C:/Program Files/ImageMagick-7.1.1-Q16/magick.exe"})

# Set global paths
Project_Path = "./Web/LongNewsProjects"
DB_PATH = "NEWSAI_DB.db"

@eel.expose()
# Step 1: Start video processing by moving files from web folder to process folder
def start_long_video_process(project_id):
    print(f'Process Start for Project Id: {project_id}')
    
    # Move files from web folder to project root directory
    web_folder = os.path.join(Project_Path, project_id)
    base_folder = os.path.join("LongNewsProjects", project_id)
    process_root_folder = os.path.join("./LongNewsProjects/", project_id, "raw_videos")
    util.copy_files(web_folder, process_root_folder)
    audios_folder=os.path.join(base_folder,"Audios")
    
    # Use glob to find all .mp4 files in the folder
    mp4_files = glob.glob(os.path.join(process_root_folder, '*.mp4'))
    for file in mp4_files:
        # Get the filename without the extension
        filename_without_ext = os.path.splitext(os.path.basename(file))[0]   
        save_news_audio(filename_without_ext,audios_folder)
   
    for file in mp4_files:
        # Get the filename without the extension
        filename_without_ext = os.path.splitext(os.path.basename(file))[0]  
        talking_heads_folder=os.path.join(base_folder,"TalkingHeads")      
        audio_path=os.path.join(base_folder,"Audios",filename_without_ext + ".mp3")
        talking_head_output_path=os.path.join(talking_heads_folder,filename_without_ext)
        talking_head_image_path=os.path.join("Web","assets","images","vendor","Headlines.png")
        generate_talking_head(audio_path, talking_head_image_path, talking_head_output_path)
        util.rename_first_mp4(talking_head_output_path,filename_without_ext + ".mp4") 
              
        # Output path for the video with overlay news
        overlay_output_file_path = os.path.join(base_folder, "NewsOverlay", filename_without_ext)
        add_video_overlay(
            os.path.join(talking_head_output_path, filename_without_ext + ".mp4"),
            os.path.join(process_root_folder, filename_without_ext + ".mp4"),
            overlay_output_file_path
        )
    
    startVideoEditing(project_id)       
    return "success"

def save_news_audio(news_id, output_path, language='hi'):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT full_story FROM news_master WHERE Status=0 AND video_id=?", (news_id,))
            row = cursor.fetchone()
            if row is None:
                logging.warning(f"No entry found for NewsId: {news_id}")
                return
            
            text = row[0]

            # Clean text by removing multiple spaces
            text = re.sub(r'\s+', ' ', text.strip())

            sentences = util.break_into_sentences(text)

            # Create a temporary directory to store audio files
            temp_dir = tempfile.mkdtemp()
            logging.info(f"Temporary directory created at: {temp_dir}")

            # List to store filenames of individual sentence audio files
            audio_files = []

            # Loop through each sentence and generate TTS
            for idx, sentence in enumerate(sentences):
                sentence = sentence.strip()  # Strip extra spaces
                if sentence:  # Ensure sentence is not empty
                    sentence += "।"  # Adding '।' back after the split
                    tts = gTTS(text=sentence, lang=language, slow=False)
                    filename = os.path.join(temp_dir, f"sentence_{idx}.mp3")  # Save each sentence in the temp directory
                    tts.save(filename)
                    audio_files.append(filename)
                    logging.info(f"Saved {filename}")

            # Combine all sentence MP3 files into one
            combined_audio = AudioSegment.empty()
            for file in audio_files:
                audio = AudioSegment.from_mp3(file)

                # Remove unwanted silence between words
                audio = effects.strip_silence(audio, silence_thresh=-40, padding=100)

                # Increase the volume
                audio = audio + 6  # Increase by 6 dB

                # Maintain sound quality and speed up using resampling
                new_frame_rate = int(audio.frame_rate * 1.2)  # 20% faster
                audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_frame_rate})
                audio = audio.set_frame_rate(44100)  # Reset to a standard frame rate to maintain quality

                combined_audio += audio  # Concatenate without gaps

            # Create the output path if it doesn't exist
            os.makedirs(output_path, exist_ok=True)

            final_audio_path = os.path.join(output_path, f"{news_id}.mp3")
            combined_audio.export(final_audio_path, format="mp3")
            logging.info(f"Combined audio saved at: {final_audio_path}")

            # Clean up: delete the temporary directory
            shutil.rmtree(temp_dir)
            logging.info(f"Temporary directory {temp_dir} deleted.")

            return final_audio_path

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

# Step 3: Generate the talking head video using the processed audio
def generate_talking_head(audio_path, image_path, output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Example: Call an external script or system command to generate talking head
    # This could be a machine learning model that syncs lips to audio
    os.system(f"python .\SadTalker\inference.py --driven_audio {audio_path} --source_image {image_path} --result_dir {output_path} --still  --preprocess full")
    
    print(f"Talking head video generated in: {output_path}")

def add_video_overlay(background_video_path, overlay_video_path, output_path):
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    with VideoFileClip(background_video_path) as background_video:
        video_duration = background_video.duration

        # Load and resize the overlay video
        overlay_video = (VideoFileClip(overlay_video_path)
                         .set_duration(video_duration)
                         .resize(height=430)
                         .without_audio())
        
        # Loop the overlay video
        overlay_video = overlay_video.loop(duration=video_duration)
        overlay_video = overlay_video.set_pos((50, 'center'))

        # Combine background video and overlay
        final_video = CompositeVideoClip([background_video, overlay_video.set_start(0)])
        final_video.write_videofile(output_path + ".mp4", codec='libx264', fps=background_video.fps)
    
    print(f"Final video created at: {output_path}")

def startVideoEditing(project_id):
    web_folder = os.path.join(Project_Path, project_id)
    base_folder = os.path.join("LongNewsProjects", project_id)
    process_root_folder = os.path.join("./LongNewsProjects/", project_id, "raw_videos") 
    overlay_videos_folder = os.path.join(base_folder, "NewsOverlay")    
    transition_video_path = os.path.join("Web", "assets", "images", "vendor", "Transition.mp4")
    
    
    if not os.path.exists(transition_video_path):
        raise FileNotFoundError(f"Transition video not found at: {transition_video_path}")
    
    merged_overlay_video_path = os.path.join(base_folder, "NewsMerged")
    merge_videos_with_intro(transition_video_path, overlay_videos_folder, merged_overlay_video_path)
    add_grey_footer(os.path.join(base_folder, "NewsMerged.mp4"))
    headlines = fetch_concatenated_introductions(project_id)   
    headlines *= 100     
    add_scrolling_text_to_video(os.path.join(base_folder, "NewsMerged.mp4"),os.path.join(base_folder, "Final.mp4"),headlines)
    
    add_breaking_news_footer(os.path.join(base_folder, "Din_Bhar_ki_Badi_khabbar.mp4"))
    create_thumbnail('Web\\assets\\images\\vendor\\Headlines.png',os.path.join(base_folder,"thumnbail.png"))
    return "success"

def create_thumbnail(image_path, output_path):
    # Define the text to be added to the image
    current_date = datetime.now().strftime('%d-%b-%Y')
    main_text = "Aaj Ki\nBadi\nKhabbar"

    # Load the image
    image_clip = ImageClip(image_path)

    # Create the shadow text clip (slightly offset and darker color)
    shadow_clip = TextClip(
        main_text,
        fontsize=150,  # Font size for the main text
        font='Verdana-Bold',
        color='black',  # Shadow color
        align='West',
        stroke_color='black',
        stroke_width=15  # Increased stroke width for more boldness
    ).set_position((55, 55)).set_duration(10)  # Offset shadow position for effect

    # Create the main text clip with bolder white text
    main_text_clip = TextClip(
        main_text,
        fontsize=150,  # Adjust the font size as needed
        font='Verdana-Bold',
        color='white',
        align='West',
        stroke_color='red',  # Black stroke for better visibility
        stroke_width=8  # Increased stroke width for more boldness
    ).set_position((50, 50)).set_duration(10)  # Adjust position as needed

    # Create the date text clip with a different color
    date_clip = TextClip(
        current_date,
        fontsize=150,  # Same font size as the main text
        font='Verdana-Bold',
        color='yellow',  # Change to your preferred color for the date
        align='West',
        stroke_color='black',  # Black stroke to maintain visibility
        stroke_width=10
    ).set_position((50, 580)).set_duration(10)  # Position the date below the main text

    # Composite the image, shadow, main text, and date together
    final_clip = CompositeVideoClip([image_clip, shadow_clip, main_text_clip, date_clip])

    # Save the output to the specified path
    final_clip.save_frame(output_path)

def merge_videos_with_intro(intro_file_path, videos_folder_path, output_path):
    """
    Merges all videos in the folder with a specified intro video.
    
    Parameters:
    - intro_file_path: Path to the intro video file.
    - videos_folder_path: Path to the folder with video files.
    - output_path: Path to save the final output video.
    """
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    # Load the intro video and resize it
    intro_clip = VideoFileClip(intro_file_path).resize((1920, 1080))

    # Get all video files from the folder
    video_files = [os.path.join(videos_folder_path, f) for f in os.listdir(videos_folder_path) if f.endswith(('.mp4', '.avi', '.mov'))]

    # Load videos and combine with intro
    video_clips = []
    
    for video_path in video_files:
        # Load each video and resize it
        video = VideoFileClip(video_path).resize((1920, 1080))

        # Combine intro and video
        combined = concatenate_videoclips([intro_clip, video])
        video_clips.append(combined)

    # Concatenate all video clips
    final_clip = concatenate_videoclips(video_clips, method="compose")

    # Write the final output to a file
    final_clip.write_videofile(output_path + ".mp4", codec="libx264")

def add_grey_footer(video_path, footer_height=120, footer_color=(128, 128, 128)):
    # Ensure the video path exists
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return
    
    # Load the video
    with VideoFileClip(video_path) as video:
        video_duration = video.duration
        video_width, video_height = video.size

        # Create the grey footer using ColorClip
        footer = ColorClip(size=(video_width, footer_height), color=footer_color)
        footer = footer.set_duration(video_duration)
        footer = footer.set_pos(('center', video_height - footer_height))

        # Add the footer to the video
        final_video = CompositeVideoClip([video, footer])

        # Replace the original video with the modified video (overwrite)
        temp_output_path = video_path.replace('.mp4', '_temp.mp4')
        final_video.write_videofile(temp_output_path, codec='libx264', fps=video.fps)
    
    # Replace the original video with the new one
    os.replace(temp_output_path, video_path)
    print(f"Grey footer added and video saved at: {video_path}")
        
def add_breaking_news_footer(video_path, footer_height=120, footer_color=(196, 37, 37)):
    # Ensure the video path exists
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return
    
    # Load the video
    with VideoFileClip(video_path) as video:
        video_duration = video.duration
        video_width, video_height = video.size

        # Create the grey footer using ColorClip
        footer = ColorClip(size=(400, footer_height), color=footer_color)
        footer = footer.set_duration(video_duration)
        footer = footer.set_pos(('left', video_height - 120))
        
        text_clip = TextClip("Headlines", font="Verdana", fontsize=60, color="white")
        text_width, text_height = text_clip.size
        text_clip = text_clip.set_duration(video_duration)
        text_clip = text_clip.set_position((30,video_height - 100))
        
        logo = ImageClip("Web/assets/images/vendor/logo.png").set_duration(video.duration)       
        logo = logo.resize(height=100).set_position((100, video_width-100))
        

        # Add the footer to the video
        final_video = CompositeVideoClip([video, footer, text_clip, logo])

        # Replace the original video with the modified video (overwrite)
        temp_output_path = video_path.replace('.mp4', '_temp.mp4')
        final_video.write_videofile(temp_output_path, codec='libx264', fps=video.fps)
    
    # Replace the original video with the new one
    os.replace(temp_output_path, video_path)
    print(f"Grey footer added and video saved at: {video_path}")

def fetch_concatenated_introductions(project_id):
    # Step 1: Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Step 2: Fetch headlines from the database for the given project_id
    cursor.execute("SELECT headline FROM news_master WHERE project_id=?", (project_id,))
    headlines = cursor.fetchall()

    # Step 3: Check if there are headlines available
    if not headlines:
        return "No headlines found for this project."

    # Step 4: Concatenate all headlines into a single string, starting with a bullet '•' and separated by '•'
    concatenated_string = ' • ' + ' • '.join([headline[0] for headline in headlines])

    # Step 5: Add three blank spaces at the end
    concatenated_string += '   '
    print(concatenated_string)
    # Step 6: Return the concatenated string
    return concatenated_string

def add_scrolling_text_to_video(video_path, output_path, text, font="Verdana", fontsize=40, color="black", scroll_speed=100):
    # Load the video
    video = VideoFileClip(video_path)
    video_width, video_height = video.size

    # Create the scrolling text clip
    text_clip = TextClip(text, font=font, fontsize=fontsize, color=color)
    text_width, text_height = text_clip.size

    # Calculate the scroll duration based on the scroll speed and the width of the text
    scroll_duration = (video_width + text_width) / scroll_speed

    # Set the position of the text to scroll from right to left
    scrolling_text = text_clip.set_position(lambda t: (video_width - t * scroll_speed, video_height - fontsize - 50))

    # Loop the text for the entire video duration
    scrolling_text = scrolling_text.set_duration(scroll_duration).loop(duration=video.duration)

    # Composite the video with the scrolling text
    final_video = CompositeVideoClip([video, scrolling_text])

    # Write the final video with scrolling text
    final_video.write_videofile(output_path, codec="libx264", fps=video.fps)

def sendEmail(projectId):
    YoutubeTitle='Latest News - ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
    YoutubeDescription='''
    Stay informed with the latest updates on Politics. At UB News, we bring you the most accurate and up-to-date news from around the world, covering everything from relevant topics like politics, technology, entertainment etc..


        📢 SUBSCRIBE to UB News for daily news updates: [Insert subscription link]
        📱 Follow us on social media:
        - Facebook: facebook.com/UnsignedBenny
        - Twitter: twitter.com/UnsignedBenny
        - Instagram: instagram.com/UnsignedBenny
        #UBNews #LatestNews #BreakingNews #NewsUpdate 
    ''', 
    YoutubeTags="", 
    InstagramDescription="", 
    destFileName=""
    subject = 'Latest News - ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"""
    <html>
    <body>
    <b>Youtube Title: </b> {YoutubeTitle}<br><br>
    <b>Youtube Description: </b> {YoutubeDescription}<br><br>   
    </body>
    </html>
    """
    
    attachment_path = f"./LongNewsProjects/{project_id}/Final.mp4"   

    # Send email
    util.send_emails(subject, message, attachment_path)

if __name__ == "__main__":
    project_id = "6"
    start_long_video_process(project_id) 
    startVideoEditing(project_id)  
    #sendEmail(project_id)
     
      
    
    
    

