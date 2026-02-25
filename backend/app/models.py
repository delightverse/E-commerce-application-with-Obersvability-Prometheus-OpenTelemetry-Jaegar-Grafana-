"""
Database Models
===============

Defines the database schema using SQLAlchemy ORM.

Tables:
- products: Items for sale
- orders: Customer orders
- order_items: Products in each order (junction table)

Key SQLAlchemy Concepts:
- Column: A field in the table
- relationship(): Links tables together (foreign keys)
- back_populates: Two-way relationship
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# ============================================================================
# PRODUCT MODEL
# ============================================================================

class Product(Base):
    """
    Products available for purchase.
    
    Attributes:
        id: Primary key
        name: Product name (max 200 chars)
        description: Detailed description
        price: Price in USD
        stock: Available quantity
        created_at: Timestamp when product was added
        updated_at: Timestamp when product was last modified
        
    Relationships:
        order_items: All order items containing this product
    """
    __tablename__ = "products"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Product information
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    
    # Timestamps (auto-managed)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to order items
    order_items = relationship("OrderItem", back_populates="product")


# ============================================================================
# ORDER MODEL
# ============================================================================

class Order(Base):
    """
    Customer orders.
    
    Attributes:
        id: Primary key
        user_id: Customer identifier (simplified - no user table yet)
        total_amount: Total order value in USD
        status: Order status (pending, completed, cancelled)
        created_at: When order was placed
        
    Relationships:
        items: All items in this order
    """
    __tablename__ = "orders"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Order information
    user_id = Column(Integer, nullable=False, index=True)  # Simplified (no FK for now)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to order items
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


# ============================================================================
# ORDER ITEM MODEL (Junction Table)
# ============================================================================

class OrderItem(Base):
    """
    Individual items within an order (junction table).
    
    This creates a many-to-many relationship:
    - One order can have many products
    - One product can be in many orders
    
    Attributes:
        id: Primary key
        order_id: Foreign key to orders table
        product_id: Foreign key to products table
        quantity: Number of units ordered
        price_at_purchase: Price when order was placed (historical record)
        
    Relationships:
        order: The order this item belongs to
        product: The product being ordered
    """
    __tablename__ = "order_items"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Item details
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)  # Store historical price
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# ============================================================================
# RELATIONSHIP EXPLANATION
# ============================================================================
# 
# Product ←→ OrderItem ←→ Order
# 
# Example:
# - Order #1: 2x iPhone ($999 each), 1x AirPods ($199)
#   Order.items = [OrderItem(product=iPhone, qty=2), OrderItem(product=AirPods, qty=1)]
# 
# - iPhone appears in multiple orders:
#   Product(iPhone).order_items = [OrderItem(order=1), OrderItem(order=5), ...]
# 
# back_populates creates bidirectional relationships:
# - order.items → list of OrderItems
# - order_item.order → the Order object
# 
# ============================================================================
