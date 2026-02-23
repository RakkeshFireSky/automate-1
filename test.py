from playwright.sync_api import sync_playwright
import os
import requests

URL = "https://dribbble.com/shots/25586920-Prodex-Admin-Dashboard-Design"
DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, timeout=60000)
    page.wait_for_load_state("networkidle")

    # 🎯 ONLY main shot container
    shot_images = page.locator('div img[data-test="v-img"]')

    count = shot_images.count()
    print("Main shot images found:", count)

    for i in range(count):
        img = shot_images.nth(i)

        src = img.get_attribute("src")

        file_path = os.path.join(DOWNLOAD_DIR, f"main_{i}.png")

        if src:
            clean_url = src.split("?")[0]
            try:
                response = requests.get(
                    clean_url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10
                )

                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"Downloaded: main_{i}.png")
                    continue
            except:
                pass

        # Fallback → Screenshot only if URL failed
        img.screenshot(path=file_path)
        print(f"Screenshot fallback: main_{i}.png")

    browser.close()

print("Done.")
