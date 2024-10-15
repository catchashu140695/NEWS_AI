import os
import tempfile
import moviepy.editor as mp  # for video processing
import speech_recognition as sr  # for speech recognition
import eel  # for exposing the function to the frontend
from g4f.client import Client
import asyncio
from gtts import gTTS
import threading
import pygame
import time
from Utilities.db_Connection import *
import shutil
from pydub import AudioSegment
import re



# Set appropriate event loop policy for Windows
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
current_thread = None
pygame.mixer.init()


@eel.expose()
def transcribe_video(project_id, file_id, language='hi-IN'):
    # Fixing file path (remove the extra dot before the .mp4)
    video_path = os.path.join("Web", "LongNewsProjects", project_id, file_id + ".mp4")
    
    # Ensure the path is correct
    print(f"Video path: {video_path}")
    
    # Check if the file exists before proceeding
    if not os.path.exists(video_path):
        print(f"Error: The video file '{video_path}' does not exist!")
        return f"Error: The video file '{video_path}' does not exist!"
    
    try:
        # Create a temporary directory for audio chunks
        temp_dir = tempfile.mkdtemp()

        # Load the video file and extract audio
        video = mp.VideoFileClip(video_path)
        
        # Extract audio and save it as a .wav file
        full_audio_path = os.path.join(temp_dir, "full_audio.wav")
        video.audio.write_audiofile(full_audio_path)

        # Initialize the recognizer
        recognizer = sr.Recognizer()
        
        # Split audio into chunks (you can modify chunk size in seconds)
        chunk_length = 20  # Length of each audio chunk in seconds
        audio = AudioSegment.from_wav(full_audio_path)
        duration_ms = len(audio)  # Get audio duration in milliseconds
        
        transcriptions = []

        for i, start_time in enumerate(range(0, duration_ms, chunk_length * 1000)):
            # Get the chunk from the full audio
            chunk = audio[start_time:start_time + chunk_length * 1000]

            # Save the chunk as a temporary .wav file
            chunk_path = os.path.join(temp_dir, f"chunk_{i}.wav")
            chunk.export(chunk_path, format="wav")
            print(f"Processing chunk {i}: {chunk_path}")
            
            # Transcribe the chunk
            with sr.AudioFile(chunk_path) as source:
                audio_chunk = recognizer.record(source)
            
            try:
                chunk_text = recognizer.recognize_google(audio_chunk, language=language)
                print(f"Chunk {i} transcription: {chunk_text}")
                transcriptions.append(chunk_text)
            except sr.UnknownValueError:
                print(f"Google Speech Recognition could not understand chunk {i}")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service for chunk {i}; {e}")

        # Concatenate all the transcriptions
        final_transcription = " ".join(transcriptions).replace("*", "")
        print("Final Transcription: " + final_transcription)
        return final_transcription
    except Exception as e:
        print(f"Error processing video/audio: {e}")
    finally:
        # Clean up temporary files
        shutil.rmtree(temp_dir)

@eel.expose()
def get_chat_response(prompt):
    # Define patterns to check in the response
    patterns_to_retry = [
        "I'm sorry, but I can't provide",
        "How can I assist you ?",
        "I am not able to assist with that request",
        "I'm here to assist you with your inquiries",  # Pattern 1
        "One message exceeds the 1000chars per message limit",  # Pattern 2
        "One message exceeds the 1000 characters per message limit",  # Pattern 3
        "I'm sorry, I cannot assist with that request. If you have any other questions or need help, feel free to ask!"  # Pattern 4
    ]  

    def custom_similarity(pattern, response_text):
        # Tokenize both strings into lowercase words
        pattern_words = pattern.lower().split()
        response_words = response_text.lower().split()
        
        # Calculate number of matching words
        matching_words = len(set(pattern_words).intersection(response_words))
        
        # Calculate a similarity score as a percentage of matching words
        similarity_score = matching_words / len(pattern_words) * 100
        
        return similarity_score

    def should_retry(response_text):
        # Check if response is blank or exceeds 1000 characters
        if not response_text.strip() or len(response_text) > 1000:
            return True
        
        # Check for custom similarity with a threshold of 70% match
        similarity_threshold = 70
        for pattern in patterns_to_retry:
            similarity_score = custom_similarity(pattern, response_text)
            if similarity_score >= similarity_threshold:
                print(f"Pattern matched with similarity score: {similarity_score}%")
                return True
        
        return False

    while True:
        try:
            # Create a new session for each request
            client = Client()

            # Request completion
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract and clean the response
            chat_response = response.choices[0].message.content
            clean_response = chat_response.replace('"', '').replace('*', '').replace("_{code:200,status:true,model:gpt-3.5-turbo,gpt:", "").replace(",original:null}", "").replace("\n", "").replace("\\n\\n", "").replace("\n\n", "")
            
            # Check if we should retry (for blank responses, length, or pattern matches)
            if should_retry(clean_response):
                print("Retrying due to invalid response (blank, too long, or pattern matched)...")
            else:
                print("GPT Response:", clean_response)
                return clean_response

        except Exception as e:
            print(f"Error occurred in chat response: {e}")
            return None

    
    
