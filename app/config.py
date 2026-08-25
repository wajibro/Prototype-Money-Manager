import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_URL      = os.environ.get("DB_URL")
    DB_KEY      = os.environ.get("DB_KEY")
    CORRECT_PIN = os.environ.get("CORRECT_PIN")
    SECRET_KEY  = os.environ.get('SECRET_KEY')