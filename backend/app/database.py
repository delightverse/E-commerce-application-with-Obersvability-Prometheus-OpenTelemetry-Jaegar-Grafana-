"""
Database Configuration
======================

This module sets up:
1. SQLAlchemy engine (connection to PostgreSQL)
2. SessionLocal (database session factory)
3. Base (declarative base for models)

Key Concepts:
- Engine: The "pool" of database connections
- Session: A "conversation" with the database (one request = one session)
- Base: Parent class for all database models
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ============================================================================
# DATABASE URL
# ============================================================================
# Format: postgresql://username:password@host:port/database
# This is gotten from the environment variable (set in postgres section of the docker-compose.yml)
# Example: postgresql://user:password@postgres:5432/ecommerce

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/ecommerce"  # Fallback for local dev
)

# ============================================================================
# SQLAlchemy ENGINE
# ============================================================================
# The engine that manages database connections
#
# Parameters explained:
# - connect_args={"check_same_thread": False}
#   Only needed for SQLite (not Postgres), but harmless to include
#   Allows multiple threads to use the same connection
#
# - pool_pre_ping=True
#   IMPORTANT: Tests connections before using them
#   If connection died (database restarted), SQLAlchemy will reconnect
#   Prevents "connection lost" errors
#
# - echo=False
#   If True, prints all SQL queries to console (useful for debugging)
#   Set to True if you want to see what SQL is being generated

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Test connections before use (resilience). Restarts DB if connection is lost without crashing app.
    echo=False,          # Set to True to see SQL queries in logs
)

# ============================================================================
# SESSION FACTORY
# ============================================================================
# SessionLocal is a FACTORY, not a session itself i.e. it's a function that creates sessions
# Each time you call SessionLocal(), you get a NEW session
#
# Why not create one global session?
# - Sessions are NOT thread-safe
# - Each HTTP request should have its own session
# - Sessions are like database "transactions"
#
# Parameters:
# - autocommit=False
#   Changes aren't saved until you call session.commit()
#   Gives you control over when data is written
#
# - autoflush=False
#   SQLAlchemy won't automatically sync in-memory changes to DB
#   You control when this happens
#
# - bind=engine
#   This session factory will use our engine (Postgres connection pool)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ============================================================================
# DECLARATIVE BASE
# ============================================================================
# All database models will inherit from this Base class
# When you create a model: class Product(Base): ...
# SQLAlchemy knows "this is a database table"
#
# Base provides:
# - __tablename__ (maps class to table name)
# - Columns (id, name, price, etc.)
# - Relationships (Product → Orders)
# - Metadata (used to create/drop tables)

Base = declarative_base()

# ============================================================================
# EXAMPLE USAGE (for understanding)
# ============================================================================
# This is NOT executed, just showing how these are used:
#
# # Import this module
# from app.database import SessionLocal, engine, Base
#
# # Create all tables (usually done at startup)
# Base.metadata.create_all(bind=engine)
#
# # Use a session in an API endpoint
# def get_products():
#     db = SessionLocal()  # Create new session
#     try:
#         products = db.query(Product).all()  # Query database
#         return products
#     finally:
#         db.close()  # ALWAYS close the session!
#
# ============================================================================
