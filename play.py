from playwright.sync_api import sync_playwright
import os

URL = "https://dribbble.com/shots/24324744-HR-management-admin-dashboard-design"
DOWNLOAD_DIR = "image_screenshots"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL)
    page.wait_for_timeout(3000)  # wait for images to load

    # Find all visible images
    images = page.query_selector_all("img")
    print(f"Found {len(images)} images")

    for i, img in enumerate(images):
        if img.is_visible():
            file_path = os.path.join(DOWNLOAD_DIR, f"image_{i}.png")
            img.screenshot(path=file_path)
            print(f"Saved screenshot: {file_path}")

    browser.close()

print("Done!")