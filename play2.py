import os
import asyncio
import aiohttp
from urllib.parse import quote
from playwright.sync_api import sync_playwright

KEYWORD = "admin dashboard design"
MAX_IMAGES = 50
DOWNLOAD_DIR = "dashboard_images"
CONCURRENT_DOWNLOADS = 20

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ------------------ COLLECT IMAGES ------------------

def collect_image_urls():
    urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🔎 Searching...")
        page.goto(f"https://dribbble.com/search/{quote(KEYWORD)}", timeout=60000)

        page.wait_for_load_state("networkidle")

        last_height = 0

        while len(urls) < MAX_IMAGES:
            page.mouse.wheel(0, 8000)
            page.wait_for_timeout(1500)

            images = page.query_selector_all("img")

            for img in images:
                src = img.get_attribute("src")
                if not src:
                    continue

                if (
                    "cdn.dribbble.com" in src
                    and "avatar" not in src
                    and "/users/" not in src
                ):
                    clean = src.split("?")[0]
                    urls.add(clean)

                if len(urls) >= MAX_IMAGES:
                    break

            # stop if no more new content loads
            new_height = page.evaluate("document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        browser.close()

    print("Collected:", len(urls))
    return list(urls)[:MAX_IMAGES]


# ------------------ FAST ASYNC DOWNLOAD ------------------

async def download_image(session, url, filepath):
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(filepath, "wb") as f:
                    f.write(await resp.read())
                print("✅", filepath)
    except:
        print("⚠️ Failed:", url)


async def download_all(urls):
    connector = aiohttp.TCPConnector(limit=CONCURRENT_DOWNLOADS)
    headers = {"User-Agent": "Mozilla/5.0"}

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = []
        for i, url in enumerate(urls):
            file_path = os.path.join(DOWNLOAD_DIR, f"{KEYWORD.replace(' ','_')}_{i}.jpg")
            tasks.append(download_image(session, url, file_path))

        await asyncio.gather(*tasks)


# ------------------ MAIN ------------------

def main():
    urls = collect_image_urls()

    if not urls:
        print("No images found.")
        return

    print(f"⚡ Downloading {len(urls)} images fast...")
    asyncio.run(download_all(urls))


if __name__ == "__main__":
    main()