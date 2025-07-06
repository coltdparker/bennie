import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """
    Get database URL from environment variables.
    Railway automatically provides DATABASE_URL when you add a PostgreSQL service.
    """
    # Railway provides DATABASE_URL in production
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Railway's DATABASE_URL format: postgresql://username:password@host:port/database
        # SQLAlchemy expects: postgresql://username:password@host:port/database
        # So we just use it as-is
        return database_url
    
    # Fallback for local development
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "bennie_db")
    username = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    
    return f"postgresql://{username}:{password}@{host}:{port}/{database}"

def create_database_engine():
    """
    Create SQLAlchemy engine with appropriate configuration for Railway.
    """
    database_url = get_database_url()
    
    # Engine configuration
    engine_kwargs = {
        "echo": os.getenv("DEBUG", "False").lower() == "true",  # Log SQL queries in debug mode
        "pool_pre_ping": True,  # Verify connections before use
        "pool_recycle": 300,  # Recycle connections every 5 minutes
    }
    
    # Railway-specific configurations
    if "railway.app" in database_url or os.getenv("RAILWAY_ENVIRONMENT"):
        # Railway PostgreSQL configurations
        engine_kwargs.update({
            "pool_size": 5,  # Smaller pool size for Railway
            "max_overflow": 10,
            "pool_timeout": 30,
        })
    
    return create_engine(database_url, **engine_kwargs)

# Create engine instance
engine = create_database_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency to get database session.
    Use this in FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database tables.
    Call this when setting up the application.
    """
    from .models import Base
    Base.metadata.create_all(bind=engine)

def test_connection():
    """
    Test database connection.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    # Test the connection
    test_connection() 