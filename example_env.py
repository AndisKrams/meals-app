# Environment Variables Configuration

import os

# Database connection string
# For local development, you can omit this to use SQLite
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://URL_TO_YOUR_DATABASE_HERE",
)

# Django secret key - generate a new one for production
os.environ.setdefault("SECRET_KEY", "your-secret-key-here")

# Set to "1" for development mode (enables DEBUG=True)
# Remove or comment out for production
os.environ.setdefault("DEVELOPMENT", "1")
