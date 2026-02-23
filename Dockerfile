# Use the official Playwright Python image with Chromium pre-installed
FROM mcr.microsoft.com/playwright/python:1.58.0-focal

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose your FastAPI port
EXPOSE 10000

# Start FastAPI via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]