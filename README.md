# AI Resume Analyzer

An advanced AI-powered resume analysis tool built with Flask, OpenAI GPT, and modern web technologies.

## Features

- 🤖 AI-powered resume analysis using OpenAI GPT-4
- 📊 Interactive skill gap visualization with Chart.js
- 📱 Progressive Web App (PWA) with offline capabilities
- 🔒 Secure authentication with rate limiting
- 📈 Analytics dashboard for tracking progress
- 📄 Support for PDF, DOCX, and TXT file formats
- 🎯 Role-specific skill recommendations
- 📋 Learning roadmaps and interview questions
- 💾 Report history and management

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env`:
   ```
   SECRET_KEY=your-secret-key
   OPENAI_API_KEY=your-openai-api-key
   REDIS_URL=redis://localhost:6379/0  # For Celery
   ```

4. Initialize the database:
   ```bash
   python app.py
   ```

5. Run with Celery for async processing:
   ```bash
   celery -A celery_tasks worker --loglevel=info
   ```

6. Start the application:
   ```bash
   python app.py
   ```

## Deployment

The app is configured for Heroku deployment with the included `Procfile` and `runtime.txt`.

## Technologies Used

- Flask - Web framework
- OpenAI GPT-4 - AI analysis
- SQLAlchemy - Database ORM
- Chart.js - Data visualization
- Bootstrap 5 - UI framework
- Celery - Async task processing
- Redis - Message broker

## License

MIT License