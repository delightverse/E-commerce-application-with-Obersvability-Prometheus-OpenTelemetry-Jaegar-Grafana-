"""
CRUD Operations
===============

Business logic layer for database operations.

CRUD = Create, Read, Update, Delete

Why separate CRUD from API endpoints?
- Reusability: Same logic for API, CLI, tests
- Separation of concerns: DB logic separate from HTTP logic
- Easier testing: Test business logic without HTTP
- Transaction management: Control commits/rollbacks

Pattern:
def operation_name(db: Session, parameters) -> ReturnType:
    # Database operations
    return result
"""

from sqlalchemy.orm import Session
from app import models, schemas
from typing import List, Optional

# ============================================================================
# PRODUCT CRUD OPERATIONS
# ============================================================================

def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    """
    Retrieve a single product by ID.
    
    Args:
        db: Database session
        product_id: ID of product to retrieve
        
    Returns:
        Product object if found, None otherwise
        
    SQL generated:
        SELECT * FROM products WHERE id = product_id LIMIT 1
    """
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[models.Product]:
    """
    Retrieve list of products with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return
        
    Returns:
        List of Product objects
        
    Pagination example:
        Page 1: skip=0, limit=10   → Products 1-10
        Page 2: skip=10, limit=10  → Products 11-20
        Page 3: skip=20, limit=10  → Products 21-30
        
    SQL generated:
        SELECT * FROM products OFFSET skip LIMIT limit
    """
    return db.query(models.Product).offset(skip).limit(limit).all()


def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
    """
    Create a new product.
    
    Args:
        db: Database session
        product: ProductCreate schema with product data
        
    Returns:
        Created Product object (with id, timestamps)
        
    Process:
        1. Convert Pydantic schema → SQLAlchemy model
        2. Add to session (in-memory)
        3. Commit to database (persist)
        4. Refresh to get DB-generated fields (id, timestamps)
        
    SQL generated:
        INSERT INTO products (name, description, price, stock)
        VALUES (?, ?, ?, ?)
        RETURNING id, created_at, updated_at
    """
    # Convert Pydantic schema to dict, then to SQLAlchemy model
    db_product = models.Product(**product.model_dump())
    
    # Add to session (not saved yet)
    db.add(db_product)
    
    # Commit transaction (save to database)
    db.commit()
    
    # Refresh to get DB-generated fields
    # This makes a SELECT query to get id, created_at, updated_at
    db.refresh(db_product)
    
    return db_product


def update_product(
    db: Session,
    product_id: int,
    product_update: schemas.ProductUpdate
) -> Optional[models.Product]:
    """
    Update an existing product (partial update).
    
    Args:
        db: Database session
        product_id: ID of product to update
        product_update: ProductUpdate schema with fields to update
        
    Returns:
        Updated Product object if found, None otherwise
        
    Process:
        1. Find product by ID
        2. Update only fields that are provided (not None)
        3. Commit changes
        
    Example:
        product_update = {"price": 899.99}  # Only update price
        Other fields (name, stock) remain unchanged
        
    SQL generated:
        UPDATE products
        SET price = ?, updated_at = NOW()
        WHERE id = ?
    """
    # Find product
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    if db_product is None:
        return None
    
    # Update only provided fields
    update_data = product_update.model_dump(exclude_unset=True)
    # exclude_unset=True: Only include fields explicitly set by client
    # Example: {"price": 899} → only price updated
    #          {"price": None} → price not in dict (not updated)
    
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    
    return db_product


def delete_product(db: Session, product_id: int) -> bool:
    """
    Delete a product by ID.
    
    Args:
        db: Database session
        product_id: ID of product to delete
        
    Returns:
        True if deleted, False if not found
        
    Note: 
        If product is in any orders, this may fail due to foreign key constraint.
        In production, consider soft delete (status='deleted') instead.
        
    SQL generated:
        DELETE FROM products WHERE id = ?
    """
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    if db_product is None:
        return False
    
    db.delete(db_product)
    db.commit()
    
    return True


