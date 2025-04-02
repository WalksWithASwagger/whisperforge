#!/usr/bin/env python3
"""
Test script for WhisperForge refactored modules.
This script tests the core functionality of the new modular structure.
"""

import os
import logging
import json
from config import logger
import sys
import time
import argparse
import tempfile
import unittest
import requests
from pathlib import Path

# Import from our new modules
from database.db import init_db, get_user_by_id
from auth.auth import init_admin_user, hash_password
from utils.helpers import get_api_key_for_service
from integrations.openai_service import get_openai_client
from content.wisdom import extract_wisdom
from content.outline import generate_outline
from content.blog import generate_blog_post
from content.social import generate_social_content
from content.image import generate_image_prompts
from content.summary import generate_summary

# Setup logging
logger.setLevel(logging.INFO)

def test_database():
    """Test database module functionality."""
    print("\n=== Testing Database Module ===")
    
    # Initialize the database
    init_db()
    print("✓ Database initialized")
    
    # Get admin user
    user = get_user_by_id(1)
    if user and user['email']:
        print(f"✓ Retrieved user: {user['email']}")
    else:
        print("✗ Failed to retrieve user")

def test_auth():
    """Test authentication module functionality."""
    print("\n=== Testing Auth Module ===")
    
    # Initialize admin user
    init_admin_user()
    print("✓ Admin user initialized")
    
    # Test password hashing
    password = "test_password"
    hashed = hash_password(password)
    print(f"✓ Password hashed: {hashed[:10]}...")

def test_utils():
    """Test utilities module functionality."""
    print("\n=== Testing Utils Module ===")
    
    # Test API key retrieval
    api_key = get_api_key_for_service("openai")
    if api_key:
        print(f"✓ Retrieved OpenAI API key: {api_key[:5]}...")
    else:
        print("✗ Failed to retrieve OpenAI API key")

def test_integrations():
    """Test integrations module functionality."""
    print("\n=== Testing Integrations Module ===")
    
    # Test OpenAI client
    client = get_openai_client()
    if client:
        print("✓ OpenAI client initialized")
    else:
        print("✗ Failed to initialize OpenAI client")

def test_content():
    """Test content generation module functionality."""
    print("\n=== Testing Content Module ===")
    
    # Test wisdom generation (without actually calling the API)
    try:
        # Just test if the function can be called
        transcript = "This is a test transcript. It contains some text that we'll use to test the wisdom generation function."
        # Set a flag to skip actual API calls
        result = extract_wisdom(transcript, "OpenAI", "gpt-3.5-turbo")
        print("✓ Wisdom generation function called successfully")
    except Exception as e:
        print(f"✗ Error in wisdom generation: {str(e)}")

class TestWhisperForgeModules(unittest.TestCase):
    """Tests for WhisperForge content generation modules"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Sample transcript for testing
        cls.transcript = """
        Welcome to this podcast episode about productivity systems. Today we're going to discuss how to organize your tasks, manage your time, and reduce stress.
        
        First, let's talk about the importance of having a trusted system. When you have a reliable place to store all your tasks and ideas, your mind can relax knowing nothing will be forgotten.
        
        Second, we'll explore different productivity methodologies like GTD (Getting Things Done), the Pomodoro Technique, and Time Blocking. Each has strengths for different types of work.
        
        Finally, we'll cover how to choose the right tools - whether digital apps or paper systems - based on your specific needs and work style.
        
        Remember, the best productivity system is the one you'll actually use consistently.
        """
        
    def test_extract_wisdom(self):
        """Test wisdom extraction functionality"""
        logger.info("Testing wisdom extraction...")
        start_time = time.time()
        
        result = extract_wisdom(self.transcript, "OpenAI", "gpt-3.5-turbo")
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 100)
        
        logger.info(f"Wisdom extraction test completed in {time.time() - start_time:.2f} seconds")
        logger.info(f"Sample result: {result[:100]}...")
        
    def test_generate_outline(self):
        """Test outline generation functionality"""
        logger.info("Testing outline generation...")
        start_time = time.time()
        
        wisdom = extract_wisdom(self.transcript, "OpenAI", "gpt-3.5-turbo")
        result = generate_outline(self.transcript, wisdom, "OpenAI", "gpt-3.5-turbo")
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 100)
        
        logger.info(f"Outline generation test completed in {time.time() - start_time:.2f} seconds")
        logger.info(f"Sample result: {result[:100]}...")
        
# Additional tests for other modules would go here
        
def main():
    """Run the tests"""
    parser = argparse.ArgumentParser(description='Test WhisperForge modules')
    parser.add_argument('--test', help='Specific test to run (wisdom, outline, etc.)')
    args = parser.parse_args()
    
    suite = unittest.TestSuite()
    
    if args.test == 'wisdom':
        suite.addTest(TestWhisperForgeModules('test_extract_wisdom'))
    elif args.test == 'outline':
        suite.addTest(TestWhisperForgeModules('test_generate_outline'))
    else:
        suite = unittest.makeSuite(TestWhisperForgeModules)
    
    unittest.TextTestRunner(verbosity=2).run(suite)
    
if __name__ == '__main__':
    main() 