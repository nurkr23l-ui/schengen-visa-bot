import os
import sys
import logging
import json
import asyncio
import requests
import telebot
from telebot import types
from dotenv import load_dotenv
import time
import urllib3
import pytz
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Set timezone
TURKEY_TIMEZONE = pytz.timezone('Europe/Istanbul')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def format_date(date_str):
    """Format date: YYYY-MM-DD -> DD Month YYYY"""
    try:
        year, month, day = map(int, date_str.split('-'))
        return f"{day} {MONTHS_TR[month]} {year}"
    except:
        return date_str  # Return original date in case of error

def get_current_time():
    """Return current time in Turkey timezone"""
    return datetime.now(TURKEY_TIMEZONE)