#!/usr/bin/env python3
"""
Script to generate synthetic buyer personas for the e-commerce search demo.
"""
import os
import sys
import json
import uuid
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from app
from app.config.settings import NUM_PERSONAS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Persona profiles with preferences
PERSONA_PROFILES = [
    {
        "name": "Tech Enthusiast",
        "preferences": {
            "categories": ["Electronics"],
            "price_range": (200, 2000),
            "brands": ["Apple", "Samsung", "Sony", "Google", "Microsoft"],
            "search_style": "precise",  # Tends to search for specific models
            "purchase_frequency": "medium"  # Makes purchases occasionally
        }
    },
    {
        "name": "Budget Shopper",
        "preferences": {
            "categories": ["Clothing", "Home & Kitchen", "Office Supplies"],
            "price_range": (10, 100),
            "brands": ["H&M", "Ikea", "Amazon Basics", "Target", "Walmart"],
            "search_style": "general",  # Searches for general terms
            "purchase_frequency": "high"  # Makes frequent purchases
        }
    },
    {
        "name": "Luxury Buyer",
        "preferences": {
            "categories": ["Clothing", "Beauty & Personal Care"],
            "price_range": (100, 5000),
            "brands": ["Gucci", "Prada", "Chanel", "Louis Vuitton", "Estee Lauder"],
            "search_style": "descriptive",  # Uses descriptive terms
            "purchase_frequency": "low"  # Makes infrequent but expensive purchases
        }
    },
    {
        "name": "Home Decorator",
        "preferences": {
            "categories": ["Home & Kitchen"],
            "price_range": (50, 500),
            "brands": ["Crate & Barrel", "West Elm", "Pottery Barn", "Wayfair", "IKEA"],
            "search_style": "semantic",  # Uses semantic descriptions
            "purchase_frequency": "medium"  # Makes occasional purchases
        }
    },
    {
        "name": "Office Manager",
        "preferences": {
            "categories": ["Office Supplies", "Electronics"],
            "price_range": (20, 300),
            "brands": ["Staples", "HP", "Dell", "3M", "Brother"],
            "search_style": "precise",  # Searches for specific items
            "purchase_frequency": "high"  # Makes frequent purchases for the office
        }
    },
    {
        "name": "Beauty Enthusiast",
        "preferences": {
            "categories": ["Beauty & Personal Care"],
            "price_range": (15, 200),
            "brands": ["Sephora", "L'Oreal", "MAC", "Fenty Beauty", "Glossier"],
            "search_style": "descriptive",  # Uses descriptive terms
            "purchase_frequency": "high"  # Makes frequent purchases
        }
    },
    {
        "name": "Parent Shopper",
        "preferences": {
            "categories": ["Clothing", "Home & Kitchen", "Office Supplies"],
            "price_range": (10, 150),
            "brands": ["Target", "Old Navy", "Gap", "Amazon Basics", "Walmart"],
            "search_style": "general",  # Searches for general terms
            "purchase_frequency": "high"  # Makes frequent purchases
        }
    }
]

# Search query templates by search style
SEARCH_QUERIES = {
    "precise": [
        "{brand} {product_name} {model}",
        "{product_name} {model} {attribute}",
        "{brand} {product_name} {attribute}",
        "{product_name} for {specific_use}",
        "{brand} {product_name} {size} {color}"
    ],
    "general": [
        "best {product_category}",
        "affordable {product_name}",
        "{product_name} under ${max_price}",
        "{product_name} for {general_use}",
        "{color} {product_name}"
    ],
    "descriptive": [
        "{adjective} {product_name} for {specific_use}",
        "high quality {product_name}",
        "{product_name} with {feature}",
        "{style} {product_name} {color}",
        "premium {product_name} {attribute}"
    ],
    "semantic": [
        "something to {action} with",
        "{product_name} that {benefit}",
        "{product_name} for {situation}",
        "best way to {action}",
        "{product_name} similar to {reference_product}"
    ]
}

