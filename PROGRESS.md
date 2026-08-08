# SkillMe Python Internship Progress

## Week 1: Web Scraper with BeautifulSoup
- **Status**: Completed ✅
- **Task Description**: Built a modular web scraper using `requests` and `BeautifulSoup4` that scrapes product data across 5 paginated pages from `books.toscrape.com`.
- **Features Implemented**:
  - Extracted 5 fields per product (`Title`, `Price`, `Rating`, `Availability`, `Product_URL`).
  - Added robust HTTP error handling and retry mechanism (retry on 429/503/network errors).
  - Included a respectful rate limit delay (`time.sleep(1)`) between requests.
  - Exported structured results into a clean UTF-8 CSV (`scraped_books.csv`).
  - Modular function architecture (`fetch_page`, `parse_page`, `scrape_pages`, `save_to_csv`).
