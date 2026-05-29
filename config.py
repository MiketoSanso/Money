import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'studio-secret-key-2025'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost:5432/photo_studio'
    DEBUG = True
