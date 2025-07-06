#!/usr/bin/env python3
"""
Database setup script for Bennie.
This script initializes the database and creates the initial migration.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(__file__))

from database.connection import init_db, test_connection
from database.models import Base

load_dotenv()

def setup_database():
    """Set up the database tables."""
    print("🚀 Setting up Bennie database...")
    
    # Test connection first
    print("Testing database connection...")
    if not test_connection():
        print("❌ Database connection failed. Please check your configuration.")
        return False
    
    # Initialize database tables
    print("Creating database tables...")
    try:
        init_db()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        return False

def create_initial_migration():
    """Create the initial Alembic migration."""
    print("Creating initial migration...")
    
    try:
        # Run alembic init if it hasn't been done
        if not os.path.exists("alembic/versions"):
            print("Initializing Alembic...")
            os.system("alembic init alembic")
        
        # Create initial migration
        print("Creating initial migration...")
        os.system("alembic revision --autogenerate -m 'Initial migration'")
        
        # Run the migration
        print("Running migration...")
        os.system("alembic upgrade head")
        
        print("✅ Initial migration created and applied successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create migration: {e}")
        return False

def main():
    """Main setup function."""
    print("=" * 50)
    print("BENNIE DATABASE SETUP")
    print("=" * 50)
    
    # Check if we're in a Railway environment
    if os.getenv("DATABASE_URL"):
        print("✅ Railway environment detected")
        print(f"Database URL: {os.getenv('DATABASE_URL')[:20]}...")
    else:
        print("⚠️  Local development environment detected")
        print("Make sure you have PostgreSQL running locally")
    
    # Set up database
    if not setup_database():
        print("❌ Database setup failed")
        sys.exit(1)
    
    # Create migration
    if not create_initial_migration():
        print("❌ Migration creation failed")
        sys.exit(1)
    
    print("=" * 50)
    print("✅ Database setup complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Your database is ready to use")
    print("2. You can now run your application")
    print("3. To add new migrations in the future, run:")
    print("   alembic revision --autogenerate -m 'Description of changes'")
    print("   alembic upgrade head")

if __name__ == "__main__":
    main() 