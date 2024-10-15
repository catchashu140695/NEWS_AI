import eel
from gtts import gTTS
import os
import json
from newsapi import NewsApiClient
from datetime import datetime, timedelta
import time
import uuid
import shutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from scipy.io.wavfile import write as write_wav
import requests
from moviepy.editor import *
from Utilities.db_Connection import DatabaseConnection
import random
from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_silence
from bs4 import BeautifulSoup
from g4f.client import Client


@eel.expose("get_website_content")
def get_website_content(url):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the text from the website content
        content = soup.get_text()

        return content

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"

@eel.expose
def fetch_news(topic="bollywood"):
    newsapi = NewsApiClient(api_key="43cd03efd7434c8faddab5e95dbb60d8")    
    categories = [topic] if isinstance(topic, str) else topic
    yesterday_date = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday_date.strftime('%Y-%m-%d')
    articles_list = []

    for category in categories:
        try:
            articles_response = newsapi.get_everything(
                q=category,
                from_param=yesterday_str,
                to=yesterday_str,
                language='en',
                sort_by='relevancy',
            )
            articles = articles_response.get('articles', [])
            for article in articles:
                articles_list.append({
                    "source_name": article['source']['name'],
                    "author": article.get('author', None),
                    "title": article['title'],
                    "description": article.get('description', None),
                    "url": article['url'],
                    "url_to_image": article.get('urlToImage', None),
                    "published_at": article['publishedAt'],
                    "content": article.get('content', None),
                    "category": category
                })
        except Exception as e:
            print(f"Error fetching articles for category {category}: {e}")
            continue    
    print(articles_list)
    return articles_list

@eel.expose("add_news_to_db")
def add_news_to_db(title, description, url, urlToImage, youtubeTitle, youtubeDescription, youtubeTags, instagramDescription):
   
    
    database = "NEWSAI_DB.db"
    with DatabaseConnection(database) as conn:
        if conn is not None:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO NewsArticle (
                    Title, Description, Url, UrlToImage, NewsId,YoutubeTitle, YoutubeDescription, YoutubeTags, InstagramDescription, Status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    title,description,url,str(urlToImage),str(uuid.uuid1()),youtubeTitle,youtubeDescription,youtubeTags,instagramDescription,0
                ))
                conn.commit()
                return "Success"
            except Exception as e:
                print(f"Error inserting article into database: {e}")
                return "Failed"

@eel.expose("get_added_news")
def get_added_news():
    database = "NEWSAI_DB.db"
    with DatabaseConnection(database) as conn:
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("SELECT NewsId, Title, Description, UrlToImage FROM NewsArticle where Status=0")
            rows = cursor.fetchall()
            news_articles = [{"NewsId": row[0], "title": row[1], "description": row[2], "url_to_image": row[3]} for row in rows]
            return news_articles
    return []

@eel.expose("delete_news_from_db")
def delete_news_from_db(news_id):
    database = "NEWSAI_DB.db"
    with DatabaseConnection(database) as conn:
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("update NewsArticle set Status=1 WHERE NewsId = ?", (news_id,))
            conn.commit()
            return "Success"
    return "Failed"




@eel.expose("startProcess")
def startProcess():
    while True:
        save_news_audio()
        generate_talking_head()   
        ready_to_upload()


def generate_random_number(min_value, max_value):    
    if min_value > max_value:
        raise ValueError("min_value should be less than or equal to max_value")    
    return random.randint(min_value, max_value)

