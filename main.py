#!/usr/bin/env python3
"""
Main application entry point for Bennie.
This file serves the frontend and provides API endpoints.
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")

# Debug: Print environment variables (mask key)
logger.info(f"SUPABASE_URL: {SUPABASE_URL}")
logger.info(f"SUPABASE_KEY: {SUPABASE_KEY[:6] + '...' if SUPABASE_KEY else None}")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing required environment variables: SUPABASE_URL or SUPABASE_KEY")
    raise ValueError("Missing required environment variables")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    raise

# Create FastAPI app
app = FastAPI(
    title="Bennie - AI Language Learning",
    description="AI-powered language learning through personalized emails",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://itsbennie.com", "http://localhost:3000", "http://localhost:8000"],  # Add localhost for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def read_root():
    """Serve the main landing page."""
    return FileResponse("index.html")

@app.get("/onboard")                    # I assume that this is not complete as this needs a custom link that is for each user
async def read_onboard():
    """Serve the onboarding page."""
    return FileResponse("onboard.html")

@app.get("/health")                     # This is a health check endpoint for Railway to know that the backend is running
async def health_check():
    """Health check endpoint for Railway."""
    try:
        # Test Supabase connection
        response = supabase.table("users").select("count", count="exact").limit(1).execute()
        logger.info("Health check: Supabase connection successful")
        return {
            "status": "healthy", 
            "service": "bennie",
            "database": "connected",
            "timestamp": "2025-01-27T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "bennie", 
            "database": "disconnected",
            "error": str(e)
        }

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    language: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "John Doe",
                "language": "spanish"
            }
        }

@app.post("/api/users")
async def create_user(user_data: UserCreate):
    """
    Create a new user in the database.
    
    Args:
        user_data: User information including email, name, and target language
        
    Returns:
        dict: Success response with user ID and message
        
    Raises:
        HTTPException: If user already exists or database operation fails
    """
    try:
        logger.info(f"Creating user: {user_data.email}")
        
        # Check if user already exists
        logger.info("Checking if user already exists...")
        existing_user_response = supabase.table("users").select("id").eq("email", user_data.email).execute()
        logger.info(f"Supabase response for existing user: {existing_user_response}")
        
        # Check for error using status_code or data
        if hasattr(existing_user_response, 'status_code') and existing_user_response.status_code >= 400:
            logger.error(f"Error checking existing user: {existing_user_response}")
            raise HTTPException(status_code=500, detail=f"Database error: {existing_user_response}")
        
        if existing_user_response.data and len(existing_user_response.data) > 0:
            logger.warning(f"User already exists: {user_data.email}")
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Prepare data for insertion
        insert_data = {
            "email": user_data.email.lower().strip(),
            "name": user_data.name.strip(),
            "target_language": user_data.language.lower().strip()
        }
        
        logger.info(f"Inserting user data: {insert_data}")
        
        # Insert new user
        insert_response = supabase.table("users").insert(insert_data).execute()
        logger.info(f"Supabase response for insert: {insert_response}")
        
        if hasattr(insert_response, 'status_code') and insert_response.status_code >= 400:
            logger.error(f"Supabase insert error: {insert_response}")
            raise HTTPException(status_code=500, detail=f"Failed to create user: {insert_response}")
        
        if not insert_response.data or len(insert_response.data) == 0:
            logger.error("No data returned from insert operation")
            raise HTTPException(status_code=500, detail="Failed to create user: No data returned")
        
        user_id = insert_response.data[0]["id"]
        logger.info(f"User created successfully with ID: {user_id}")
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "User created successfully",
            "user": {
                "email": insert_data["email"],
                "name": insert_data["name"],
                "target_language": insert_data["target_language"]
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_user: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/users/{email}")
async def get_user(email: str):
    """
    Get user information by email.
    
    Args:
        email: User's email address
        
    Returns:
        dict: User information
        
    Raises:
        HTTPException: If user not found or database operation fails
    """
    try:
        logger.info(f"Getting user: {email}")
        
        response = supabase.table("users").select("*").eq("email", email.lower().strip()).execute()
        logger.info(f"Supabase response for get_user: {response}")
        
        if hasattr(response, 'status_code') and response.status_code >= 400:
            logger.error(f"Error getting user: {response}")
            raise HTTPException(status_code=500, detail=f"Database error: {response}")
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = response.data[0]
        # Remove sensitive fields
        user.pop("id", None)
        
        return {"success": True, "user": user}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting Bennie server on port {port} (debug={debug})")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level="info"
    ) 