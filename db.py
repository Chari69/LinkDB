import sqlite3
import os

DB_PATH = "bookmarks.db"

def init_db():
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'w').close()
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT,
            folder_id INTEGER,
            color TEXT,
            tags TEXT,
            FOREIGN KEY(folder_id) REFERENCES folders(id)
        )
    ''')
    conn.commit()
    conn.close()

def migrate_add_color_and_tags_column():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA table_info(bookmarks)")
    columns = [row[1] for row in c.fetchall()]
    if "color" not in columns:
        c.execute("ALTER TABLE bookmarks ADD COLUMN color TEXT")
        conn.commit()
    if "tags" not in columns:
        c.execute("ALTER TABLE bookmarks ADD COLUMN tags TEXT")
        conn.commit()
    conn.close()

def get_folders_and_bookmarks():
    migrate_add_color_and_tags_column()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name FROM folders ORDER BY name")
    folders = c.fetchall()
    c.execute("SELECT id, url, title, folder_id, color, tags FROM bookmarks ORDER BY id DESC")
    bookmarks = c.fetchall()
    conn.close()
    return folders, bookmarks

def add_bookmark(url, folder_id=None, title=None, color=None, tags=None):
    if title is None:
        from utils import fetch_title
        title = fetch_title(url)
    if color is None:
        colors = ["red", "green", "yellow", "blue", "magenta", "cyan", "white"]
        import random
        color = random.choice(colors)
    if tags is None:
        tags = ""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO bookmarks (url, title, folder_id, color, tags) VALUES (?, ?, ?, ?, ?)", (url, title, folder_id, color, tags))
    conn.commit()
    conn.close()

def update_bookmark(url, title, color, tags):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE bookmarks SET title = ?, color = ?, tags = ? WHERE url = ?", (title, color, tags, url))
    conn.commit()
    conn.close()

def delete_bookmark(url):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM bookmarks WHERE url = ?", (url,))
    conn.commit()
    conn.close()

def reset_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
