#!/usr/bin/env python3
"""
Main application entry point for Bennie.
This file serves the frontend and provides API endpoints.
"""

import os
import logging
import secrets
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Header, Query, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel, EmailStr, Field
from supabase import create_client, Client
from typing import Optional
import sys
sys.path.append('./Backend')
from new_user_email import send_welcome_email
from Backend.bennie_email_sender import send_language_learning_email
from Backend.openai_connectivity_test import test_openai

import base64
import httpx
from fastapi.exceptions import RequestValidationError
import datetime

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Log environment setup
logger.info("Starting Bennie application...")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info("Checking required environment variables...")

SUPABASE_URL: str = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")

# Debug: Print environment variables (mask key)
logger.info(f"SUPABASE_URL configured: {bool(SUPABASE_URL)}")
logger.info(f"SUPABASE_KEY configured: {bool(SUPABASE_KEY)}")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing required environment variables: SUPABASE_URL or SUPABASE_KEY")
    raise ValueError("Missing required environment variables")

try:
    logger.info("Initializing Supabase client...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully")
    
    # Test connection immediately
    test_response = supabase.table("users").select("count", count="exact").limit(1).execute()
    logger.info("Successfully tested Supabase connection")
except Exception as e:
    logger.error(f"Failed to initialize or test Supabase client: {e}")
    raise

# Create FastAPI app
app = FastAPI()

# Log middleware setup
logger.info("Configuring CORS middleware...")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware configured")

# Update static files configuration
app.mount("/static", StaticFiles(directory="frontend/public/static"), name="static")
logger.info("Static files directory mounted")

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    language: str

class OnboardingData(BaseModel):
    token: str
    skill_level: int = Field(ge=1, le=100)
    learning_goal: str
    target_proficiency: int = Field(ge=1, le=100)
    motivation_goal: str
    topics_of_interest: str

@app.get("/")
async def read_root():
    """Serve the landing page."""
    return FileResponse("frontend/src/index.html")

@app.get("/onboard")
async def read_onboard():
    """Serve the onboarding page."""
    return FileResponse("frontend/src/onboard.html")

