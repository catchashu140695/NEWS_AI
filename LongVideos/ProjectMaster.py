import eel
from Utilities.db_Connection import *
from datetime import datetime
import os
import uuid
import requests
import shutil
import wx

@eel.expose("add_project")
def add_project(project_name, description):
    print("Add Project begins")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO project_master (project_name, description, created_on) VALUES (?, ?, ?)',
        (project_name, description, datetime.now())
    )
    conn.commit()
    conn.close()
    return "Project Added"

@eel.expose
def get_projects():
    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL query to format the created_on date as dd-MMM-yyyy
    cursor.execute('''
        SELECT id,
               project_name,
               description,
               strftime('%d-', created_on) || 
               CASE strftime('%m', created_on)
                    WHEN '01' THEN 'Jan'
                    WHEN '02' THEN 'Feb'
                    WHEN '03' THEN 'Mar'
                    WHEN '04' THEN 'Apr'
                    WHEN '05' THEN 'May'
                    WHEN '06' THEN 'Jun'
                    WHEN '07' THEN 'Jul'
                    WHEN '08' THEN 'Aug'
                    WHEN '09' THEN 'Sep'
                    WHEN '10' THEN 'Oct'
                    WHEN '11' THEN 'Nov'
                    WHEN '12' THEN 'Dec'
               END || '-' || strftime('%Y', created_on) AS created_on
        FROM project_master order by Id desc
    ''')

    # Fetch all the results
    projects = cursor.fetchall()
    conn.close()

    # Convert the SQLite Row objects to a list of dictionaries
    project_list = [dict(row) for row in projects]
    return project_list


@eel.expose
def delete_project(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM project_master WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return "Project Deleted"

@eel.expose
def update_project(id, project_name, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE project_master SET project_name = ?, description = ?, created_on = ?,  WHERE id = ?',
        (project_name, description, datetime.now(), id)
    )
    conn.commit()
    conn.close()
    return "Project Updated"


@eel.expose
def pythonFunction(wildcard="*.mp4"):
    app = wx.App(None)
    style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE
    dialog = wx.FileDialog(None, 'Open', wildcard=wildcard, style=style)
    
    if dialog.ShowModal() == wx.ID_OK:
        paths = dialog.GetPaths()
    else:
        paths = []
    
    dialog.Destroy()
    return paths





@eel.expose
def saveProjectVideos(ProjectId, FilePaths):
    # Define the destination path based on ProjectId
    destination_folder = os.path.join("Web", "LongNewsProjects", str(ProjectId))
    
    # Ensure the destination directory exists
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    # Connect to the SQLite database
    conn = get_db_connection()  
    cursor = conn.cursor()

    for path in FilePaths:
        print(f"Copying file from: {path}")
        
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
            
            # Insert the details into the news_master table
            cursor.execute("""
                INSERT INTO news_master (project_id, video_id, headline, introduction, full_story, yt_title, yt_description, yt_tags, insta_description, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ProjectId, video_uuid, '', '', '', '', '', '', '', '0'))  # Modify the fields as necessary
            
            # Commit the changes to the database
            conn.commit()
        
        except FileNotFoundError:
            print(f"File not found: {path}")
        except PermissionError:
            print(f"Permission denied: {path}")
        except Exception as e:
            print(f"Error copying {path}: {e}")
    
    # Close the database connection
    conn.close()


@eel.expose
def list_videos(ProjectId):
    print("Fetching Starts")
    print(ProjectId)
    
    # Convert ProjectId to string
    ProjectId_str = str(ProjectId)
    
    # Construct project path
    Project_Path = os.path.join("Web", "LongNewsProjects", ProjectId_str)
    print(Project_Path)
    
    # List all video files in the project path
    videos = [f for f in os.listdir(Project_Path) if f.endswith('.mp4')]
    
    # Join the videos list into a single string separated by '~'
    videos_str = '~'.join(videos)
    
    # Return project path and videos string separated by '|'
    print(videos_str)
    return f"{Project_Path}|{videos_str}"

