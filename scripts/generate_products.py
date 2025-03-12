#!/usr/bin/env python3
"""
Script to generate synthetic product data for the e-commerce search demo.
"""
import os
import sys
import json
import uuid
import random
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from app
from app.config.settings import NUM_PRODUCTS, TEXT_EMBEDDING_DIMS, IMAGE_EMBEDDING_DIMS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Product categories and their subcategories
PRODUCT_CATEGORIES = {
    "Electronics": [
        "Smartphones", "Laptops", "Tablets", "Monitors", "Headphones", 
        "Speakers", "Cameras", "Printers", "Smart Home", "Wearables"
    ],
    "Clothing": [
        "Men's Shirts", "Women's Dresses", "Jeans", "Shoes", "Jackets",
        "Activewear", "Underwear", "Socks", "Hats", "Accessories"
    ],
    "Home & Kitchen": [
        "Cookware", "Appliances", "Furniture", "Bedding", "Bath",
        "Decor", "Storage", "Cleaning", "Dining", "Lighting"
    ],
    "Office Supplies": [
        "Pens & Pencils", "Notebooks", "Desk Accessories", "Printers & Ink",
        "Paper", "Binders", "Calendars", "Staplers", "Scissors", "Markers"
    ],
    "Beauty & Personal Care": [
        "Skincare", "Makeup", "Hair Care", "Fragrances", "Oral Care",
        "Shaving", "Bath & Body", "Nail Care", "Tools & Accessories", "Men's Grooming"
    ]
}

# Popular brands for each category
BRANDS = {
    "Electronics": [
        "Apple", "Samsung", "Sony", "LG", "Dell", "HP", "Lenovo", "Bose",
        "Canon", "Logitech", "Microsoft", "Asus", "Acer", "JBL", "Philips"
    ],
    "Clothing": [
        "Nike", "Adidas", "Levi's", "H&M", "Zara", "Gap", "Calvin Klein",
        "Ralph Lauren", "Under Armour", "Puma", "Tommy Hilfiger", "Gucci", "Uniqlo"
    ],
    "Home & Kitchen": [
        "KitchenAid", "Cuisinart", "Calphalon", "Ninja", "Instant Pot", "OXO",
        "Pyrex", "Rubbermaid", "Ikea", "Dyson", "Shark", "Breville", "Keurig"
    ],
    "Office Supplies": [
        "Staples", "3M", "Pilot", "Sharpie", "Moleskine", "Bic", "HP", "Epson",
        "Brother", "Avery", "Scotch", "Faber-Castell", "Papermate", "Zebra"
    ],
    "Beauty & Personal Care": [
        "L'Oreal", "Maybelline", "Neutrogena", "Dove", "Olay", "Nivea", "Pantene",
        "Garnier", "Revlon", "Clinique", "Estee Lauder", "Gillette", "Colgate"
    ]
}

