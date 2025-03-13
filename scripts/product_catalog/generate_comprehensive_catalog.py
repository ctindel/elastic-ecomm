#!/usr/bin/env python3
"""
Generate a comprehensive product catalog for the e-commerce search demo
This script generates a diverse product catalog with specific examples
"""
import os
import sys
import json
import uuid
import random
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define product categories
PRODUCT_CATEGORIES = [
    "Electronics",
    "Computers",
    "Home & Kitchen",
    "Clothing",
    "Beauty & Personal Care",
    "Health & Household",
    "Office Products",
    "Toys & Games",
    "Sports & Outdoors",
    "Automotive",
    "Books",
    "Movies & TV",
    "Music",
    "Pet Supplies",
    "Baby",
    "Industrial & Scientific",
    "Grocery",
    "Tools & Home Improvement",
    "Garden & Outdoor",
    "Appliances"
]

# Define specific product examples
SPECIFIC_EXAMPLES = [
    {
        "category": "Health & Household",
        "subcategory": "Household Supplies",
        "products": [
            {
                "name": "EcoClean Laundry Detergent",
                "description": "Eco-friendly laundry detergent with plant-based ingredients. Removes tough stains while being gentle on fabrics and the environment.",
                "brand": "EcoClean",
                "price": 12.99,
                "attributes": {
                    "size": "64 oz",
                    "scent": "Fresh Linen",
                    "form": "Liquid",
                    "eco_friendly": True
                }
            },
            {
                "name": "BrightWash Heavy Duty Laundry Detergent",
                "description": "Industrial strength laundry detergent for the toughest stains. Perfect for work clothes and heavily soiled items.",
                "brand": "BrightWash",
                "price": 15.99,
                "attributes": {
                    "size": "96 oz",
                    "scent": "Original",
                    "form": "Liquid",
                    "eco_friendly": False
                }
            },
            {
                "name": "NaturePure Organic Hand Soap",
                "description": "Gentle hand soap made with organic ingredients. Moisturizes while cleaning for soft, healthy hands.",
                "brand": "NaturePure",
                "price": 6.99,
                "attributes": {
                    "size": "12 oz",
                    "scent": "Lavender",
                    "form": "Liquid",
                    "eco_friendly": True
                }
            },
            {
                "name": "CleanGuard Antibacterial Hand Soap",
                "description": "Kills 99.9% of germs while leaving hands feeling soft and clean. Dermatologist tested formula.",
                "brand": "CleanGuard",
                "price": 4.99,
                "attributes": {
                    "size": "8 oz",
                    "scent": "Citrus",
                    "form": "Foam",
                    "eco_friendly": False
                }
            }
        ]
    },
    {
        "category": "Office Products",
        "subcategory": "School Supplies",
        "products": [
            {
                "name": "ColorBright Colored Pencils Set",
                "description": "Premium colored pencils for students and artists. Vibrant colors and smooth application for all your creative projects.",
                "brand": "ColorBright",
                "price": 8.99,
                "attributes": {
                    "count": 24,
                    "type": "Colored Pencils",
                    "age_range": "6+"
                }
            },
            {
                "name": "SchoolPro Composition Notebook",
                "description": "College-ruled composition notebook with durable binding. Perfect for notes, journaling, and assignments.",
                "brand": "SchoolPro",
                "price": 3.49,
                "attributes": {
                    "pages": 100,
                    "type": "Composition Notebook",
                    "ruling": "College-ruled"
                }
            },
            {
                "name": "KidsSafe Blunt Tip Scissors",
                "description": "Safe scissors for young children with blunt tips and easy grip handles. Perfect for classroom and home use.",
                "brand": "KidsSafe",
                "price": 2.99,
                "attributes": {
                    "size": "5 inch",
                    "type": "Scissors",
                    "age_range": "3-8"
                }
            },
            {
                "name": "StudyMaster Backpack",
                "description": "Durable backpack with multiple compartments for books, supplies, and electronics. Padded straps for comfort.",
                "brand": "StudyMaster",
                "price": 29.99,
                "attributes": {
                    "capacity": "30L",
                    "type": "Backpack",
                    "color": "Navy Blue"
                }
            }
        ]
    },
    {
        "category": "Computers",
        "subcategory": "Monitors",
        "products": [
            {
                "name": "DesignPro 27-inch 4K Monitor",
                "description": "Professional-grade monitor for graphic designers with 99% Adobe RGB color accuracy. Perfect for photo and video editing.",
                "brand": "DesignPro",
                "price": 499.99,
                "attributes": {
                    "size": "27 inch",
                    "resolution": "4K (3840x2160)",
                    "panel_type": "IPS",
                    "refresh_rate": "60Hz"
                }
            },
            {
                "name": "GameMaster 32-inch Curved Gaming Monitor",
                "description": "Immersive curved gaming monitor with 144Hz refresh rate and 1ms response time. G-Sync compatible for smooth gameplay.",
                "brand": "GameMaster",
                "price": 349.99,
                "attributes": {
                    "size": "32 inch",
                    "resolution": "2K (2560x1440)",
                    "panel_type": "VA",
                    "refresh_rate": "144Hz"
                }
            },
            {
                "name": "OfficePro 24-inch Anti-Glare Monitor",
                "description": "Office monitor with anti-glare coating to reduce eye strain during long work hours. Flicker-free technology for comfortable viewing.",
                "brand": "OfficePro",
                "price": 199.99,
                "attributes": {
                    "size": "24 inch",
                    "resolution": "Full HD (1920x1080)",
                    "panel_type": "IPS",
                    "refresh_rate": "75Hz"
                }
            },
            {
                "name": "ScreenGuard Anti-Glare Screen Protector",
                "description": "Universal anti-glare screen protector for monitors up to 27 inches. Reduces reflections and protects your screen from scratches.",
                "brand": "ScreenGuard",
                "price": 24.99,
                "attributes": {
                    "size": "27 inch",
                    "type": "Screen Protector",
                    "material": "Anti-glare Film"
                }
            }
        ]
    }
]

