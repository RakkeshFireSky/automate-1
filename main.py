# main.py
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, asyncio, aiohttp
from playwright.async_api import async_playwright
from tempfile import mkdtemp
from zipfile import ZipFile
from urllib.parse import quote

app = FastAPI(title="Image Scraper API")

# ------------------- CORS -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- IMAGE SCRAPER (simplified) -------------------
async def collect_image_urls(keyword: str, max_images: int):
    urls = set()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"https://dribbble.com/search/{quote(keyword)}")
        await page.wait_for_load_state("networkidle")
        images = await page.query_selector_all("img")
        for img in images:
            src = await img.get_attribute("src")
            if src and "cdn.dribbble.com" in src and "avatar" not in src:
                urls.add(src.split("?")[0])
            if len(urls) >= max_images:
                break
        await browser.close()
    return list(urls)[:max_images]

async def download_image(session, url, filepath):
    async with session.get(url) as resp:
        if resp.status == 200:
            with open(filepath, "wb") as f:
                f.write(await resp.read())

async def download_all(urls, folder_path):
    connector = aiohttp.TCPConnector(limit=30)
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = [download_image(session, url, os.path.join(folder_path, f"{i}.jpg")) for i, url in enumerate(urls)]
        await asyncio.gather(*tasks)

# ------------------- API ENDPOINT -------------------
@app.post("/scrape")
@app.post("/scrape/")  # <-- add this to handle trailing slash
async def scrape_images(
    keyword: str = Form(...),
    max_images: int = Form(50)
):
    if not keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword is required")

    folder_path = mkdtemp()
    try:
        urls = await collect_image_urls(keyword, max_images)
        if not urls:
            raise HTTPException(status_code=404, detail="No images found")

        await download_all(urls, folder_path)

        zip_path = folder_path + ".zip"
        with ZipFile(zip_path, "w") as zipf:
            for img_file in os.listdir(folder_path):
                zipf.write(os.path.join(folder_path, img_file), arcname=img_file)

        return FileResponse(
            zip_path,
            filename=f"{keyword.replace(' ', '_')}.zip",
            media_type="application/zip"
        )
    finally:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)