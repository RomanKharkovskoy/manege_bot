import sqlite3
from datetime import datetime

DB_NAME = 'progress.db'

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            surname TEXT,
            current_round INTEGER,
            current_image INTEGER,
            hints_left INTEGER,
            completed_images TEXT,
            start_time TEXT,
            end_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, name, surname):
    start_time = datetime.now().isoformat()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_progress (user_id, name, surname, current_round, current_image, hints_left, completed_images, start_time)
        VALUES (?, ?, ?, 1, 1, 2, '', ?)
    ''', (user_id, name, surname, start_time))
    conn.commit()
    conn.close()

def update_user_progress(user_id, current_round=None, current_image=None, hints_left=None, completed_images=None, name=None, surname=None, end_time=None):
    user_progress = get_user_progress(user_id)
    
    current_round = current_round if current_round is not None else user_progress['current_round']
    current_image = current_image if current_image is not None else user_progress['current_image']
    hints_left = hints_left if hints_left is not None else user_progress['hints_left']
    completed_images = completed_images if completed_images is not None else user_progress['completed_images']
    name = name if name is not None else user_progress['name']
    surname = surname if surname is not None else user_progress['surname']
    end_time = end_time if end_time is not None else user_progress['end_time']

    completed_images_str = ','.join(map(str, completed_images))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        '''
        UPDATE user_progress
        SET current_round = ?, current_image = ?, hints_left = ?, completed_images = ?, name = ?, surname = ?, end_time = ?
        WHERE user_id = ?
        ''',
        (current_round, current_image, hints_left, completed_images_str, name, surname, end_time, user_id)
    )
    conn.commit()
    conn.close()

def get_user_progress(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_progress WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'user_id': row[0],
            'name': row[1],
            'surname': row[2],
            'current_round': row[3],
            'current_image': row[4],
            'hints_left': row[5],
            'completed_images': set(map(int, row[6].split(','))) if row[6] else set(),
            'start_time': row[7],
            'end_time': row[8]
        }
    return None

def user_exists(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM user_progress WHERE user_id = ?', (user_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists
