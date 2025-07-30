# Product Monitor and Scraper

A Python-based toolkit for monitoring product releases and scraping images from e-commerce websites. Built with MongoDB for data storage and Discord for notifications. You can read more about how to write your own toolkit [here](https://vlad.wwz.ro/blog/setting-up-your-own-product-monitor-and-scraper).

## Overview

This project contains two main tools:

- **Monitor** (`monitor.py`) - Tracks new product releases on Shoe Palace
- **Scraper** (`scraper.py`) - Discovers new images on JD Sports CDN

Both tools use the same core architecture: fetch data, check for new items, save to database, and send Discord notifications.

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Before running either script, update the configuration variables:

### Monitor Configuration (`monitor.py`)
```python
WEBSITE_URL = "https://shoepalace.com/products.json"
MONGO_URL = "mongodb+srv://username:password@cluster.mongodb.net/"
MONGO_DATABASE_NAME = "shoepalace_monitor"
MONGO_COLLECTION_NAME = "products"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
DELAY_IN_SECONDS = 30
```

### Scraper Configuration (`scraper.py`)
```python
CDN_BASE_URL = "https://i1.adis.ws/i/jpl/jd_{}_a?w=500&unique={}"
MONGO_URL = "mongodb+srv://username:password@cluster.mongodb.net/"
MONGO_DATABASE_NAME = "jdsports_scraper"
MONGO_COLLECTION_NAME = "images"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
DELAY_IN_SECONDS = 1
STARTING_ID = 773220
ENDING_ID = 773230
```

## Usage

### Running the Monitor
```bash
python3 monitor.py
```

### Running the Scraper
```bash
python3 scraper.py
```

## License

This project is for educational purposes. Use responsibly and in accordance with target website terms of service. 