# Use Playwright image with all browsers preinstalled
FROM mcr.microsoft.com/playwright:focal

# Set working directory
WORKDIR /app

# Copy your project files
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port your FastAPI app will run on
EXPOSE 10000

# Command to run your app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]