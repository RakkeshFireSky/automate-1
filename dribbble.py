import os
import requests
from apify_client import ApifyClient
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# ==============================
# CONFIG
# ==============================
load_dotenv()
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

URL = "https://dribbble.com/shots/24324744-HR-management-admin-dashboard-design"
DOWNLOAD_DIR = "image_screenshots"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

client = ApifyClient(APIFY_TOKEN)

print("Running Dribbble scraper...")

# ==============================
# RUN APIFY ACTOR
# ==============================
run = client.actor("easyapi/dribbble-designer-scraper").call(
    run_input={
        "startUrls": [{"url": URL}],
        "proxyConfiguration": {"useApifyProxy": True}
    }
)

dataset_id = run["defaultDatasetId"]
items = client.dataset(dataset_id).list_items().items

print(f"Total items found: {len(items)}")

# ==============================
# EXTRACT IMAGE URLS
# ==============================
image_urls = []

for item in items:
    img = (
        item.get("imageUrl")
        or item.get("image")
        or item.get("thumbnail")
        or item.get("thumbnailUrl")
    )
    if img:
        image_urls.append(img.split("?")[0])

print(f"Collected {len(image_urls)} image URLs")

# ==============================
# SCREENSHOT EACH IMAGE
# ==============================
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for i, img_url in enumerate(image_urls):
        page = browser.new_page()
        page.goto(img_url)
        page.wait_for_timeout(2000)

        # Select the image element
        img_element = page.query_selector("img")

        if img_element:
            file_path = os.path.join(DOWNLOAD_DIR, f"image_{i}.png")
            img_element.screenshot(path=file_path)
            print(f"Saved screenshot: {file_path}")
        else:
            print("Image element not found")

        page.close()

    browser.close()

print("Done.")
print("Items: ", items[0])