current_thread = None
@eel.expose
def play_text(text):
    global current_thread

    sound_file = "temp_audio.mp3"

    # Stop the previous sound if any
    if current_thread and current_thread.is_alive():
        pygame.mixer.music.stop()
        current_thread.do_run = False
        current_thread.join()

    # Remove the old sound file if it exists to avoid overwriting issues
    if os.path.exists(sound_file):
        os.remove(sound_file)

    # Convert text to speech and save it
    tts = gTTS(text=text, lang='en')
    tts.save(sound_file)

    def run_sound():
        t = threading.currentThread()
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()

            # Wait for the sound to finish playing
            while pygame.mixer.music.get_busy() and getattr(t, "do_run", True):
                time.sleep(0.1)

        except Exception as e:
            print(f"Error playing sound: {e}")

        finally:
            # Ensure the sound file is not in use before deleting
            pygame.mixer.music.unload()

            # Clean up the audio file after playing
            if os.path.exists(sound_file):
                os.remove(sound_file)

    # Start a new thread for playing sound
    current_thread = threading.Thread(target=run_sound)
    current_thread.do_run = True
    current_thread.start()
    
@eel.expose
def save_video_details(details):    
    # Connect to the SQLite database
    conn = get_db_connection()  # Replace 'your_database.db' with the actual database name
    cursor = conn.cursor()

    try:
        # Prepare the SQL statement to update data
        query = '''
        UPDATE news_master
        SET 
            transcription = ?, 
            headline = ?, 
            introduction = ?, 
            full_story = ?, 
            yt_title = ?, 
            yt_description = ?, 
            yt_tags = ?, 
            insta_description = ?, 
            status = ?
        WHERE 
            project_id = ? AND 
            video_id = ?
        '''

        # Execute the SQL query
        cursor.execute(query, (
            details['transcription'],
            details['headline'],
            details['introduction'],
            details['full_story'],
            details['yt_title'],
            details['yt_description'],
            details['yt_tags'],
            details['insta_description'],
            details['status'],
            details['project_id'],
            details['video_id']
        ))

        # Check if any row was updated
        if cursor.rowcount == 0:
            return 'no_update'  # No matching record found for the update

        # Commit the transaction and close the connection
        conn.commit()
        return 'success'

    except Exception as e:
        print(f"Error saving video details: {e}")
        return 'error'

    finally:
        conn.close()
        
@eel.expose
def fetch_video_details(video_id, project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, project_id, video_id, transcription, headline, introduction, full_story, yt_title, yt_description, yt_tags, insta_description, status FROM news_master WHERE video_id=? and project_id=?", (video_id, project_id,))
    row = cursor.fetchone()  # Fetch one row

    conn.close()

    if row:
        # Convert result into a dictionary
        result = {
            "id": row[0],
            "project_id": row[1],
            "video_id": row[2],
            "transcription": row[3],
            "headline": row[4],
            "introduction": row[5],
            "full_story": row[6],
            "yt_title": row[7],
            "yt_description": row[8],
            "yt_tags": row[9],
            "insta_description": row[10],
            "status": row[11]
        }
        return result
    return None  # Return None if no row is found
