#!/usr/bin/env python3
"""
Generate a large product catalog with thousands of diverse products
"""
import os
import sys
import json
import random
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Product categories and subcategories
CATEGORIES = {
    "Electronics": [
        "Computers", "Laptops", "Desktops", "Monitors", "Tablets", 
        "Smartphones", "Accessories", "Audio", "Cameras", "TVs",
        "Gaming", "Networking", "Printers", "Storage"
    ],
    "Home & Kitchen": [
        "Appliances", "Cookware", "Bakeware", "Kitchen Utensils", 
        "Dining", "Furniture", "Bedding", "Bath", "Cleaning", 
        "Decor", "Storage & Organization", "Lighting"
    ],
    "Clothing": [
        "Men's", "Women's", "Children's", "Shoes", "Activewear", 
        "Outerwear", "Underwear", "Accessories", "Jewelry", "Watches"
    ],
    "Beauty & Personal Care": [
        "Skincare", "Haircare", "Makeup", "Fragrances", "Bath & Body", 
        "Oral Care", "Shaving", "Health Care", "Personal Hygiene"
    ],
    "Office & School Supplies": [
        "Writing Instruments", "Paper Products", "Binders & Folders", 
        "School Supplies", "Art Supplies", "Office Furniture", 
        "Office Electronics", "Calendars & Planners"
    ],
    "Toys & Games": [
        "Action Figures", "Dolls", "Building Toys", "Games", "Puzzles", 
        "Educational Toys", "Outdoor Play", "Stuffed Animals", "Vehicles"
    ],
    "Sports & Outdoors": [
        "Exercise & Fitness", "Team Sports", "Outdoor Recreation", 
        "Camping & Hiking", "Cycling", "Water Sports", "Winter Sports", 
        "Fan Shop"
    ],
    "Grocery": [
        "Beverages", "Breakfast", "Canned Goods", "Condiments & Sauces", 
        "Snacks", "Baking", "Dairy", "Meat & Seafood", "Produce", 
        "Frozen Foods", "Household Essentials"
    ],
    "Pet Supplies": [
        "Dogs", "Cats", "Fish", "Birds", "Small Animals", "Reptiles", 
        "Pet Food", "Pet Toys", "Pet Beds", "Pet Grooming"
    ],
    "Automotive": [
        "Parts & Accessories", "Tools & Equipment", "Car Care", 
        "Electronics", "Tires & Wheels", "Motorcycle", "RV", "Oils & Fluids"
    ]
}