# Common attributes for each category
ATTRIBUTES = {
    "Electronics": {
        "color": ["Black", "White", "Silver", "Gray", "Blue", "Red"],
        "weight": ["Light", "Medium", "Heavy"],
        "connectivity": ["Bluetooth", "Wi-Fi", "USB-C", "Lightning", "HDMI"],
        "battery_life": ["8 hours", "10 hours", "12 hours", "15 hours", "24 hours"],
        "storage": ["64GB", "128GB", "256GB", "512GB", "1TB", "2TB"],
        "resolution": ["HD", "Full HD", "2K", "4K", "8K"],
        "screen_size": ["13 inch", "15 inch", "17 inch", "24 inch", "27 inch", "32 inch"]
    },
    "Clothing": {
        "color": ["Black", "White", "Blue", "Red", "Green", "Yellow", "Pink", "Purple", "Gray", "Brown"],
        "size": ["XS", "S", "M", "L", "XL", "XXL"],
        "material": ["Cotton", "Polyester", "Wool", "Linen", "Silk", "Denim", "Leather"],
        "fit": ["Slim", "Regular", "Relaxed", "Loose"],
        "season": ["Spring", "Summer", "Fall", "Winter", "All Season"],
        "pattern": ["Solid", "Striped", "Plaid", "Floral", "Polka Dot", "Graphic"]
    },
    "Home & Kitchen": {
        "color": ["Black", "White", "Silver", "Red", "Blue", "Green", "Yellow", "Brown"],
        "material": ["Stainless Steel", "Plastic", "Glass", "Ceramic", "Wood", "Silicone"],
        "size": ["Small", "Medium", "Large", "Extra Large"],
        "dishwasher_safe": ["Yes", "No"],
        "warranty": ["1 Year", "2 Years", "5 Years", "10 Years", "Lifetime"],
        "power": ["600W", "800W", "1000W", "1200W", "1500W"]
    },
    "Office Supplies": {
        "color": ["Black", "Blue", "Red", "Green", "Yellow", "Assorted"],
        "quantity": ["Single", "Pack of 5", "Pack of 10", "Pack of 20", "Pack of 50", "Pack of 100"],
        "material": ["Plastic", "Metal", "Paper", "Cardboard", "Wood"],
        "size": ["Small", "Medium", "Large", "Standard", "Legal", "Letter"],
        "refillable": ["Yes", "No"]
    },
    "Beauty & Personal Care": {
        "skin_type": ["Normal", "Dry", "Oily", "Combination", "Sensitive"],
        "scent": ["Unscented", "Floral", "Citrus", "Woody", "Fresh", "Sweet"],
        "volume": ["30ml", "50ml", "100ml", "200ml", "250ml", "500ml"],
        "organic": ["Yes", "No"],
        "cruelty_free": ["Yes", "No"],
        "spf": ["SPF 15", "SPF 30", "SPF 50", "SPF 100"]
    }
}

# Adjectives for product names
ADJECTIVES = [
    "Premium", "Deluxe", "Professional", "Ultimate", "Advanced", "Essential",
    "Classic", "Modern", "Compact", "Portable", "Wireless", "Smart", "Ultra",
    "Super", "Eco-friendly", "Luxury", "Budget", "High-end", "Ergonomic", "Durable"
]

def generate_product_name(category, subcategory, brand):
    """Generate a realistic product name."""
    adjective = random.choice(ADJECTIVES)
    model_number = f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(100, 999)}"
    
    # 50% chance to include model number
    if random.random() > 0.5:
        return f"{brand} {adjective} {subcategory} {model_number}"
    else:
        return f"{brand} {adjective} {subcategory}"

def generate_product_description(category, subcategory, attributes):
    """Generate a detailed product description."""
    descriptions = [
        f"This {attributes.get('color', 'versatile')} {subcategory.lower()} is perfect for everyday use.",
        f"Featuring a {random.choice(['sleek', 'modern', 'classic', 'elegant', 'minimalist'])} design.",
        f"Made with {attributes.get('material', 'high-quality materials')} for durability and longevity.",
    ]
    
    # Add category-specific descriptions
    if category == "Electronics":
        descriptions.extend([
            f"Equipped with {attributes.get('connectivity', 'the latest technology')} for seamless connectivity.",
            f"Enjoy up to {attributes.get('battery_life', 'long-lasting')} battery life on a single charge.",
            f"Comes with {attributes.get('storage', 'ample storage')} to store all your important files."
        ])
    elif category == "Clothing":
        descriptions.extend([
            f"Perfect for {attributes.get('season', 'any season')} wear.",
            f"Features a {attributes.get('fit', 'comfortable')} fit for all-day comfort.",
            f"The {attributes.get('pattern', 'stylish')} pattern adds a touch of elegance to your wardrobe."
        ])
    elif category == "Home & Kitchen":
        descriptions.extend([
            f"This {subcategory.lower()} is {attributes.get('dishwasher_safe', 'easy to clean')}.",
            f"Comes with a {attributes.get('warranty', 'manufacturer warranty')} for peace of mind.",
            f"The {attributes.get('size', 'perfect size')} is ideal for any kitchen."
        ])
    elif category == "Office Supplies":
        descriptions.extend([
            f"Comes in a {attributes.get('quantity', 'convenient package')}.",
            f"The {attributes.get('color', 'professional color')} is perfect for office use.",
            f"Designed for {random.choice(['efficiency', 'productivity', 'organization', 'convenience'])}."
        ])
    elif category == "Beauty & Personal Care":
        descriptions.extend([
            f"Suitable for {attributes.get('skin_type', 'all skin types')}.",
            f"The {attributes.get('scent', 'pleasant fragrance')} leaves you feeling refreshed.",
            f"This product is {attributes.get('cruelty_free', 'ethically made')}."
        ])
    
    # Add general closing statements
    descriptions.extend([
        f"An excellent choice for {random.choice(['home', 'office', 'travel', 'everyday', 'professional'])} use.",
        f"Buy now and experience the difference!",
        f"Satisfaction guaranteed or your money back."
    ])
    
    # Shuffle and join descriptions
    random.shuffle(descriptions)
    return " ".join(descriptions[:random.randint(4, 7)])

