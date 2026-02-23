# main.py
import os
import shutil
import asyncio
import aiohttp
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
from zipfile import ZipFile
from tempfile import mkdtemp
from urllib.parse import quote

# ------------------- CONFIG -------------------
CONCURRENT_DOWNLOADS = 30
MAX_IMAGES_DEFAULT = 50
DOWNLOAD_TIMEOUT = 20  # seconds

# ------------------- APP INIT -------------------
app = FastAPI(title="Image Scraper API")

# CORS middleware for frontend (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173/"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- IMAGE SCRAPER -------------------
async def collect_image_urls(keyword: str, max_images: int):
    urls = set()
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await browser.new_page()

        await page.goto(
            f"https://dribbble.com/search/{quote(keyword)}",
            timeout=60000
        )
        await page.wait_for_load_state("networkidle")

        last_height = 0
        while len(urls) < max_images:
            # Scroll page to load more images
            await page.mouse.wheel(0, 8000)
            await page.wait_for_timeout(1200)

            images = await page.query_selector_all("img")
            for img in images:
                src = await img.get_attribute("src")
                if src and "cdn.dribbble.com" in src and "avatar" not in src and "/users/" not in src:
                    urls.add(src.split("?")[0])
                if len(urls) >= max_images:
                    break

            # Stop if no more new content
            new_height = await page.evaluate("document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        await browser.close()

    return list(urls)[:max_images]


# ------------------- ASYNC DOWNLOAD -------------------
async def download_image(session, url, filepath):
    try:
        async with session.get(url, timeout=DOWNLOAD_TIMEOUT) as resp:
            if resp.status == 200:
                with open(filepath, "wb") as f:
                    f.write(await resp.read())
    except Exception as e:
        print(f"⚠️ Failed to download {url}: {e}")


async def download_all(urls, folder_path):
    connector = aiohttp.TCPConnector(limit=CONCURRENT_DOWNLOADS)
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = [
            download_image(session, url, os.path.join(folder_path, f"{i}.jpg"))
            for i, url in enumerate(urls)
        ]
        await asyncio.gather(*tasks)


# ------------------- API ENDPOINT -------------------
@app.post("/scrape")
async def scrape_images(
    keyword: str = Form(...),
    max_images: int = Form(MAX_IMAGES_DEFAULT)
):
    if not keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword is required")

    folder_path = mkdtemp()

    try:
        # Step 1: Collect image URLs
        urls = await collect_image_urls(keyword, max_images)
        if not urls:
            raise HTTPException(status_code=404, detail="No images found")

        # Step 2: Download images concurrently
        await download_all(urls, folder_path)

        # Step 3: Create ZIP file
        zip_path = folder_path + ".zip"
        with ZipFile(zip_path, "w") as zipf:
            for img_file in os.listdir(folder_path):
                zipf.write(os.path.join(folder_path, img_file), arcname=img_file)

        return FileResponse(
            zip_path,
            filename=f"{keyword.replace(' ','_')}.zip",
            media_type="application/zip"
        )

    finally:
        # Cleanup temp folder (keep zip for sending)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)


# ------------------- HEALTH CHECK -------------------
@app.get("/health")
def health():
    return {"status": "ok"}