def update_product_stock(db: Session, product_id: int, quantity_change: int) -> Optional[models.Product]:
    """
    Update product stock (for order processing).
    
    Args:
        db: Database session
        product_id: ID of product
        quantity_change: Change in stock (negative for sales, positive for restocks)
        
    Returns:
        Updated Product object if found, None otherwise
        
    Example:
        Sell 2 units: update_product_stock(db, 1, -2)
        Restock 10 units: update_product_stock(db, 1, 10)
        
    SQL generated:
        UPDATE products
        SET stock = stock + quantity_change
        WHERE id = ?
    """
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    if db_product is None:
        return None
    
    db_product.stock += quantity_change
    db.commit()
    db.refresh(db_product)
    
    return db_product


# ============================================================================
# ORDER CRUD OPERATIONS
# ============================================================================

def get_order(db: Session, order_id: int) -> Optional[models.Order]:
    """
    Retrieve a single order by ID (includes items).
    
    Args:
        db: Database session
        order_id: ID of order to retrieve
        
    Returns:
        Order object with nested items, None if not found
        
    SQL generated (2 queries due to relationships):
        SELECT * FROM orders WHERE id = ?
        SELECT * FROM order_items WHERE order_id = ?
    """
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_orders(db: Session, skip: int = 0, limit: int = 100) -> List[models.Order]:
    """
    Retrieve list of orders with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of Order objects
    """
    return db.query(models.Order).offset(skip).limit(limit).all()


def create_order(
    db: Session,
    order: schemas.OrderCreate,
    total_amount: float
) -> models.Order:
    """
    Create a new order with items.
    
    Args:
        db: Database session
        order: OrderCreate schema with user_id and items
        total_amount: Pre-calculated total (passed from API)
        
    Returns:
        Created Order object with nested items
        
    Process:
        1. Create Order record
        2. For each item, create OrderItem record
        3. Link OrderItems to Order
        4. Commit transaction (atomic!)
        
    Why atomic?
        If ANY step fails, ENTIRE order is rolled back.
        You never get an order with some items missing.
        
    SQL generated (multiple queries in one transaction):
        BEGIN TRANSACTION;
        INSERT INTO orders (user_id, total_amount, status) VALUES (?, ?, ?);
        INSERT INTO order_items (order_id, product_id, qty, price) VALUES (?, ?, ?, ?);
        INSERT INTO order_items (order_id, product_id, qty, price) VALUES (?, ?, ?, ?);
        COMMIT;
    """
    # Create order record
    db_order = models.Order(
        user_id=order.user_id,
        total_amount=total_amount,
        status="pending"
    )
    
    db.add(db_order)
    db.flush()  # Flush to get order.id without committing
    # flush() saves to DB but doesn't commit transaction yet
    # This gives us db_order.id for creating order_items
    
    # Create order items
    for item in order.items:
        # Get product to get current price
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        
        if product:
            db_order_item = models.OrderItem(
                order_id=db_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_purchase=product.price  # Store historical price
            )
            db.add(db_order_item)
    
    # Commit entire transaction
    db.commit()
    db.refresh(db_order)
    
    return db_order


def update_order_status(db: Session, order_id: int, status: str) -> Optional[models.Order]:
    """
    Update order status.
    
    Args:
        db: Database session
        order_id: ID of order
        status: New status (pending, completed, cancelled)
        
    Returns:
        Updated Order object if found, None otherwise
        
    Use cases:
        - Payment successful → "completed"
        - User cancels → "cancelled"
        - Awaiting payment → "pending"
    """
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    
    if db_order is None:
        return None
    
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    
    return db_order


# ============================================================================
# QUERY EXAMPLES (for understanding)
# ============================================================================
#
# SIMPLE QUERY:
# products = db.query(models.Product).all()
# SQL: SELECT * FROM products
#
# FILTER:
# product = db.query(models.Product).filter(models.Product.price > 100).all()
# SQL: SELECT * FROM products WHERE price > 100
#
# FIRST/ONE:
# product = db.query(models.Product).filter(models.Product.id == 1).first()
# SQL: SELECT * FROM products WHERE id = 1 LIMIT 1
#
# ORDER BY:
# products = db.query(models.Product).order_by(models.Product.price.desc()).all()
# SQL: SELECT * FROM products ORDER BY price DESC
#
# JOIN (automatic via relationships):
# order = db.query(models.Order).filter(models.Order.id == 1).first()
# order.items  # Automatically loads order_items via relationship
#
# COUNT:
# count = db.query(models.Product).count()
# SQL: SELECT COUNT(*) FROM products
#
# ============================================================================