def generate_price(category, subcategory):
    """Generate a realistic price based on category and subcategory."""
    base_prices = {
        "Electronics": {
            "Smartphones": (299.99, 1299.99),
            "Laptops": (499.99, 2499.99),
            "Tablets": (199.99, 999.99),
            "Monitors": (149.99, 799.99),
            "Headphones": (29.99, 349.99),
            "Speakers": (39.99, 399.99),
            "Cameras": (199.99, 1499.99),
            "Printers": (89.99, 499.99),
            "Smart Home": (29.99, 299.99),
            "Wearables": (49.99, 399.99)
        },
        "Clothing": {
            "Men's Shirts": (19.99, 89.99),
            "Women's Dresses": (29.99, 149.99),
            "Jeans": (39.99, 129.99),
            "Shoes": (49.99, 199.99),
            "Jackets": (59.99, 249.99),
            "Activewear": (24.99, 99.99),
            "Underwear": (9.99, 49.99),
            "Socks": (4.99, 24.99),
            "Hats": (14.99, 39.99),
            "Accessories": (9.99, 79.99)
        },
        "Home & Kitchen": {
            "Cookware": (29.99, 299.99),
            "Appliances": (49.99, 499.99),
            "Furniture": (99.99, 999.99),
            "Bedding": (29.99, 199.99),
            "Bath": (19.99, 99.99),
            "Decor": (14.99, 149.99),
            "Storage": (19.99, 129.99),
            "Cleaning": (9.99, 79.99),
            "Dining": (24.99, 199.99),
            "Lighting": (29.99, 249.99)
        },
        "Office Supplies": {
            "Pens & Pencils": (2.99, 29.99),
            "Notebooks": (4.99, 24.99),
            "Desk Accessories": (9.99, 49.99),
            "Printers & Ink": (19.99, 199.99),
            "Paper": (3.99, 29.99),
            "Binders": (4.99, 19.99),
            "Calendars": (9.99, 24.99),
            "Staplers": (5.99, 29.99),
            "Scissors": (3.99, 19.99),
            "Markers": (2.99, 14.99)
        },
        "Beauty & Personal Care": {
            "Skincare": (9.99, 99.99),
            "Makeup": (7.99, 79.99),
            "Hair Care": (5.99, 49.99),
            "Fragrances": (19.99, 149.99),
            "Oral Care": (3.99, 29.99),
            "Shaving": (7.99, 49.99),
            "Bath & Body": (6.99, 39.99),
            "Nail Care": (4.99, 24.99),
            "Tools & Accessories": (9.99, 59.99),
            "Men's Grooming": (8.99, 69.99)
        }
    }
    
    min_price, max_price = base_prices.get(category, {}).get(subcategory, (9.99, 99.99))
    
    # Generate a price within the range, with common price endings (.99, .95, etc.)
    price = random.uniform(min_price, max_price)
    price = round(price * 0.95, 2) + 0.99  # Apply a slight discount and end with .99
    
    return round(price, 2)

def generate_product_attributes(category, subcategory):
    """Generate realistic attributes for a product based on its category."""
    category_attrs = ATTRIBUTES.get(category, {})
    attributes = {}
    
    # Add 3-5 attributes from the category's attribute list
    for attr_name, attr_values in random.sample(list(category_attrs.items()), min(random.randint(3, 5), len(category_attrs))):
        attributes[attr_name] = random.choice(attr_values)
    
    return attributes