# Product-related terms for search query generation
PRODUCT_TERMS = {
    "Electronics": {
        "product_names": ["laptop", "smartphone", "headphones", "tablet", "monitor", "camera", "printer", "speaker", "smartwatch", "TV"],
        "models": ["Pro", "Air", "Ultra", "Max", "Plus", "Elite", "X1", "G5", "Z10", "S21"],
        "attributes": ["wireless", "bluetooth", "4K", "HD", "OLED", "touchscreen", "portable", "noise-cancelling", "waterproof", "fast-charging"],
        "specific_uses": ["gaming", "video editing", "photography", "streaming", "work from home", "travel", "music production", "graphic design", "programming", "presentations"],
        "features": ["long battery life", "high resolution", "fast processor", "large storage", "compact design", "voice control", "fingerprint sensor", "facial recognition", "surround sound", "high refresh rate"]
    },
    "Clothing": {
        "product_names": ["shirt", "dress", "jeans", "jacket", "shoes", "sweater", "pants", "skirt", "coat", "socks"],
        "attributes": ["cotton", "leather", "denim", "wool", "silk", "slim-fit", "oversized", "waterproof", "breathable", "stretchy"],
        "colors": ["black", "white", "blue", "red", "green", "gray", "navy", "beige", "pink", "purple"],
        "styles": ["casual", "formal", "business", "athletic", "vintage", "modern", "bohemian", "minimalist", "streetwear", "classic"],
        "sizes": ["small", "medium", "large", "XL", "XXL", "petite", "plus size", "tall", "regular", "custom"]
    },
    "Home & Kitchen": {
        "product_names": ["blender", "coffee maker", "toaster", "cookware set", "knife set", "cutting board", "mixing bowl", "food processor", "air fryer", "microwave"],
        "attributes": ["stainless steel", "non-stick", "dishwasher safe", "BPA-free", "ceramic", "glass", "silicone", "wooden", "cast iron", "copper"],
        "specific_uses": ["baking", "cooking", "food prep", "entertaining", "storage", "organization", "cleaning", "decoration", "dining", "serving"],
        "features": ["easy to clean", "durable", "space-saving", "multifunctional", "energy efficient", "programmable", "adjustable", "portable", "quiet operation", "high capacity"]
    },
    "Office Supplies": {
        "product_names": ["pen", "notebook", "stapler", "desk organizer", "printer paper", "binder", "calendar", "whiteboard", "desk lamp", "file cabinet"],
        "attributes": ["refillable", "recycled", "heavy-duty", "compact", "wireless", "rechargeable", "adjustable", "portable", "ergonomic", "magnetic"],
        "specific_uses": ["note-taking", "organizing", "planning", "filing", "presenting", "writing", "drawing", "sketching", "labeling", "highlighting"],
        "features": ["smooth writing", "durable binding", "easy storage", "quick access", "long-lasting", "smudge-proof", "tear-resistant", "water-resistant", "archival quality", "eco-friendly"]
    },
    "Beauty & Personal Care": {
        "product_names": ["moisturizer", "shampoo", "conditioner", "face wash", "lipstick", "foundation", "mascara", "perfume", "sunscreen", "body lotion"],
        "attributes": ["organic", "vegan", "cruelty-free", "fragrance-free", "hypoallergenic", "dermatologist-tested", "oil-free", "non-comedogenic", "paraben-free", "sulfate-free"],
        "specific_uses": ["dry skin", "oily skin", "sensitive skin", "anti-aging", "acne-prone skin", "color correction", "hydration", "exfoliation", "sun protection", "hair styling"],
        "features": ["long-lasting", "quick-absorbing", "lightweight", "full coverage", "natural finish", "deep cleansing", "moisturizing", "volumizing", "color-safe", "UV protection"]
    }
}

# General terms for search query generation
GENERAL_TERMS = {
    "adjectives": ["best", "top", "premium", "affordable", "high-quality", "durable", "reliable", "stylish", "comfortable", "innovative"],
    "actions": ["clean", "organize", "cook", "work", "relax", "exercise", "travel", "study", "entertain", "decorate"],
    "benefits": ["saves time", "reduces stress", "improves productivity", "enhances comfort", "lasts longer", "looks better", "feels better", "works faster", "costs less", "saves space"],
    "situations": ["small apartment", "home office", "outdoor activities", "travel", "daily commute", "special occasions", "everyday use", "professional use", "gift", "emergency"],
    "general_uses": ["home", "office", "travel", "outdoors", "sports", "work", "school", "parties", "everyday", "special occasions"]
}

def load_products():
    """Load generated products from file."""
    products_file = Path("data/products.json")
    
    if not products_file.exists():
        logger.warning("Products file not found. Run generate_products.py first.")
        return []
    
    with open(products_file, "r") as f:
        products = json.load(f)
    
    logger.info(f"Loaded {len(products)} products from file")
    return products

def generate_search_query(persona, products):
    """Generate a realistic search query based on persona preferences."""
    # Get persona preferences
    preferences = persona["preferences"]
    search_style = preferences["search_style"]
    preferred_categories = preferences["categories"]
    
    # Select a random category from persona's preferred categories
    category = random.choice(preferred_categories)
    
    # Get query template based on search style
    query_template = random.choice(SEARCH_QUERIES[search_style])
    
    # Get terms for the selected category
    category_terms = PRODUCT_TERMS.get(category, {})
    
    # Prepare query parameters
    query_params = {}
    
    # Add category-specific terms
    for term_type, terms in category_terms.items():
        if terms:
            query_params[term_type] = random.choice(terms)
    
    # Add general terms
    for term_type, terms in GENERAL_TERMS.items():
        if terms:
            query_params[term_type] = random.choice(terms)
    
    # Add brand from persona preferences
    if preferences["brands"]:
        query_params["brand"] = random.choice(preferences["brands"])
    
    # Add price range
    min_price, max_price = preferences["price_range"]
    query_params["max_price"] = str(random.randint(min_price, max_price))
    
    # Add product category
    query_params["product_category"] = category
    
    # Add reference product (for semantic searches)
    if products:
        reference_product = random.choice([p for p in products if p["category"] == category])
        query_params["reference_product"] = reference_product["name"]
    
    # Format query template with available parameters
    # Only use parameters that are in the template
    available_params = {}
    for key, value in query_params.items():
        if "{" + key + "}" in query_template:
            available_params[key] = value
    
    try:
        query = query_template.format(**available_params)
    except KeyError:
        # Fallback if some parameters are missing
        query = f"{query_params.get('adjective', 'best')} {query_params.get('product_names', category)}"
    
    return query

