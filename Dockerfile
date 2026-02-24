# Use Python 3.14 slim image
FROM python:3.14-slim

# Install system dependencies required by Playwright
RUN apt-get update && apt-get install -y \
    libgtk-4-1 libnss3 libxss1 libasound2 libgbm1 \
    libpangocairo-1.0-0 libx11-xcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxext6 libxi6 libxrandr2 libatk1.0-0 libcups2 \
    libdrm2 libxinerama1 libxkbcommon0 libwayland-client0 libwayland-cursor0 \
    libwoff1 libepoxy0 libgles2-mesa libpango-1.0-0 libpangocairo-1.0-0 \
    libharfbuzz0b libjpeg-dev libpng-dev libglib2.0-0 libfontconfig1 \
    wget curl unzip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy your project files
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Expose port for FastAPI
EXPOSE 10000

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]