# Brands by category
BRANDS = {
    "Electronics": [
        "Apple", "Samsung", "Sony", "LG", "Dell", "HP", "Lenovo", "Asus", 
        "Acer", "Microsoft", "Logitech", "Canon", "Nikon", "Bose", 
        "JBL", "Philips", "Panasonic", "Toshiba", "Sharp", "Epson", 
        "Brother", "Western Digital", "SanDisk", "Seagate", "Intel", 
        "AMD", "Nvidia", "Corsair", "Razer", "HyperX"
    ],
    "Home & Kitchen": [
        "KitchenAid", "Cuisinart", "Instant Pot", "Ninja", "Calphalon", 
        "OXO", "Pyrex", "Corelle", "Rubbermaid", "Tupperware", 
        "Keurig", "Hamilton Beach", "Breville", "Dyson", "Shark", 
        "Bissell", "iRobot", "Whirlpool", "GE", "Maytag", 
        "Frigidaire", "Bosch", "IKEA", "Wayfair", "Ashley Furniture"
    ],
    "Clothing": [
        "Nike", "Adidas", "Under Armour", "Levi's", "Gap", "H&M", 
        "Zara", "Calvin Klein", "Ralph Lauren", "Tommy Hilfiger", 
        "North Face", "Columbia", "Patagonia", "Hanes", "Fruit of the Loom", 
        "Champion", "New Balance", "Puma", "Reebok", "Vans", 
        "Converse", "Timberland", "Dr. Martens", "Crocs", "Skechers"
    ],
    "Beauty & Personal Care": [
        "L'Oreal", "Maybelline", "Revlon", "CoverGirl", "Neutrogena", 
        "Olay", "Dove", "Pantene", "Head & Shoulders", "Garnier", 
        "Nivea", "Aveeno", "Cetaphil", "Eucerin", "Burt's Bees", 
        "Colgate", "Crest", "Oral-B", "Gillette", "Schick", 
        "Degree", "Secret", "Old Spice", "Axe", "Dove Men+Care"
    ],
    "Office & School Supplies": [
        "Staples", "Office Depot", "3M", "Sharpie", "Paper Mate", 
        "Pilot", "BIC", "Pentel", "Faber-Castell", "Crayola", 
        "Avery", "Mead", "Five Star", "Post-it", "Scotch", 
        "HP", "Canon", "Epson", "Brother", "Xerox"
    ],
    "Toys & Games": [
        "LEGO", "Hasbro", "Mattel", "Fisher-Price", "Melissa & Doug", 
        "Playmobil", "Nerf", "Hot Wheels", "Barbie", "Play-Doh", 
        "Disney", "Marvel", "Star Wars", "Nintendo", "PlayStation", 
        "Xbox", "Ravensburger", "Crayola", "VTech", "LeapFrog"
    ],
    "Sports & Outdoors": [
        "Nike", "Adidas", "Under Armour", "Wilson", "Spalding", 
        "Callaway", "TaylorMade", "Coleman", "The North Face", "Columbia", 
        "Patagonia", "REI", "Yeti", "CamelBak", "Schwinn", 
        "Trek", "Speedo", "Titleist", "Rawlings", "Louisville Slugger"
    ],
    "Grocery": [
        "Kraft", "Heinz", "Kellogg's", "General Mills", "Nestle", 
        "Coca-Cola", "Pepsi", "Frito-Lay", "Nabisco", "Hershey's", 
        "Mars", "Campbell's", "Progresso", "Del Monte", "Dole", 
        "Quaker", "Pillsbury", "Betty Crocker", "McCormick", "Folgers"
    ],
    "Pet Supplies": [
        "Purina", "Pedigree", "Royal Canin", "Hill's Science Diet", "Blue Buffalo", 
        "Iams", "Eukanuba", "Friskies", "Fancy Feast", "Whiskas", 
        "Kong", "Nylabone", "PetSafe", "Petmate", "Hartz", 
        "Tetra", "API", "Fluval", "Kaytee", "Oxbow"
    ],
    "Automotive": [
        "Bosch", "Michelin", "Goodyear", "Bridgestone", "Continental", 
        "Mobil", "Castrol", "Valvoline", "Pennzoil", "Shell", 
        "Armor All", "Turtle Wax", "Rain-X", "STP", "WD-40", 
        "3M", "Stanley", "DeWalt", "Craftsman", "Black+Decker"
    ]
}

# Specific product examples requested by the user
SPECIFIC_PRODUCTS = [
    {
        "category": "Home & Kitchen",
        "subcategory": "Cleaning",
        "name": "Premium Laundry Detergent",
        "description": "High-efficiency laundry detergent for all washing machines. Removes tough stains and leaves clothes fresh and clean.",
        "brand": "Tide",
        "price": 19.99,
        "attributes": {
            "size": "100 oz",
            "scent": "Fresh Linen",
            "form": "Liquid"
        }
    },
    {
        "category": "Beauty & Personal Care",
        "subcategory": "Personal Hygiene",
        "name": "Moisturizing Hand Soap",
        "description": "Gentle hand soap with moisturizing ingredients to keep hands soft and clean. Kills 99.9% of germs.",
        "brand": "Dove",
        "price": 4.99,
        "attributes": {
            "size": "7.5 oz",
            "scent": "Cucumber & Mint",
            "form": "Liquid"
        }
    },
    {
        "category": "Office & School Supplies",
        "subcategory": "School Supplies",
        "name": "Elementary School Supply Kit",
        "description": "Complete school supply kit for elementary students. Includes pencils, erasers, crayons, scissors, and more.",
        "brand": "Crayola",
        "price": 24.99,
        "attributes": {
            "grade_level": "K-5",
            "pieces": "42",
            "case_included": "Yes"
        }
    },
    {
        "category": "Electronics",
        "subcategory": "Monitors",
        "name": "27-inch 4K UHD Computer Monitor",
        "description": "Professional-grade 4K monitor with IPS panel for accurate colors and wide viewing angles. Perfect for graphic design and video editing.",
        "brand": "Dell",
        "price": 349.99,
        "attributes": {
            "resolution": "3840x2160",
            "refresh_rate": "60Hz",
            "panel_type": "IPS",
            "connectivity": "HDMI, DisplayPort, USB-C"
        }
    },
    {
        "category": "Electronics",
        "subcategory": "Accessories",
        "name": "Anti-Glare Screen Protector for Monitors",
        "description": "Reduces eye strain and eliminates glare from your computer monitor. Easy to apply and remove without leaving residue.",
        "brand": "3M",
        "price": 29.99,
        "attributes": {
            "size": "24-27 inch",
            "material": "Anti-reflective film",
            "blue_light_reduction": "Yes"
        }
    }
]

