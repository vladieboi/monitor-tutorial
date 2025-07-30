#!/usr/bin/env python3
"""
JD Sports Image Scraper
A minimal scraper that checks for new images on JD Sports CDN and sends notifications.
"""

import time
import requests
import random
import string
from pymongo import MongoClient
from discord_webhook import DiscordWebhook, DiscordEmbed

# Configuration: EDIT THIS BEFORE RUNNING THE SCRIPT
CDN_BASE_URL = "https://i1.adis.ws/i/jpl/jd_{}_a?w=500&unique={}"
MONGO_URL = "mongodb+srv://username:password@cluster.mongodb.net/"
MONGO_DATABASE_NAME = "jdsports_scraper"
MONGO_COLLECTION_NAME = "images"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
DELAY_IN_SECONDS = 1
STARTING_ID = 773220
ENDING_ID = 773230

def generate_unique_string():
    """Generate a random unique string for CDN requests."""
    # Generate 20 random characters (letters and numbers)
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(20))

def connect_to_mongodb():
    """Connect to MongoDB and return database and collection."""
    try:
        client = MongoClient(MONGO_URL)
        db = client[MONGO_DATABASE_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        # Create index if it doesn't exist (ignore if it already exists)
        try:
            collection.create_index("id", unique=True)
        except Exception:
            pass  # Index already exists, that's fine
        return db, collection
    except Exception as e:
        print(f"MongoDB error: {e}")
        return None, None

def fetch_image(image_id):
    """Fetch image from JD Sports CDN and return tuple (response, status_code) if image exists."""
    try:
        unique_string = generate_unique_string()
        url = CDN_BASE_URL.format(image_id, unique_string)
        response = requests.get(url, timeout=10)
        
        # Check if image exists (status 200) and is actually an image
        if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
            return response, response.status_code
        else:
            return None, response.status_code
    except Exception as e:
        print(f"Image fetch error for ID {image_id}: {e}")
        return None, 0

def extract_image_data(image_id, response):
    """Extract relevant data from image response and return it as a dictionary."""
    return {
        "id": image_id,
        "url": response.url  # Use the actual URL that was fetched
    }

def save_to_database(collection, image_data):
    """Save image to database if it doesn't exist and return `True` if it's new. Returns `False` if it's not new or if there's an error."""
    try:
        # Check if image already exists
        existing_image = collection.find_one({"id": image_data["id"]})
        
        if existing_image is None:
            # Image doesn't exist, insert it
            collection.insert_one(image_data)
            return True
        else:
            # Image already exists, skip it
            return False
            
    except Exception as e:
        print(f"Database error: {e}")
        return False

def send_discord_notification(image_data):
    """Send Discord notification for new image."""
    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("Discord webhook URL not configured. Skipping notification.")
        return
    
    try:
        webhook = DiscordWebhook(
            url=DISCORD_WEBHOOK_URL,
            username="JD Sports Image Scraper",
            avatar_url="https://vlad.wwz.ro/favicon.png"
        )
        
        embed = DiscordEmbed(
            title=f"Image Loaded via JD Sports [{image_data['id']}]",
            color=0x00ff00,
            url=image_data['url']
        )
        embed.set_author(name="New image", icon_url="https://vlad.wwz.ro/favicon.png")
        embed.set_image(url=image_data['url'])
        embed.set_footer(text="JD Sports Image Scraper", icon_url="https://vlad.wwz.ro/favicon.png")
        
        webhook.add_embed(embed)
        webhook.execute()
        
    except Exception as e:
        print(f"Discord error: {e}")

def main():
    """Main scraper loop. Connects to MongoDB, fetches images, processes them, and sends notifications for new images."""
    
    # Connect to MongoDB
    print("Starting scraper...")
    db, collection = connect_to_mongodb()
    if collection is None:
        print("MongoDB connection failed. Exiting.")
        return
    print("Scraper running...")
    
    # Main loop
    current_id = STARTING_ID
    while True: 
        try:
            # Fetch image from the website
            response, status_code = fetch_image(current_id)
            
            if response:
                # Image exists, extract data
                image_data = extract_image_data(current_id, response)
                # Try to save to database and check if it's new
                is_new = save_to_database(collection, image_data)
                # If image is new, send notification via Discord
                if is_new:
                    send_discord_notification(image_data)
                    print(f"[{status_code}] Found new image: ID {current_id}")
                else:
                    # Image exists but already in database
                    print(f"[{status_code}] Image already exists: ID {current_id}")
            else:
                # Image fetch was unsuccessful
                print(f"[{status_code}] Failed to fetch image: ID {current_id}")
            
            # Move to next ID
            current_id += 1
            
            # Reset to starting ID when we reach the end
            if current_id > ENDING_ID:
                current_id = STARTING_ID
                print(f"Completed range {STARTING_ID} - {ENDING_ID}, starting over...")
            
            # Wait between requests
            time.sleep(DELAY_IN_SECONDS)
            
        # Stop loop using Ctrl+C
        except KeyboardInterrupt:
            print("Scraper stopped")
            break
        # Print exception when error
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(DELAY_IN_SECONDS)

if __name__ == "__main__":
    main() 