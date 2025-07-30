#!/usr/bin/env python3
"""
Shoe Palace Product Monitor
A minimal monitor that checks for new products and sends notifications.
"""

import time
import requests
from pymongo import MongoClient
from discord_webhook import DiscordWebhook, DiscordEmbed

# Configuration: EDIT THIS BEFORE RUNNING THE SCRIPT
WEBSITE_URL = "https://shoepalace.com/products.json"
MONGO_URL = "mongodb+srv://username:password@cluster.mongodb.net/"
MONGO_DATABASE_NAME = "shoepalace_monitor"
MONGO_COLLECTION_NAME = "products"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
DELAY_IN_SECONDS = 30

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

def fetch_products():
    """Fetch products from website JSON endpoint and return them as a tuple (products_list, status_code)."""
    try:
        # You can add proxies here to avoid being banned
        response = requests.get(WEBSITE_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("products", []), response.status_code
    except Exception as e:
        print(f"API error: {e}")
        return [], 0

def extract_product_data(product):
    """Extract relevant data from product and return it as a dictionary."""
    # Get first image URL
    image_url = ""
    if product.get("images"):
        image_url = product["images"][0].get("src", "")
    
    # Get all variants and sizes
    variants = product.get("variants", [])
    sizes = []
    atc_links = {}
    
    for variant in variants:
        size = variant.get("title", "")
        variant_id = variant.get("id", "")
        if size and variant_id:
            sizes.append(size)
            # Sanitize size for MongoDB (replace dots with underscores)
            sanitized_size = size.replace(".", "_")
            atc_links[sanitized_size] = f"https://shoepalace.com/cart/{variant_id}:1"
    
    return {
        "id": product.get("id"),
        "url": f"https://shoepalace.com/products/{product.get('handle', '')}",
        "image": image_url,
        "title": product.get("title", ""),
        "price": variants[0].get("price", "0.00") if variants else "0.00",
        "sizes": sizes,
        "atc_links": atc_links
    }

def save_to_database(collection, product_data):
    """Save product to database if it doesn't exist and return `True` if it's new. Returns `False` if it's not new or if there's an error."""
    try:
        # Check if product already exists
        existing_product = collection.find_one({"id": product_data["id"]})
        
        if existing_product is None:
            # Product doesn't exist, insert it
            collection.insert_one(product_data)
            return True
        else:
            # Product already exists, skip it
            return False
            
    except Exception as e:
        print(f"Database error: {e}")
        return False

def send_discord_notification(product_data):
    """Send Discord notification for new product."""
    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("Discord webhook URL not configured. Skipping notification.")
        return
    
    try:
        webhook = DiscordWebhook(
            url=DISCORD_WEBHOOK_URL,
            username="Shoe Palace Monitor",
            avatar_url="https://vlad.wwz.ro/favicon.png"
        )
        
        # Format sizes into 3 columns
        sizes = product_data.get('sizes', [])
        atc_links = product_data.get('atc_links', {})
        
        if sizes:
            total_sizes = len(sizes)
            col1_size = (total_sizes + 2) // 3
            col2_size = (total_sizes + 1) // 3
            
            # Column 1
            col1_sizes = []
            for i in range(min(col1_size, total_sizes)):
                size = sizes[i]
                sanitized_size = size.replace(".", "_")
                link = atc_links.get(sanitized_size, product_data['url'])
                col1_sizes.append(f"[{size} US]({link})")
            
            # Column 2
            col2_sizes = []
            for i in range(col1_size, min(col1_size + col2_size, total_sizes)):
                size = sizes[i]
                sanitized_size = size.replace(".", "_")
                link = atc_links.get(sanitized_size, product_data['url'])
                col2_sizes.append(f"[{size} US]({link})")
            
            # Column 3
            col3_sizes = []
            for i in range(col1_size + col2_size, total_sizes):
                size = sizes[i]
                sanitized_size = size.replace(".", "_")
                link = atc_links.get(sanitized_size, product_data['url'])
                col3_sizes.append(f"[{size} US]({link})")
        else:
            col1_sizes = col2_sizes = col3_sizes = []
        
        embed = DiscordEmbed(
            title=product_data['title'],
            url=product_data['url'],
            color=0x00ff00,
        )
        embed.set_author(name="New product")
        embed.add_embed_field(name="Price", value=f"${product_data['price']}", inline=True)
        embed.add_embed_field(name="Website", value="Shoe Palace 🇺🇸", inline=True)
        embed.add_embed_field(name="ID", value=str(product_data['id']), inline=True)
        if col1_sizes:
            embed.add_embed_field(name="Sizes", value="\n".join(col1_sizes), inline=True)
        if col2_sizes:
            embed.add_embed_field(name="Sizes", value="\n".join(col2_sizes), inline=True)
        if col3_sizes:
            embed.add_embed_field(name="Sizes", value="\n".join(col3_sizes), inline=True)
        
        if product_data['image']:
            embed.set_thumbnail(url=product_data['image'])
        embed.set_footer(text="Shoe Palace Monitor", icon_url="https://vlad.wwz.ro/favicon.png")
        embed.set_timestamp()
        
        webhook.add_embed(embed)
        webhook.execute()
        
    except Exception as e:
        print(f"Discord error: {e}")

def main():
    """Main monitor loop. Connects to MongoDB, fetches products, processes them, and sends notifications for new products."""
    
    # Connect to MongoDB
    print("Starting monitor...")
    db, collection = connect_to_mongodb()
    if collection is None:
        print("MongoDB connection failed. Exiting.")
        return
    print("Monitor running...")
    
    # Main loop
    while True:
        try:
            # Fetch products from the website
            products, status_code = fetch_products()
            if not products:
                time.sleep(DELAY_IN_SECONDS)
                continue
            
            # Parse and process each product
            new_products_count = 0
            for product in products:
                product_data = extract_product_data(product)
                # Try check if product is new and save to database
                is_new = save_to_database(collection, product_data)
                # If product is new, send notification via Discord
                if is_new:
                    new_products_count += 1
                    send_discord_notification(product_data)
            
            if new_products_count > 0:
                print(f"[{status_code}] Found {new_products_count} new products")
            else:
                print(f"[{status_code}] No new products found")
            
            # Wait for the next iteration
            time.sleep(DELAY_IN_SECONDS)
            
        # Stop loop using Ctrl+C
        except KeyboardInterrupt:
            print("Monitor stopped")
            break
        # Print exception when error
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(DELAY_IN_SECONDS)

if __name__ == "__main__":
    main() 