def generate_product_id(index: int) -> str:
    """Generate a product ID"""
    return f"PROD-{index:06d}"

def generate_random_product(index: int) -> Dict[str, Any]:
    """Generate a random product"""
    # Select a random category
    category = random.choice(list(CATEGORIES.keys()))
    subcategory = random.choice(CATEGORIES[category])
    brand = random.choice(BRANDS.get(category, BRANDS["Electronics"]))
    
    # Generate a product name
    adjectives = ["Premium", "Deluxe", "Professional", "Advanced", "Essential", "Classic", "Ultra", "Super", "Compact", "Portable"]
    descriptors = ["High-Performance", "Lightweight", "Durable", "Wireless", "Smart", "Digital", "Ergonomic", "Eco-Friendly", "All-Purpose", "Heavy-Duty"]
    
    name_parts = []
    if random.random() < 0.3:
        name_parts.append(random.choice(adjectives))
    if random.random() < 0.3:
        name_parts.append(random.choice(descriptors))
    
    name_parts.append(f"{subcategory[:-1] if subcategory.endswith('s') else subcategory}")
    
    # Add model number for electronics
    if category == "Electronics" and random.random() < 0.7:
        model_series = random.choice(["X", "Pro", "Plus", "Max", "Elite", "Ultra", "S", "Z"])
        model_number = random.randint(1, 9999)
        name_parts.append(f"{model_series}{model_number}")
    
    name = " ".join(name_parts)
    
    # Generate a product description
    features = [
        "High-quality materials",
        "Durable construction",
        "Easy to use",
        "Compact design",
        "Energy efficient",
        "Wireless connectivity",
        "Smart features",
        "Ergonomic design",
        "Eco-friendly",
        "Versatile functionality"
    ]
    
    benefits = [
        "saves time",
        "reduces effort",
        "improves productivity",
        "enhances comfort",
        "increases efficiency",
        "provides convenience",
        "ensures reliability",
        "delivers superior results",
        "offers exceptional value",
        "guarantees satisfaction"
    ]
    
    description_parts = []
    description_parts.append(f"{name} by {brand}.")
    
    # Add 2-3 features
    selected_features = random.sample(features, k=random.randint(2, 3))
    for feature in selected_features:
        description_parts.append(f"{feature} that {random.choice(benefits)}.")
    
    # Add a target audience
    audiences = [
        "Perfect for home use",
        "Ideal for professionals",
        "Great for students",
        "Designed for families",
        "Suitable for office environments",
        "Made for outdoor enthusiasts",
        "Excellent for beginners",
        "Crafted for experts",
        "Built for everyday use",
        "Created for special occasions"
    ]
    
    description_parts.append(random.choice(audiences) + ".")
    
    description = " ".join(description_parts)
    
    # Generate price
    price_ranges = {
        "Electronics": (50, 1500),
        "Home & Kitchen": (20, 500),
        "Clothing": (15, 200),
        "Beauty & Personal Care": (5, 100),
        "Office & School Supplies": (5, 150),
        "Toys & Games": (10, 200),
        "Sports & Outdoors": (20, 500),
        "Grocery": (2, 50),
        "Pet Supplies": (5, 200),
        "Automotive": (10, 300)
    }
    
    price_range = price_ranges.get(category, (10, 200))
    price = round(random.uniform(price_range[0], price_range[1]), 2)
    
    # Generate attributes
    attributes = {}
    
    # Common attributes
    attributes["color"] = random.choice(["Black", "White", "Silver", "Blue", "Red", "Green", "Gray", "Brown", "Purple", "Pink"])
    
    # Category-specific attributes
    if category == "Electronics":
        attributes["weight"] = f"{round(random.uniform(0.5, 10), 1)} lbs"
        attributes["warranty"] = f"{random.randint(1, 5)} years"
        if subcategory in ["Computers", "Laptops", "Tablets", "Smartphones"]:
            attributes["storage"] = f"{random.choice([64, 128, 256, 512, 1024])} GB"
            attributes["memory"] = f"{random.choice([4, 8, 16, 32])} GB"
            attributes["processor"] = random.choice(["Intel Core i3", "Intel Core i5", "Intel Core i7", "AMD Ryzen 3", "AMD Ryzen 5", "AMD Ryzen 7"])
        elif subcategory in ["Monitors", "TVs"]:
            attributes["screen_size"] = f"{random.choice([24, 27, 32, 43, 50, 55, 65])} inches"
            attributes["resolution"] = random.choice(["1080p", "1440p", "4K", "8K"])
    
    elif category == "Home & Kitchen":
        attributes["material"] = random.choice(["Plastic", "Metal", "Glass", "Ceramic", "Wood", "Silicone", "Stainless Steel"])
        attributes["dimensions"] = f"{random.randint(5, 50)}\" x {random.randint(5, 50)}\" x {random.randint(5, 50)}\""
    
    elif category == "Clothing":
        attributes["size"] = random.choice(["XS", "S", "M", "L", "XL", "XXL"])
        attributes["material"] = random.choice(["Cotton", "Polyester", "Wool", "Linen", "Silk", "Denim", "Leather"])
        attributes["care"] = random.choice(["Machine Wash", "Hand Wash", "Dry Clean Only"])
    
    # Generate rating and review count
    rating = round(random.uniform(3.0, 5.0), 1)
    review_count = random.randint(5, 1000)
    
    # Generate stock status
    stock_status = random.choice(["In Stock", "Low Stock", "Out of Stock", "Back Order"])
    if stock_status == "Low Stock":
        stock_status += f" (Only {random.randint(1, 10)} left)"
    
    # Generate image URL (mock)
    image_url = f"data/images/product_{index:06d}.jpg"
    
    # Create the product object
    product = {
        "id": generate_product_id(index),
        "name": name,
        "description": description,
        "category": category,
        "subcategory": subcategory,
        "price": price,
        "brand": brand,
        "rating": rating,
        "review_count": review_count,
        "stock_status": stock_status,
        "attributes": attributes,
        "image": {
            "url": image_url,
            "alt_text": f"Image of {name}"
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return product

def generate_products(num_products: int, output_file: str) -> None:
    """
    Generate a large product catalog
    
    Args:
        num_products: Number of products to generate
        output_file: Path to the output file
    """
    logger.info(f"Generating {num_products} products...")
    
    # Create the output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate products
    products = []
    
    # Add specific products first
    for i, specific_product in enumerate(SPECIFIC_PRODUCTS):
        product_id = generate_product_id(i + 1)
        product = {
            "id": product_id,
            "name": specific_product["name"],
            "description": specific_product["description"],
            "category": specific_product["category"],
            "subcategory": specific_product["subcategory"],
            "price": specific_product["price"],
            "brand": specific_product["brand"],
            "rating": round(random.uniform(4.0, 5.0), 1),
            "review_count": random.randint(50, 1000),
            "stock_status": "In Stock",
            "attributes": specific_product["attributes"],
            "image": {
                "url": f"data/images/product_{i+1:06d}.jpg",
                "alt_text": f"Image of {specific_product['name']}"
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        products.append(product)
    
    # Generate random products
    for i in range(len(SPECIFIC_PRODUCTS) + 1, num_products + 1):
        product = generate_random_product(i)
        products.append(product)
    
    # Write products to file
    with open(output_file, "w") as f:
        json.dump(products, f, indent=2)
    
    logger.info(f"Generated {len(products)} products and saved to {output_file}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate a large product catalog")
    parser.add_argument("--num-products", type=int, default=5000, help="Number of products to generate")
    parser.add_argument("--output-file", type=str, default="data/products.json", help="Path to the output file")
    args = parser.parse_args()
    
    # Generate products
    generate_products(args.num_products, args.output_file)

if __name__ == "__main__":
    main()
