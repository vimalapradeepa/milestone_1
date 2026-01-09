import threading
import queue
import time
import os
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag

# -------------------------------
# SETTINGS
# -------------------------------

SEED_URLS = [
    "https://example.com",
    "https://www.python.org",
    "https://www.wikipedia.org"
]

MAX_PAGES = 20
NUM_WORKERS = 3
SAVE_DIR = "pages"

os.makedirs(SAVE_DIR, exist_ok=True)

# -------------------------------
# SHARED STATE
# -------------------------------

url_queue = queue.Queue()
visited = set()
lock = threading.Lock()

pages_crawled = 0
STOP_FLAG = False


# -------------------------------
# FETCH HTML
# -------------------------------

def fetch_page(url):
    try:
        resp = requests.get(url, timeout=8, headers={
            "User-Agent": "MiniCrawler/1.0"
        })
        if resp.status_code != 200:
            return None
        return resp.text
    except:
        return None


# -------------------------------
# SAVE PAGE TO DISK
# -------------------------------

def save_page(url, html):
    fname = hashlib.md5(url.encode()).hexdigest() + ".html"
    path = os.path.join(SAVE_DIR, fname)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    return path


# -------------------------------
# EXTRACT LINKS
# -------------------------------

def extract_links(html, base):
    soup = BeautifulSoup(html, "lxml")
    links = []

    for a in soup.find_all("a", href=True):
        link = urljoin(base, a["href"])
        link, _ = urldefrag(link)

        if link.startswith("http"):
            links.append(link)

    return links


# -------------------------------
# WORKER THREAD
# -------------------------------

def worker(worker_id):
    global pages_crawled, STOP_FLAG

    print(f"[WORKER-{worker_id}] Ready — waiting for URLs...")

    while True:

        # stop if global stop flag set
        with lock:
            if STOP_FLAG:
                return

        try:
            url = url_queue.get(timeout=2)
        except queue.Empty:
            return

        with lock:
            # skip duplicates
            if url in visited:
                url_queue.task_done()
                continue

            # hard stop BEFORE crawling extra pages
            if pages_crawled >= MAX_PAGES:
                STOP_FLAG = True
                url_queue.task_done()
                return

            visited.add(url)

        html = fetch_page(url)

        if not html:
            print(f"[WORKER-{worker_id}] ✗ Failed: {url}")
            url_queue.task_done()
            continue

        save_page(url, html)

        soup = BeautifulSoup(html, "lxml")
        title = soup.title.string.strip() if soup.title else "No Title"

        with lock:
            pages_crawled += 1
            count = pages_crawled

            print(f"[WORKER-{worker_id}] ✓ Crawled ({count}): {url} -> {title}")

            # if limit reached, stop expansion
            if pages_crawled >= MAX_PAGES:
                STOP_FLAG = True

        # enqueue links ONLY if limit not hit
        if not STOP_FLAG:
            for link in extract_links(html, url):
                with lock:
                    if link not in visited:
                        url_queue.put(link)

        url_queue.task_done()


# -------------------------------
# RUN CRAWLER
# -------------------------------

start_time = time.time()

print(f"\n=== {NUM_WORKERS} Workers Started in Single Terminal ===\n")

for url in SEED_URLS:
    url_queue.put(url)

threads = []

for wid in range(1, NUM_WORKERS + 1):
    t = threading.Thread(target=worker, args=(wid,), daemon=True)
    t.start()
    threads.append(t)

# wait for crawling to complete
for t in threads:
    t.join()

elapsed = round(time.time() - start_time, 2)

print("\n\n========== SUMMARY ==========")
print(f"Workers used        : {NUM_WORKERS}")
print(f"Total pages crawled : {pages_crawled}")
print(f"Time taken (sec)    : {elapsed}")
print(f"Pages saved in      : {SAVE_DIR}")
print("================================")
