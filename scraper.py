"""
Web Scraper with BeautifulSoup
Week 1 Project - SkillMe Python Internship

Scrapes structured product data from books.toscrape.com across multiple pages,
handles HTTP errors gracefully with retries, respects rate limits with delays,
and outputs clean structured data to a CSV file.
"""

import csv
import logging
import re
import sys
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Base configuration constants
BASE_URL = "http://books.toscrape.com/catalogue/page-{page}.html"
SITE_DOMAIN = "http://books.toscrape.com/catalogue/"
OUTPUT_CSV = "scraped_books.csv"
DEFAULT_PAGES = 5
REQUEST_DELAY = 1.0  # seconds between requests
MAX_RETRIES = 3
TIMEOUT = 10  # seconds


def fetch_page(url: str, retries: int = MAX_RETRIES, delay: float = REQUEST_DELAY) -> Optional[str]:
    """
    Fetches the HTML content of a URL with retry logic for HTTP errors (e.g. 429, 503).

    Args:
        url (str): Target web page URL.
        retries (int): Maximum number of retry attempts.
        delay (float): Delay in seconds before retrying.

    Returns:
        Optional[str]: Raw HTML text if successful, None otherwise.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.4000 Safari/537.36"
        )
    }

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Fetching URL (Attempt {attempt}/{retries}): {url}")
            response = requests.get(url, headers=headers, timeout=TIMEOUT)

            # Check for retryable HTTP status codes (429 Too Many Requests, 500, 502, 503, 504)
            if response.status_code in (429, 500, 502, 503, 504):
                logger.warning(f"HTTP {response.status_code} received from {url}. Retrying in {delay * attempt}s...")
                time.sleep(delay * attempt)
                continue

            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as exc:
            logger.error(f"Request failed for {url} on attempt {attempt}: {exc}")
            if attempt < retries:
                time.sleep(delay * attempt)
            else:
                logger.error(f"Max retries reached. Unable to fetch {url}.")
                return None

    return None


def parse_page(html_content: str, base_url: str = SITE_DOMAIN) -> List[Dict[str, str]]:
    """
    Parses HTML content using BeautifulSoup to extract book items and their fields.

    Args:
        html_content (str): HTML content of the page.
        base_url (str): Base URL to resolve relative product links.

    Returns:
        List[Dict[str, str]]: List of dictionary items containing book fields.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    product_pods = soup.find_all("article", class_="product_pod")
    books: List[Dict[str, str]] = []

    for pod in product_pods:
        try:
            # 1. Title
            title_tag = pod.h3.find("a") if pod.h3 else None
            title = title_tag["title"].strip() if (title_tag and title_tag.has_attr("title")) else "N/A"

            # 2. Price
            price_tag = pod.find("p", class_="price_color")
            price = f"£{re.sub(r'[^\d.]', '', price_tag.text)}" if price_tag else "N/A"

            # 3. Rating
            rating_tag = pod.find("p", class_="star-rating")
            rating = "N/A"
            if rating_tag and "class" in rating_tag.attrs:
                classes = rating_tag["class"]
                # Extract rating word (One, Two, Three, Four, Five)
                rating = [c for c in classes if c != "star-rating"][0] if len(classes) > 1 else "N/A"

            # 4. Availability
            availability_tag = pod.find("p", class_="instock availability")
            availability = availability_tag.text.strip() if availability_tag else "N/A"

            # 5. Product Link
            link_rel = title_tag["href"] if title_tag and title_tag.has_attr("href") else ""
            product_url = urljoin(base_url, link_rel)

            books.append({
                "Title": title,
                "Price": price,
                "Rating": rating,
                "Availability": availability,
                "Product_URL": product_url,
            })
        except Exception as err:
            logger.warning(f"Error parsing product pod: {err}")
            continue

    return books


def scrape_pages(total_pages: int = DEFAULT_PAGES, delay: float = REQUEST_DELAY) -> List[Dict[str, str]]:
    """
    Scrapes product data across multiple paginated pages with respectful delays.

    Args:
        total_pages (int): Number of pages to scrape.
        delay (float): Delay in seconds between page requests.

    Returns:
        List[Dict[str, str]]: Combined list of all extracted items.
    """
    all_books: List[Dict[str, str]] = []

    for page_num in range(1, total_pages + 1):
        target_url = BASE_URL.format(page=page_num)
        logger.info(f"--- Scraping Page {page_num} of {total_pages} ---")

        html = fetch_page(target_url)
        if html:
            page_books = parse_page(html)
            logger.info(f"Successfully extracted {len(page_books)} books from page {page_num}.")
            all_books.extend(page_books)
        else:
            logger.error(f"Skipping page {page_num} due to fetch failure.")

        # Respectful delay between requests
        if page_num < total_pages:
            logger.info(f"Waiting {delay} seconds before requesting next page...")
            time.sleep(delay)

    return all_books


def save_to_csv(data: List[Dict[str, str]], filename: str = OUTPUT_CSV) -> bool:
    """
    Saves extracted data dictionary list to a CSV file with headers.

    Args:
        data (List[Dict[str, str]]): List of extracted records.
        filename (str): Target CSV filename.

    Returns:
        bool: True if write succeeded, False otherwise.
    """
    if not data:
        logger.warning("No data to save.")
        return False

    fieldnames = list(data[0].keys())

    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Saved {len(data)} items to '{filename}'.")
        return True
    except IOError as err:
        logger.error(f"Failed to write CSV file '{filename}': {err}")
        return False


def main() -> None:
    """
    Main entry point for running the web scraper pipeline.
    """
    logger.info("Starting Web Scraper...")
    scraped_data = scrape_pages(total_pages=DEFAULT_PAGES, delay=REQUEST_DELAY)
    logger.info(f"Total items scraped: {len(scraped_data)}")

    if scraped_data:
        success = save_to_csv(scraped_data, OUTPUT_CSV)
        if success:
            logger.info(f"Web Scraping completed successfully! Output saved to {OUTPUT_CSV}")
        else:
            logger.error("Failed to save data to CSV.")
    else:
        logger.error("No items scraped.")


if __name__ == "__main__":
    main()