def generate_search_history(persona, products, num_searches=15):
    """Generate search history for a persona."""
    search_history = []
    
    for _ in range(num_searches):
        search_query = generate_search_query(persona, products)
        search_history.append(search_query)
    
    return search_history

def generate_clickstream(persona, products, num_clicks=20):
    """Generate clickstream (products clicked but not purchased) for a persona."""
    preferences = persona["preferences"]
    preferred_categories = preferences["categories"]
    min_price, max_price = preferences["price_range"]
    preferred_brands = preferences["brands"]
    
    # Filter products based on persona preferences
    matching_products = [
        p for p in products
        if p["category"] in preferred_categories
        and min_price <= p["price"] <= max_price
    ]
    
    # If no exact matches, use all products
    if not matching_products:
        matching_products = products
    
    # Select random products for clickstream
    clickstream = []
    for _ in range(min(num_clicks, len(matching_products))):
        product = random.choice(matching_products)
        clickstream.append(product["id"])
        # Remove product to avoid duplicates
        matching_products.remove(product)
    
    return clickstream

def generate_purchase_history(persona, products, clickstream, num_purchases=10):
    """Generate purchase history for a persona."""
    preferences = persona["preferences"]
    purchase_frequency = preferences["purchase_frequency"]
    
    # Adjust number of purchases based on frequency
    if purchase_frequency == "low":
        num_purchases = max(1, num_purchases // 3)
    elif purchase_frequency == "high":
        num_purchases = num_purchases * 2
    
    # Select some products from clickstream (items viewed and then purchased)
    purchase_history = []
    clickstream_copy = clickstream.copy()
    
    # 60% of purchases come from clickstream (if available)
    clickstream_purchases = min(int(num_purchases * 0.6), len(clickstream_copy))
    for _ in range(clickstream_purchases):
        if clickstream_copy:
            product_id = random.choice(clickstream_copy)
            purchase_history.append(product_id)
            clickstream_copy.remove(product_id)
    
    # Remaining purchases are random based on preferences
    preferences = persona["preferences"]
    preferred_categories = preferences["categories"]
    min_price, max_price = preferences["price_range"]
    preferred_brands = preferences["brands"]
    
    # Filter products based on persona preferences
    matching_products = [
        p for p in products
        if p["category"] in preferred_categories
        and min_price <= p["price"] <= max_price
        and p["id"] not in purchase_history  # Avoid duplicates
    ]
    
    # If no exact matches, use all products
    if not matching_products:
        matching_products = [p for p in products if p["id"] not in purchase_history]
    
    # Add remaining random purchases
    remaining_purchases = num_purchases - len(purchase_history)
    for _ in range(min(remaining_purchases, len(matching_products))):
        product = random.choice(matching_products)
        purchase_history.append(product["id"])
        # Remove product to avoid duplicates
        matching_products.remove(product)
    
    return purchase_history

def generate_personas(num_personas):
    """
    Generate synthetic buyer personas.
    
    Args:
        num_personas: Number of personas to generate
        
    Returns:
        list: List of generated buyer personas
    """
    logger.info(f"Generating {num_personas} synthetic buyer personas")
    
    # Load products
    products = load_products()
    
    if not products:
        logger.error("No products available. Run generate_products.py first.")
        return []
    
    # Select persona profiles to use
    selected_profiles = random.sample(PERSONA_PROFILES, min(num_personas, len(PERSONA_PROFILES)))
    
    # Generate personas
    personas = []
    
    for i, profile in enumerate(selected_profiles):
        # Generate persona ID
        persona_id = str(uuid.uuid4())
        
        # Generate search history
        search_history = generate_search_history(profile, products)
        
        # Generate clickstream
        clickstream = generate_clickstream(profile, products)
        
        # Generate purchase history
        purchase_history = generate_purchase_history(profile, products, clickstream)
        
        # Create persona object
        persona = {
            "id": persona_id,
            "name": profile["name"],
            "preferences": profile["preferences"],
            "search_history": search_history,
            "clickstream": clickstream,
            "purchase_history": purchase_history,
            "created_at": datetime.now().isoformat()
        }
        
        personas.append(persona)
        
        logger.info(f"Generated persona: {profile['name']}")
    
    # Save personas to file
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / "personas.json", "w") as f:
        json.dump(personas, f, indent=2)
    
    logger.info(f"Saved {len(personas)} personas to data/personas.json")
    return personas

if __name__ == "__main__":
    generate_personas(NUM_PERSONAS)
