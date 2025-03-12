"""
Search models for the E-Commerce Search Demo.
"""
from enum import Enum
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field

class SearchType(str, Enum):
    """Enum for different search types."""
    BM25 = "bm25"
    VECTOR = "vector"
    CUSTOMER_SUPPORT = "customer_support"
    IMAGE = "image"

class ProductImage(BaseModel):
    """Product image model."""
    url: str
    vector_embedding: Optional[List[float]] = None

class Product(BaseModel):
    """Product model."""
    id: str
    name: str
    description: str
    category: str
    price: float
    brand: str
    attributes: Dict[str, Any]
    image: ProductImage
    text_embedding: Optional[List[float]] = None

class SearchResult(BaseModel):
    """Search result model."""
    query: str
    product_id: str
    product_name: str
    product_description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    score: float = 1.0
    search_type: SearchType = SearchType.IMAGE
    alternatives: Optional[List[Dict[str, str]]] = None
    explanation: Optional[str] = None
    
    class Config:
        """Pydantic model configuration."""
        from_attributes = True

class BuyerPersona(BaseModel):
    """Buyer persona model."""
    id: str
    name: str
    search_history: List[str] = []
    clickstream: List[str] = []  # Product IDs clicked but not purchased
    purchase_history: List[str] = []  # Product IDs purchased
