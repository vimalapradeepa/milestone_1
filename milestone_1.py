# ==============================
# IMPORT REQUIRED LIBRARIES
# ==============================

import os                     # Task 2: Used to create folders and save HTML files
import time                   # Task 6: Used to calculate total execution time
import requests               # Task 6: Used to send HTTP requests to websites
from bs4 import BeautifulSoup # Task 3: Used to parse HTML and extract links
from urllib.parse import urljoin, urlparse  # Task 3 & 4: URL handling utilities


# ==========================================================
# Task 6: FETCH PAGE WITH RETRY AND ERROR HANDLING
# ==========================================================
def fetch_page(url, retries=3):
    attempt = 0   # Keeps track of how many retry attempts have been made

    # Loop until retries are exhausted
    while attempt < retries:
        try:
            # Send HTTP GET request to the given URL
            response = requests.get(
                url,
                timeout=5,  # Wait maximum 5 seconds for server response
                headers={"User-Agent": "MiniCrawler/1.0"},  # Identify crawler
            )

            # If request is successful
            if response.status_code == 200:
                return response.text   # Return HTML content of the page

            # If server responds with error status
            else:
                print(f"[ERROR] Status {response.status_code} → {url}")
                return None

        # DNS error when hostname cannot be resolved
        except requests.exceptions.ConnectionError:
            print(f"[DNS ERROR] Cannot resolve hostname → {url}")

        # Timeout error if site is too slow
        except requests.exceptions.Timeout:
            print(f"[TIMEOUT] While connecting → {url}")

        # Catch any other unexpected error
        except Exception as e:
            print(f"[ERROR] Fetch failed → {e}")

        # Increment retry counter
        attempt += 1

        # Show retry attempt information
        print(f"[RETRY] Attempt {attempt}/{retries} → {url}")

    # All retries failed
    print(f"[FAILED] Giving up after {retries} retries → {url}")
    return None


# ==========================================================
# Task 3: EXTRACT VALID LINKS FROM HTML
# ==========================================================
def extract_links(base_url, html):
    # Convert raw HTML into a parse tree
    soup = BeautifulSoup(html, "html.parser")

    # Use a set to avoid duplicate links
    links = set()

    # Loop through all anchor tags with href attribute
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()  # Remove extra spaces

        # Task 3: Skip unwanted or useless links
        if href.startswith(("mailto:", "javascript:", "#", "tel:")):
            continue

        # Convert relative links into absolute URLs
        full = urljoin(base_url, href)

        # Add only valid HTTP/HTTPS links
        if full.startswith("http"):
            links.add(full)

    # Return all extracted unique links
    return links


# ==========================================================
# Task 2: SAVE FETCHED WEB PAGE INTO FILE SYSTEM
# ==========================================================
def save_page(url, html):
    # Extract domain name from URL
    domain = urlparse(url).netloc.replace(":", "_")

    # Create directory for each domain (if not exists)
    os.makedirs(f"pages/{domain}", exist_ok=True)

    # Clean filename to avoid OS invalid characters
    filename = url.replace("https://", "").replace("http://", "")
    filename = filename.replace("/", "_") \
                       .replace("?", "_") \
                       .replace(":", "_") \
                       .replace("#", "_")

    # Create full file path
    filepath = f"pages/{domain}/{filename}.html"

    # Write HTML content into file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    # Confirm file saved
    print(f"[SAVED] {filepath}")


# ==========================================================
# Task 1: MAIN CRAWLER FUNCTION (BFS APPROACH)
# ==========================================================
def crawl(start_url, max_pages=5):
    # Queue holds URLs waiting to be crawled (FIFO)
    queue = [start_url]          # Task 1

    # Set to store already visited URLs
    visited = set()              # Task 1

    duplicate_count = 0          # Count repeated URLs
    unique_urls = set()          # Track unique URLs

    # Task 4: Store domain of seed URL
    start_domain = urlparse(start_url).netloc

    # Task 6: Start time measurement
    start = time.time()
    pages_crawled = 0

    # Continue crawling until queue empty or max pages reached
    while queue and pages_crawled < max_pages:
        url = queue.pop(0)       # Task 1: FIFO behavior

        # Skip URL if already visited
        if url in visited:
            duplicate_count += 1
            continue

        # ==================================================
        # Task 4: SAME-DOMAIN RESTRICTION
        # ==================================================
        # Prevent crawling external websites
        if urlparse(url).netloc != start_domain:
            print(f"[SKIPPED] Different domain → {url}")
            continue

        # Mark URL as visited
        visited.add(url)
        unique_urls.add(url)

        print(f"\n[FETCHING] {url}")

        # Fetch page safely using retry logic
        html = fetch_page(url)   # Task 6

        # Skip if fetch failed
        if html is None:
            continue

        # Save the downloaded page
        save_page(url, html)     # Task 2

        pages_crawled += 1

        # Extract new links from page
        new_links = extract_links(url, html)  # Task 3

        # Add new links to queue
        for link in new_links:
            if link not in visited:
                queue.append(link)
            else:
                duplicate_count += 1

    # Task 6: End time measurement
    end = time.time()

    # ==================================================
    # Task 5: SAVE VISITED URLS TO FILE
    # ==================================================
    with open("visited.txt", "w") as f:
        for u in visited:
            f.write(u + "\n")

    # ==================================================
    # FINAL SUMMARY REPORT
    # ==================================================
    print("\n====================")
    print("   SUMMARY REPORT   ")
    print("====================")
    print("Pages Crawled        :", pages_crawled)
    print("Total Time (seconds) :", round(end - start, 2))
    print("Unique URLs Seen     :", len(unique_urls))
    print("Duplicates Prevented :", duplicate_count)
    print("Visited URLs saved → visited.txt")


# ==================================================
# PROGRAM EXECUTION STARTS HERE
# ==================================================
if __name__ == "__main__":
    crawl("https://www.python.org", max_pages=10)