def save_news_audio():   
    database = "NEWSAI_DB.db"
    audio_directory = "SadTalker/examples/driven_audio/"
    
    # Create the directory if it does not exist
    os.makedirs(audio_directory, exist_ok=True)
    
    with DatabaseConnection(database) as conn:
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("SELECT NewsId, Title, Description, UrlToImage FROM NewsArticle WHERE Status=0 LIMIT 1")
            row = cursor.fetchone()
            if row is not None:
                news_article = {
                    "NewsId": row[0],
                    "title": row[1],
                    "description": row[2],
                    "url_to_image": row[3]
                }
                language = 'hi' 
                tld = 'com'
                tts = gTTS(text=row[2], lang=language, slow=False)  
                path = os.path.join(audio_directory, f"{row[0]}.wav")
                tts.save(path)    
                print(f"Audio file saved as {path}")
                
                
                
                tts = gTTS(text=row[2], lang=language, slow=False)  
                temp_path = os.path.join(audio_directory, "temp.wav")
                tts.save(temp_path)

                # Load the generated speech
                audio = AudioSegment.from_file(temp_path)
                
                # Increase the playback speed
                speed = 1.12  # Speed factor (1.5 means 50% faster)
                faster_audio = audio.speedup(playback_speed=speed)
                
                # Trim silence at the end of sentences
                chunks = split_on_silence(faster_audio, min_silence_len=200, silence_thresh=-40)
                trimmed_audio = AudioSegment.empty()
                for chunk in chunks:
                    trimmed_audio += chunk + AudioSegment.silent(duration=50)  # Add short silence between chunks

                # Save the trimmed and faster audio
                final_path = os.path.join(audio_directory, f"{row[0]}.wav")
                trimmed_audio.export(final_path, format="wav")

                # Remove the temporary file
                os.remove(temp_path)                
                print(f"Audio file saved as {final_path}")
                delete_news_from_db(row[0])           
    return []


def generate_talking_head():      
    driven_audio_folder = "SadTalker/examples/driven_audio/"
    audio_files = os.listdir(driven_audio_folder)
    for audio_file in audio_files:   
        if audio_file.endswith(".wav"):
            outputpath = "SadTalker/results/" + audio_file.replace(".wav","") + "/"        
            if not os.path.exists(outputpath):    
                os.makedirs(outputpath)            
            audio_path = os.path.join(driven_audio_folder, audio_file)   
            random_number = generate_random_number(1, 13)        
            img = 'SadTalker/examples/source_image/'+ str(random_number) + '.png'             
            os.system(f"python SadTalker/inference.py --driven_audio {audio_path} \
                        --source_image {img} \
                        --result_dir {outputpath} \
                        --still \
                        --preprocess full \
                        ")
            # os.system(f"python inference.py --driven_audio {audio_path} \
            #             --source_image {img} \
            #             --result_dir {outputpath} \
            #             --still \
            #             --preprocess full \
            #             --enhancer gfpgan ")
            

def ready_to_upload():
    baseDir = "SadTalker/results/"
    destFileName=""
    # Loop through all folders inside base directory
    for folder in os.listdir(baseDir):
        folderPath = os.path.join(baseDir, folder)
        if os.path.isdir(folderPath):
            # Loop through files inside current folder
            for file in os.listdir(folderPath):
                filePath = os.path.join(folderPath, file)
                if os.path.isfile(filePath) and file.endswith(".mp4"):
                    # Move the .mp4 file to the finalresult folder
                    destFolder = "SadTalker/ready_to_upload/"
                    if not os.path.exists(destFolder):
                        os.makedirs(destFolder)
                    destFileName = folder + ".mp4"
                    shutil.move(filePath, os.path.join(destFolder, destFileName))
                    add_Image_overlay()
                    
            # Delete the folder after moving the mp4 files
            shutil.rmtree(folderPath)
            print(f"Deleted folder: {folderPath}") 
            
    try:      
        database = "NEWSAI_DB.db"
        with DatabaseConnection(database) as conn:
            if conn is not None:
                cursor = conn.cursor()            
                sql_query = """
                SELECT YoutubeTitle, YoutubeDescription, YoutubeTags, InstagramDescription
                FROM NewsArticle WHERE NewsId=?
                """
                
                cursor.execute(sql_query, (destFileName.replace(".mp4",""),))  # Using parameterized query
                row = cursor.fetchone()
                
                if row:
                    YoutubeTitle, YoutubeDescription, YoutubeTags, InstagramDescription = row
                    subject = YoutubeTitle
                    message = f"<html>" \
                        f"<body>" \
                        f"<b>Youtube Title: </b> {YoutubeTitle}<br><br>" \
                        f"<b>Youtube Description: </b> {YoutubeDescription}<br><br>" \
                        f"<b>Youtube Tags: </b> {YoutubeTags}<br><br>" \
                        f"<b>Instagram Description: </b> {InstagramDescription}<br><br>" \
                        f"</body>" \
                        f"</html>"

                    attachment_path = "SadTalker/ready_to_upload/"+ destFileName.replace(".mp4","")+"_final.mp4"

                    # Set up email details
                    email_from = "bennyunsigned@gmail.com"
                    email_list = ["bennyunsigned@gmail.com"]
                    pswd = "weksdijljmpuuvpd"

                    # Send email
                    send_emails(email_from, email_list, pswd, subject, message, attachment_path)                     
                            
                    shutil.rmtree("SadTalker/ready_to_upload/")            
                else:
                    print("No records found for the given NewsId.")

    except Exception as e:
        print("Error occurred:", str(e))       
    
    shutil.rmtree("SadTalker/examples/driven_audio/")
    createAudioFoler="SadTalker/examples/driven_audio/"    
    os.makedirs(createAudioFoler)
            

