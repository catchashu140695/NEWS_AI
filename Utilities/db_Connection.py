import sqlite3
from sqlite3 import Error

class DatabaseConnection:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None

    def __enter__(self):
        try:
            self.conn = sqlite3.connect(self.db_file)
            print(f"Successfully Connected to SQLite Database '{self.db_file}'")
        except Error as e:
            print(f"Error connecting to database: {e}")
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
            print("Connection closed")

def get_db_connection():
    connection = sqlite3.connect('NEWSAI_DB.db')
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create project_master table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            description TEXT,
            created_on TEXT,
            yt_title TEXT,
            yt_description TEXT,
            yt_tags TEXT,
            insta_description TEXT,
            status INTEGER DEFAULT 0
        )
    ''')

    # Create your new table
    cursor.execute('''
       CREATE TABLE IF NOT EXISTS news_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            video_id TEXT,
            transcription TEXT,
            headline TEXT,
            introduction TEXT,
            full_story TEXT,
            yt_title TEXT,
            yt_description TEXT,
            yt_tags TEXT,
            insta_description TEXT,
            status INTEGER DEFAULT 0,
            UNIQUE(video_id, project_id)  -- Add unique constraint
        );
    ''')
    
    cursor.execute('''
       CREATE TABLE IF NOT EXISTS NewsArticle (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Title TEXT,
        Description TEXT,
        Url TEXT,
        UrlToImage TEXT,
        NewsId TEXT,
        YoutubeTitle TEXT,
        YoutubeDescription TEXT,
        YoutubeTags TEXT,
        InstagramDescription TEXT,
        Status INTEGER
    );
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()  # Initialize the database when running this file