def generate_product_image(product_id, category, subcategory, color=None):
    """
    Generate a simple product image with text and shapes.
    
    Args:
        product_id: Unique product identifier
        category: Product category
        subcategory: Product subcategory
        color: Optional color for the image
        
    Returns:
        dict: Dictionary with image URL and placeholder for vector embedding
    """
    # Create directory for images if it doesn't exist
    image_dir = Path("data/images")
    image_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine image filename
    image_filename = f"product_{product_id}.png"
    image_path = image_dir / image_filename
    
    # Determine background color based on provided color or randomly
    if color and color.lower() in ["black", "white", "blue", "red", "green", "yellow", "pink", "purple", "gray", "brown"]:
        bg_color_map = {
            "black": (30, 30, 30),
            "white": (240, 240, 240),
            "blue": (30, 30, 200),
            "red": (200, 30, 30),
            "green": (30, 200, 30),
            "yellow": (200, 200, 30),
            "pink": (200, 100, 150),
            "purple": (150, 30, 200),
            "gray": (150, 150, 150),
            "brown": (150, 100, 50)
        }
        bg_color = bg_color_map.get(color.lower(), (240, 240, 240))
    else:
        # Random pastel background
        bg_color = (
            random.randint(200, 240),
            random.randint(200, 240),
            random.randint(200, 240)
        )
    
    # Create a new image with a colored background
    img_size = (400, 400)
    img = Image.new('RGB', img_size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw category icon (simple shape based on category)
    icon_size = 150
    icon_pos = ((img_size[0] - icon_size) // 2, (img_size[1] - icon_size) // 2 - 40)
    
    if category == "Electronics":
        # Draw a device shape
        draw.rectangle(
            [icon_pos[0], icon_pos[1], icon_pos[0] + icon_size, icon_pos[1] + icon_size],
            outline=(50, 50, 50),
            width=3
        )
        # Screen
        draw.rectangle(
            [icon_pos[0] + 10, icon_pos[1] + 10, icon_pos[0] + icon_size - 10, icon_pos[1] + icon_size - 40],
            fill=(200, 200, 200)
        )
        # Button
        draw.ellipse(
            [icon_pos[0] + icon_size//2 - 10, icon_pos[1] + icon_size - 30, 
             icon_pos[0] + icon_size//2 + 10, icon_pos[1] + icon_size - 10],
            fill=(50, 50, 50)
        )
    elif category == "Clothing":
        # Draw a t-shirt shape
        # Shoulders
        draw.line(
            [icon_pos[0], icon_pos[1] + 30, 
             icon_pos[0] + icon_size, icon_pos[1] + 30],
            fill=(50, 50, 50),
            width=3
        )
        # Body
        draw.line(
            [icon_pos[0], icon_pos[1] + 30, 
             icon_pos[0], icon_pos[1] + icon_size],
            fill=(50, 50, 50),
            width=3
        )
        draw.line(
            [icon_pos[0] + icon_size, icon_pos[1] + 30, 
             icon_pos[0] + icon_size, icon_pos[1] + icon_size],
            fill=(50, 50, 50),
            width=3
        )
        # Bottom
        draw.arc(
            [icon_pos[0], icon_pos[1] + icon_size - 50, 
             icon_pos[0] + icon_size, icon_pos[1] + icon_size + 50],
            180, 0,
            fill=(50, 50, 50),
            width=3
        )
    elif category == "Home & Kitchen":
        # Draw a house shape
        # Roof
        draw.polygon(
            [icon_pos[0], icon_pos[1] + 60, 
             icon_pos[0] + icon_size//2, icon_pos[1], 
             icon_pos[0] + icon_size, icon_pos[1] + 60],
            fill=(150, 75, 0)
        )
        # House body
        draw.rectangle(
            [icon_pos[0] + 10, icon_pos[1] + 60, 
             icon_pos[0] + icon_size - 10, icon_pos[1] + icon_size],
            fill=(200, 150, 100),
            outline=(50, 50, 50),
            width=2
        )
        # Door
        draw.rectangle(
            [icon_pos[0] + icon_size//2 - 15, icon_pos[1] + 100, 
             icon_pos[0] + icon_size//2 + 15, icon_pos[1] + icon_size],
            fill=(100, 50, 0)
        )
    elif category == "Office Supplies":
        # Draw a pencil shape
        # Pencil body
        draw.rectangle(
            [icon_pos[0] + 20, icon_pos[1], 
             icon_pos[0] + icon_size - 20, icon_pos[1] + icon_size - 40],
            fill=(250, 200, 40),
            outline=(50, 50, 50),
            width=2
        )
        # Pencil tip
        draw.polygon(
            [icon_pos[0] + 20, icon_pos[1] + icon_size - 40, 
             icon_pos[0] + icon_size//2, icon_pos[1] + icon_size, 
             icon_pos[0] + icon_size - 20, icon_pos[1] + icon_size - 40],
            fill=(50, 50, 50)
        )
        # Eraser
        draw.rectangle(
            [icon_pos[0] + 20, icon_pos[1] - 20, 
             icon_pos[0] + icon_size - 20, icon_pos[1]],
            fill=(255, 100, 100),
            outline=(50, 50, 50),
            width=2
        )
    elif category == "Beauty & Personal Care":
        # Draw a bottle shape
        # Bottle neck
        draw.rectangle(
            [icon_pos[0] + icon_size//2 - 10, icon_pos[1], 
             icon_pos[0] + icon_size//2 + 10, icon_pos[1] + 30],
            fill=(200, 200, 200),
            outline=(50, 50, 50),
            width=2
        )
        # Bottle cap
        draw.rectangle(
            [icon_pos[0] + icon_size//2 - 15, icon_pos[1] - 20, 
             icon_pos[0] + icon_size//2 + 15, icon_pos[1]],
            fill=(50, 50, 50)
        )
        # Bottle body
        draw.rectangle(
            [icon_pos[0] + 20, icon_pos[1] + 30, 
             icon_pos[0] + icon_size - 20, icon_pos[1] + icon_size],
            fill=(200, 200, 200),
            outline=(50, 50, 50),
            width=2
        )
    
    # Add text for category and subcategory
    try:
        # Try to use a system font
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
    except IOError:
        # Fall back to default font
        font = ImageFont.load_default()
    
    # Add category text
    draw.text(
        (img_size[0]//2, img_size[1] - 80),
        category,
        fill=(0, 0, 0),
        font=font,
        anchor="mm"
    )
    
    # Add subcategory text
    draw.text(
        (img_size[0]//2, img_size[1] - 40),
        subcategory,
        fill=(0, 0, 0),
        font=font,
        anchor="mm"
    )
    
    # Save the image
    img.save(image_path)
    
    # Return image info
    return {
        "url": f"data/images/{image_filename}"
    }

def generate_mock_embedding(dims):
    """Generate a mock embedding vector of the specified dimension."""
    # Generate random vector
    embedding = np.random.normal(0, 1, dims)
    
    # Normalize to unit length
    embedding = embedding / np.linalg.norm(embedding)
    
    return embedding.tolist()

def generate_products(num_products):
    """
    Generate a synthetic product catalog.
    
    Args:
        num_products: Number of products to generate
        
    Returns:
        list: List of generated products
    """
    logger.info(f"Generating {num_products} synthetic products")
    
    products = []
    
    for i in range(num_products):
        # Select random category and subcategory
        category = random.choice(list(PRODUCT_CATEGORIES.keys()))
        subcategory = random.choice(PRODUCT_CATEGORIES[category])
        
        # Select random brand for the category
        brand = random.choice(BRANDS[category])
        
        # Generate product attributes
        attributes = generate_product_attributes(category, subcategory)
        
        # Generate product ID
        product_id = str(uuid.uuid4())
        
        # Generate product name
        name = generate_product_name(category, subcategory, brand)
        
        # Generate product description
        description = generate_product_description(category, subcategory, attributes)
        
        # Generate price
        price = generate_price(category, subcategory)
        
        # Generate product image
        image = generate_product_image(
            product_id, 
            category, 
            subcategory, 
            color=attributes.get("color")
        )
        

        
        # Create product object
        product = {
            "id": product_id,
            "name": name,
            "description": description,
            "category": category,
            "subcategory": subcategory,
            "price": price,
            "brand": brand,
            "attributes": attributes,
            "image": image,
            "created_at": datetime.now().isoformat()
        }
        
        products.append(product)
        
        # Log progress
        if (i + 1) % 50 == 0:
            logger.info(f"Generated {i + 1} products")
    
    logger.info(f"Completed generating {len(products)} products")
    
    # Save products to file
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / "products.json", "w") as f:
        json.dump(products, f, indent=2)
    
    logger.info(f"Saved {len(products)} products to data/products.json")
    return products

if __name__ == "__main__":
    generate_products(NUM_PRODUCTS)