def send_emails(email_from, email_list, pswd, subject, content, attachmentPath):
    smtp_port = 587                 # Standard secure SMTP port
    smtp_server = "smtp.gmail.com"  # Google SMTP Server

    # Set up the email content
    body = content
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['Subject'] = subject

    # Attach text content
    msg.attach(MIMEText(body, 'html'))

    # Attach file
    with open(attachmentPath, 'rb') as attachment:
        attachment_package = MIMEBase('application', 'octet-stream')
        attachment_package.set_payload(attachment.read())
    encoders.encode_base64(attachment_package)
    attachment_package.add_header('Content-Disposition', f"attachment; filename= {attachmentPath}")
    msg.attach(attachment_package)

    text = msg.as_string()

    # Connect with the server
    print("Connecting to server...")
    TIE_server = smtplib.SMTP(smtp_server, smtp_port)
    TIE_server.starttls()
    TIE_server.login(email_from, pswd)
    print("Successfully connected to server")
    print()

    for person in email_list:
        email_sent = False
        while not email_sent:
            try:
                # Set up recipient
                msg['To'] = person

                # Send email to "person"
                print(f"Sending email to: {person}...")
                TIE_server.sendmail(email_from, person, text)
                print(f"Email sent to: {person}")
                email_sent = True  # Mark as sent if no exception occurs
            except Exception as e:
                print(f"Error sending email to {person}: {e}")
                print("Retrying in 5 seconds...")
                time.sleep(5)  # Wait for a short period before retrying

    # Close the connection
    TIE_server.quit()
 
def add_Image_overlay():
    database = "NEWSAI_DB.db"
    driven_video_folder = "SadTalker/ready_to_upload/"
    video_files = os.listdir(driven_video_folder)
    for video_file in video_files:
        if video_file.endswith(".mp4"):
            filename = video_file.replace(".mp4", "")
            
    with DatabaseConnection(database) as conn:
        if conn is not None:
            cursor = conn.cursor()            
            sql_query = """
            SELECT UrlToImage
            FROM NewsArticle WHERE NewsId=? 
            """
            try:
                # Attempt to convert filename to a uniqueidentifier
                cursor.execute(sql_query, (filename,))
                row = cursor.fetchone()
                
                if row:
                    UrlToImage = row[0]
                    print(UrlToImage)
                    ImageFile= "SadTalker/ready_to_upload/" + filename +".jpg" 
                    response = requests.get(UrlToImage)                   
                    if response.status_code == 200:
                        # Open the file in binary write mode and write the image content
                        with open(ImageFile, "wb") as file:
                            file.write(response.content)
                            
                        video_url = "SadTalker/ready_to_upload/" + filename + ".mp4"
                        image_url = "SadTalker/ready_to_upload/" + filename + ".jpg"

                        # Load the main video
                        video = VideoFileClip(video_url)
                        main_video_duration = video.duration

                        # Load the image and set its duration to match the video
                        title = ImageClip(image_url).set_duration(main_video_duration).set_pos(("center", 800)).resize(height=550)

                        # Composite the image onto the video
                        final = CompositeVideoClip([video, title.set_start(0)])

                        # Write the final video to the output file
                        output_url = "SadTalker/ready_to_upload/" + filename + "_final.mp4"
                        final.write_videofile(output_url, codec='libx264', fps=video.fps)
                    else:
                        print("Failed to download image")
                else:
                    print("No image URL found for", filename)
            except Exception as e:
                print("SQL Error:", e)   