@app.get("/api/verify-token/{token}")
async def verify_token(token: str):
    """
    Verify a user's onboarding token and return their basic information.
    
    Args:
        token: The verification token from the email link
        
    Returns:
        dict: User information if token is valid
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        logger.info(f"Verifying token: {token[:10]}...")
        
        # Verify the magic link token
        try:
            verify_response = supabase.auth.verify_otp({
                "token_hash": token,
                "type": "magiclink"
            })
            
            if not verify_response or not verify_response.user:
                logger.warning(f"Invalid token: {token[:10]}...")
                raise HTTPException(status_code=404, detail="Invalid or expired token")
            
            user_id = verify_response.user.id
            user_email = verify_response.user.email
            
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(status_code=404, detail="Invalid or expired token")
        
        # Get user profile from public.users
        user_response = supabase.table("users").select("auth_user_id, name, target_language").eq("auth_user_id", user_id).execute()
        
        if not user_response.data:
            logger.error(f"User profile not found for auth_user_id: {user_id}")
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user = user_response.data[0]
        
        return {
            "success": True,
            "user": {
                "id": user["auth_user_id"],
                "email": user_email,
                "name": user["name"],
                "target_language": user["target_language"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in verify_token: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/complete-onboarding")
async def complete_onboarding(onboarding_data: OnboardingData):
    """
    Complete the user's onboarding process.
    
    Args:
        onboarding_data: Onboarding information including token and user preferences
        
    Returns:
        dict: Success response
        
    Raises:
        HTTPException: If token is invalid or update fails
    """
    try:
        # Log all incoming data (except token)
        log_data = onboarding_data.dict()
        log_data["token"] = log_data["token"][:10] + "..."  # Truncate token for logging
        logger.info(f"Received onboarding data: {log_data}")
        
        # First verify the token and get user
        auth_response = supabase.auth.verify_otp(onboarding_data.token)
        
        if not auth_response or not auth_response.user:
            logger.warning(f"Invalid token attempted: {onboarding_data.token[:10]}...")
            raise HTTPException(status_code=404, detail="Invalid or expired token")
        
        auth_user_id = auth_response.user.id
        logger.info(f"Token verified for auth_user_id: {auth_user_id}")
        
        # Update user with onboarding information
        update_data = {
            "proficiency_level": onboarding_data.skill_level,
            "learning_goal": onboarding_data.learning_goal,
            "target_proficiency": onboarding_data.target_proficiency,
            "motivation_goal": onboarding_data.motivation_goal,
            "topics_of_interest": onboarding_data.topics_of_interest,
            "updated_at": "now()"
        }
        
        logger.info(f"Updating user {auth_user_id} with data: {update_data}")
        update_response = supabase.table("users").update(update_data).eq("auth_user_id", auth_user_id).execute()
        
        if not update_response.data:
            logger.error(f"Failed to update user: {update_response.error}")
            raise HTTPException(status_code=500, detail="Failed to update user profile")
        
        return {
            "success": True,
            "message": "Onboarding completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in complete_onboarding: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    try:
        # Test Supabase connection
        response = supabase.table("users").select("count", count="exact").limit(1).execute()
        if hasattr(response, 'status_code') and response.status_code >= 400:
            logger.error(f"Health check failed: Supabase error {response.status_code}")
            raise Exception(f"Supabase error: {response.status_code}")
            
        logger.info("Health check: Supabase connection successful")
        logger.info(f"Response data: {response.data}")
        
        # Use current timestamp
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        return {
            "status": "healthy", 
            "service": "bennie",
            "database": "connected",
            "timestamp": current_time,
            "database_response": "success"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        # Use current timestamp even in error response
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return {
            "status": "unhealthy",
            "service": "bennie", 
            "database": "disconnected",
            "timestamp": current_time,
            "error": str(e)
        }

@app.post("/api/users")
async def create_user(user_data: UserCreate, background_tasks: BackgroundTasks):
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
        
        # Check if user already exists in auth.users
        try:
            # Use list_users and filter instead of get_user_by_email
            existing_users = supabase.auth.admin.list_users()
            existing_user = next(
                (user for user in existing_users if user.email == user_data.email.lower()),
                None
            )
            if existing_user:
                logger.warning(f"User already exists: {user_data.email}")
                raise HTTPException(status_code=400, detail="User already exists")
        except Exception as e:
            if "User not found" not in str(e):
                raise
        
        # Create user in auth.users with metadata
        signup_data = {
            "email": user_data.email.lower().strip(),
            "password": secrets.token_urlsafe(30),  # Generate a secure random password
            "email_confirm": True,  # Auto-confirm for now
            "user_metadata": {
                "name": user_data.name.strip(),
                "target_language": user_data.language.lower().strip(),
                "proficiency_level": 1,  # Default starting level
                "topics_of_interest": "",  # Will be set during onboarding
                "learning_goal": None,  # Will be set during onboarding
                "motivation_goal": None,  # Will be set during onboarding
                "target_proficiency": 50,  # Default target
                "email_schedule": {"frequency": "weekly"}
            }
        }
        
        auth_response = supabase.auth.admin.create_user(signup_data)
        
        if not auth_response or not auth_response.user:
            logger.error("Failed to create auth user")
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # The trigger will automatically create the user profile in public.users
        
        # Generate magic link for onboarding
        magic_link_response = supabase.auth.admin.generate_link(
            type="magiclink",
            email=user_data.email,
            redirect_to="https://itsbennie.com/onboard"  # Adjust this URL as needed
        )
        
        if not magic_link_response:
            logger.error("Failed to generate magic link")
            raise HTTPException(status_code=500, detail="Failed to generate verification link")
        
        # Send welcome email with magic link
        background_tasks.add_task(
            send_welcome_email,
            user_name=user_data.name,
            user_email=user_data.email,
            user_language=user_data.language,
            user_token=magic_link_response.properties.action_link
        )
        
        return {
            "success": True,
            "user_id": auth_response.user.id,
            "message": "User created successfully. Check your email to complete onboarding.",
            "user": {
                "email": user_data.email,
                "name": user_data.name,
                "target_language": user_data.language
            }
        }
        
    except HTTPException:
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
        
        # Get auth user
        users = supabase.auth.admin.list_users()
        auth_user = next(
            (user for user in users if user.email == email.lower()),
            None
        )
        
        if not auth_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user profile from public.users
        response = supabase.table("users").select("*").eq("auth_user_id", auth_user.id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user = response.data[0]
        # Remove sensitive fields
        user.pop("auth_user_id", None)
        
        return {"success": True, "user": user}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/sendgrid-inbound")
async def sendgrid_inbound(request: Request, secret: Optional[str] = Query(None)):
    """Handle inbound emails from SendGrid."""
    try:
        # Log all form data for debugging
        form = await request.form()
        logger.info(f"Form data received: {dict(form)}")
        
        sender_email = form.get('from')
        text_content = form.get('text')
        subject = form.get('subject', 'No subject')
        
        logger.info(f"Sender: {sender_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Content length: {len(text_content) if text_content else 0}")

        if not sender_email or not text_content:
            logger.error("Missing sender or content in webhook")
            return {"success": False, "error": "Missing sender or content"}

        # Extract just the email address (in case it's 'Name <email@example.com>')
        import re
        match = re.search(r'<(.+?)>', sender_email)
        if match:
            sender_email = match.group(1)
        else:
            sender_email = sender_email.strip()
            
        logger.info(f"Cleaned sender email: {sender_email}")

        # Get auth user first
        auth_user = supabase.auth.admin.get_user_by_email(sender_email.lower())
        
        if not auth_user:
            logger.error(f"User not found for email: {sender_email}")
            return {"success": False, "error": "User not found"}
        
        # Find user profile
        user_resp = supabase.table("users").select(
            "auth_user_id, name, target_language, proficiency_level, instant_reply"
        ).eq("auth_user_id", auth_user.id).execute()
        
        if not user_resp.data:
            logger.error(f"User profile not found for auth_user_id: {auth_user.id}")
            return {"success": False, "error": "User profile not found"}
        
        user = user_resp.data[0]
        instant_reply = user.get("instant_reply", False)
        
        # Save the email in history
        email_data = {
            "auth_user_id": user["auth_user_id"],
            "content": text_content,
            "is_from_bennie": False,
            "difficulty_level": user.get("proficiency_level", 1)
        }
        
        email_resp = supabase.table("email_history").insert(email_data).execute()
        
        if not email_resp.data:
            logger.error("Failed to save email to history")
            return {"success": False, "error": "Failed to save email"}
        
        # If instant reply is enabled, send a response
        if instant_reply:
            background_tasks.add_task(send_language_learning_email, sender_email)
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error processing inbound email: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Bind to all interfaces
        port=port,
        proxy_headers=True,  # Enable proxy headers
        forwarded_allow_ips="*",  # Trust forwarded headers
        log_level="info"
    ) 