def generate_random_product(category, index):
    """
    Generate a random product
    
    Args:
        category: Product category
        index: Product index
    
    Returns:
        dict: Product data
    """
    # Generate product ID
    product_id = f"PROD-{index:06d}"
    
    # Generate product name
    adjectives = ["Premium", "Deluxe", "Ultra", "Super", "Pro", "Elite", "Advanced", "Essential", "Classic", "Modern"]
    nouns = ["Widget", "Gadget", "Tool", "Device", "System", "Solution", "Kit", "Set", "Pack", "Bundle"]
    
    name = f"{random.choice(adjectives)} {random.choice(nouns)} {random.randint(100, 999)}"
    
    # Generate product description
    features = [
        "High quality materials",
        "Durable construction",
        "Easy to use",
        "Versatile design",
        "Compact and portable",
        "Energy efficient",
        "Ergonomic design",
        "Advanced technology",
        "Innovative features",
        "User-friendly interface"
    ]
    
    description = f"{name} - {random.choice(features)}. {random.choice(features)}. Perfect for {random.choice(['home', 'office', 'travel', 'outdoor', 'everyday'])} use."
    
    # Generate product brand
    brands = ["TechPro", "HomeStyle", "EcoLife", "ProGear", "SmartTech", "NatureCo", "InnovatePro", "PrimeBrand", "EliteTech", "EssentialGoods"]
    
    # Generate product price
    price = round(random.uniform(9.99, 499.99), 2)
    
    # Generate product attributes
    colors = ["Black", "White", "Silver", "Blue", "Red", "Green", "Yellow", "Purple", "Orange", "Gray"]
    materials = ["Plastic", "Metal", "Wood", "Glass", "Fabric", "Leather", "Silicone", "Aluminum", "Stainless Steel", "Ceramic"]
    
    attributes = {
        "color": random.choice(colors),
        "material": random.choice(materials),
        "weight": round(random.uniform(0.1, 10.0), 2),
        "dimensions": f"{random.randint(1, 50)}x{random.randint(1, 50)}x{random.randint(1, 50)} cm"
    }
    
    # Generate product image
    image = {
        "url": f"https://example.com/images/{product_id}.jpg",
        "alt_text": name
    }
    
    # Create product
    product = {
        "id": product_id,
        "name": name,
        "description": description,
        "category": category,
        "subcategory": random.choice(["Standard", "Premium", "Budget", "Professional", "Basic"]),
        "brand": random.choice(brands),
        "price": price,
        "currency": "USD",
        "availability": random.choice(["In Stock", "Out of Stock", "Pre-order"]),
        "rating": round(random.uniform(3.0, 5.0), 1),
        "review_count": random.randint(0, 1000),
        "attributes": attributes,
        "image": image,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return product

def generate_product_catalog(num_products=5000, output_file="data/products.json"):
    """
    Generate a product catalog
    
    Args:
        num_products: Number of products to generate
        output_file: Output file for the product catalog
    
    Returns:
        list: Product catalog
    """
    try:
        logger.info(f"Generating {num_products} products")
        
        # Create data directory if it doesn't exist
        data_dir = os.path.dirname(output_file)
        os.makedirs(data_dir, exist_ok=True)
        
        # Generate products
        products = []
        
        # Add specific examples first
        specific_product_count = 0
        for example in SPECIFIC_EXAMPLES:
            for product in example["products"]:
                # Generate product ID
                product_id = f"PROD-{specific_product_count + 1:06d}"
                
                # Add product ID and other required fields
                product["id"] = product_id
                product["category"] = example["category"]
                product["subcategory"] = example["subcategory"]
                product["currency"] = "USD"
                product["availability"] = "In Stock"
                product["rating"] = round(random.uniform(4.0, 5.0), 1)
                product["review_count"] = random.randint(10, 1000)
                
                # Add image
                product["image"] = {
                    "url": f"https://example.com/images/{product_id}.jpg",
                    "alt_text": product["name"]
                }
                
                # Add timestamps
                product["created_at"] = datetime.now().isoformat()
                product["updated_at"] = datetime.now().isoformat()
                
                # Add product to catalog
                products.append(product)
                specific_product_count += 1
        
        logger.info(f"Added {specific_product_count} specific examples")
        
        # Generate random products for the rest
        for i in range(specific_product_count, num_products):
            # Select random category
            category = random.choice(PRODUCT_CATEGORIES)
            
            # Generate product
            product = generate_random_product(category, i + 1)
            
            # Add product to catalog
            products.append(product)
            
            # Log progress
            if (i + 1) % 1000 == 0:
                logger.info(f"Generated {i + 1}/{num_products} products")
        
        # Save product catalog
        with open(output_file, "w") as f:
            json.dump(products, f, indent=2)
        
        logger.info(f"Saved product catalog to {output_file}")
        
        return products
    
    except Exception as e:
        logger.error(f"Error generating product catalog: {str(e)}")
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate a product catalog")
    parser.add_argument("--num-products", type=int, default=5000, help="Number of products to generate")
    parser.add_argument("--output-file", default="data/products.json", help="Output file for the product catalog")
    args = parser.parse_args()
    
    # Generate product catalog
    generate_product_catalog(args.num_products, args.output_file)

if __name__ == "__main__":
    main()
