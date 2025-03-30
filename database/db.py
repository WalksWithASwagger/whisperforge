import os
import sqlite3
import logging
from pathlib import Path
import json

# Import from config
from config import DATABASE_PATH, logger

def get_db_connection():
    """
    Create and return a SQLite database connection with row factory.
    
    Returns:
        sqlite3.Connection: An active SQLite connection
    """
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize the database by creating necessary tables if they don't exist.
    """
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            api_keys TEXT,
            usage_quota INTEGER DEFAULT 60,  -- Minutes per month
            usage_current INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            subscription_tier TEXT DEFAULT 'free'
        )
    ''')
    conn.commit()
    conn.close()

def get_user_by_id(user_id):
    """
    Fetch a user by their ID.
    
    Args:
        user_id (int): The user's ID
        
    Returns:
        dict: The user's data as a dictionary, or None if not found
    """
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", 
        (user_id,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_email(email):
    """
    Fetch a user by their email address.
    
    Args:
        email (str): The user's email
        
    Returns:
        dict: The user's data as a dictionary, or None if not found
    """
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", 
        (email,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(email, password_hash, is_admin=0):
    """
    Create a new user.
    
    Args:
        email (str): The user's email
        password_hash (str): The hashed password
        is_admin (int): 1 if the user is an admin, 0 otherwise
        
    Returns:
        int: The user ID of the created user
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password, is_admin) VALUES (?, ?, ?)",
            (email, password_hash, is_admin)
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        # User already exists
        return None
    finally:
        conn.close()

def update_user_api_keys(user_id, api_keys_dict):
    """
    Update the API keys for a user.
    
    Args:
        user_id (int): The user's ID
        api_keys_dict (dict): Dictionary of API keys
        
    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE users SET api_keys = ? WHERE id = ?",
            (json.dumps(api_keys_dict), user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating API keys: {str(e)}")
        return False
    finally:
        conn.close()

def get_user_api_keys(user_id):
    """
    Get the API keys for a user.
    
    Args:
        user_id (int): The user's ID
        
    Returns:
        dict: Dictionary of API keys
    """
    conn = get_db_connection()
    user = conn.execute(
        "SELECT api_keys FROM users WHERE id = ?", 
        (user_id,)
    ).fetchone()
    conn.close()
    
    if user and user['api_keys']:
        try:
            return json.loads(user['api_keys'])
        except:
            return {}
    return {}

def update_usage(user_id, minutes_used):
    """
    Update the usage statistics for a user.
    
    Args:
        user_id (int): The user's ID
        minutes_used (float): Minutes of processing used
        
    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE users SET usage_current = usage_current + ? WHERE id = ?",
            (minutes_used, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating usage: {str(e)}")
        return False
    finally:
        conn.close()

def get_usage_stats(user_id):
    """
    Get usage statistics for a user.
    
    Args:
        user_id (int): The user's ID
        
    Returns:
        tuple: (current_usage, quota)
    """
    conn = get_db_connection()
    user = conn.execute(
        "SELECT usage_current, usage_quota FROM users WHERE id = ?", 
        (user_id,)
    ).fetchone()
    conn.close()
    
    if user:
        return user['usage_current'], user['usage_quota']
    return 0, 0 