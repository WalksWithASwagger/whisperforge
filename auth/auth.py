import hashlib
import jwt
from datetime import datetime, timedelta
import re
import logging
import streamlit as st

# Import from config
from config import JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD, logger
# Import from database
from database.db import get_db_connection, get_user_by_email, create_user

def hash_password(password):
    """
    Hash a password using SHA-256.
    
    Args:
        password (str): The plaintext password
        
    Returns:
        str: The hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()

def create_jwt_token(user_id):
    """
    Create a JWT token for authentication.
    
    Args:
        user_id (int): The user's ID
        
    Returns:
        str: The JWT token
    """
    expiration = datetime.utcnow() + timedelta(hours=24)
    payload = {
        "user_id": user_id,
        "exp": expiration
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

def validate_jwt_token(token):
    """
    Validate a JWT token.
    
    Args:
        token (str): The JWT token
        
    Returns:
        int or None: The user ID if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["user_id"]
    except:
        return None

def authenticate_user(email, password):
    """
    Authenticate a user with email and password.
    
    Args:
        email (str): The user's email
        password (str): The user's password
        
    Returns:
        int or None: The user ID if authenticated, None otherwise
    """
    conn = get_db_connection()
    hashed_password = hash_password(password)
    
    user = conn.execute(
        "SELECT id FROM users WHERE email = ? AND password = ?",
        (email, hashed_password)
    ).fetchone()
    
    conn.close()
    
    if user:
        return user["id"]
    return None

def is_valid_email(email):
    """
    Check if an email is valid.
    
    Args:
        email (str): The email to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Simple regex for email validation
    email_pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    return bool(email_pattern.match(email))

def register_user(email, password):
    """
    Register a new user.
    
    Args:
        email (str): The user's email
        password (str): The user's password
        
    Returns:
        int or None: The user ID if registered successfully, None otherwise
    """
    if not is_valid_email(email):
        return None
    
    # Check if user already exists
    existing_user = get_user_by_email(email)
    if existing_user:
        return None
    
    # Hash password and create user
    hashed_password = hash_password(password)
    user_id = create_user(email, hashed_password)
    
    return user_id

def init_admin_user():
    """
    Initialize the admin user if it doesn't exist.
    """
    conn = get_db_connection()
    admin = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (ADMIN_EMAIL,)
    ).fetchone()
    
    if not admin:
        logger.info(f"Creating admin user with email: {ADMIN_EMAIL}")
        hashed_password = hash_password(ADMIN_PASSWORD)
        
        conn.execute(
            "INSERT INTO users (email, password, is_admin) VALUES (?, ?, 1)",
            (ADMIN_EMAIL, hashed_password)
        )
        conn.commit()
    
    conn.close()

def is_admin_user(user_id):
    """
    Check if a user is an admin.
    
    Args:
        user_id (int): The user's ID
        
    Returns:
        bool: True if admin, False otherwise
    """
    conn = get_db_connection()
    user = conn.execute(
        "SELECT is_admin FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    
    return user and user["is_admin"] == 1

def require_auth(redirect_if_not_auth=True):
    """
    Decorator-like function to require authentication.
    
    Args:
        redirect_if_not_auth (bool): Whether to redirect to the login page if not authenticated
        
    Returns:
        bool: True if authenticated, False otherwise
    """
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        if redirect_if_not_auth:
            st.session_state.page = "login"
        return False
    return True

def login_user(email, password):
    """
    Log in a user and set session state.
    
    Args:
        email (str): The user's email
        password (str): The user's password
        
    Returns:
        bool: True if logged in successfully, False otherwise
    """
    user_id = authenticate_user(email, password)
    
    if user_id:
        # Set session state
        st.session_state.authenticated = True
        st.session_state.user_id = user_id
        
        # Create and store JWT token
        token = create_jwt_token(user_id)
        st.session_state.token = token
        
        # Check if admin
        st.session_state.is_admin = is_admin_user(user_id)
        
        return True
    
    return False

def logout_user():
    """
    Log out a user by clearing session state.
    """
    if 'authenticated' in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' in st.session_state:
        st.session_state.user_id = None
    if 'token' in st.session_state:
        st.session_state.token = None
    if 'is_admin' in st.session_state:
        st.session_state.is_admin = False 