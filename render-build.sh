#!/bin/bash
# Upgrade pip just in case
pip install --upgrade pip

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install