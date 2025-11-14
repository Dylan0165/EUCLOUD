# EUCLOUD Backend

Flask REST API for EUCLOUD file storage platform.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
copy .env.example .env
```

4. Run server:
```bash
python app.py
```

Server runs on http://localhost:5000

## Project Structure

```
backend/
├── app.py              # Main application
├── config.py           # Configuration
├── models.py           # Database models
├── routes/             # API routes
│   ├── auth.py         # Authentication
│   ├── files.py        # File operations
│   ├── folders.py      # Folder operations
│   ├── shares.py       # Sharing
│   └── storage.py      # Storage stats
├── uploads/            # Uploaded files
├── thumbnails/         # Image thumbnails
└── eucloud.db          # SQLite database
```

## API Documentation

See main README.md for full API documentation.
