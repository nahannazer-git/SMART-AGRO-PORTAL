
import sqlite3
import os

def add_image_column():
    db_path = os.path.join('instance', 'farmers_portal.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE chat_messages ADD COLUMN image_path TEXT")
        conn.commit()
        print("Successfully added image_path column to chat_messages table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column image_path already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_image_column()
