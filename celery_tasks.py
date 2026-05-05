from celery import Celery
from app import analyze_resume
import os

# Celery configuration
app = Celery('tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

@app.task
def analyze_resume_async(resume_text, role):
    """Async task for resume analysis"""
    return analyze_resume(resume_text, role)