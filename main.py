#!/usr/bin/env python3
"""
Main application entry point for Bennie.
This file serves the frontend and provides API endpoints.
Version: 2025.07.25.1 - Fixed Supabase client initialization
"""

import os
import logging
import secrets
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Header, Query, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel, EmailStr, Field
from supabase import create_client, Client
from typing import Optional
import sys
import datetime
from urllib.parse import quote, unquote
sys.path.append('./Backend')
from new_user_email import send_welcome_email
from Backend.bennie_email_sender import send_language_learning_email
from Backend.openai_connectivity_test import test_openai

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Environment variables
SUPABASE_URL: str = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY")  # Anon key for client auth

# Debug: Print environment variables (mask keys)
logger.info(f"SUPABASE_URL configured: {bool(SUPABASE_URL)}")
logger.info(f"SUPABASE_ANON_KEY configured: {bool(SUPABASE_ANON_KEY)}")

if not all([SUPABASE_URL, SUPABASE_ANON_KEY]):
    logger.error("Missing required environment variables")
    raise ValueError("Missing required environment variables")

# Initialize Supabase client with anon key
try:
    logger.info("Initializing Supabase client...")
    
    # Initialize Supabase client
    supabase: Client = create_client(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_ANON_KEY
    )
    
    logger.info("Supabase client initialized successfully")
    
    # Test connection with proper error handling
    try:
        # Test database connection
        test_response = supabase.table("users").select("count", count="exact").limit(1).execute()
        logger.info("Successfully tested Supabase database connection")
    except Exception as db_e:
        logger.error(f"Database test failed: {db_e}")
        # Try auth connection instead
        try:
            test_response = supabase.auth.get_session()
            logger.info("Successfully tested Supabase auth connection")
        except Exception as auth_e:
            logger.error(f"Auth test failed: {auth_e}")
            raise RuntimeError("Failed to connect to Supabase services")
    
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    raise RuntimeError(f"Supabase initialization failed: {str(e)}")

# Create FastAPI app
app = FastAPI(
    title="Bennie API",
    description="Backend API for Bennie language learning platform",
    # Remove root_path as Railway handles this
)

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

# Pydantic models for authentication
class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    language: str

@app.get("/")
async def read_root():
    """Serve the landing page."""
    return FileResponse("frontend/src/index.html")

@app.get("/onboard")
async def read_onboard():
    """Serve the onboarding page."""
    return FileResponse("frontend/src/onboard.html")

@app.get("/signin")
async def read_signin():
    """Serve the sign-in page."""
    return FileResponse("frontend/src/signin.html")

@app.get("/auth/callback")
async def auth_callback(request: Request):
    """Handle OAuth callback and redirect to appropriate page."""
    logger.info("Received OAuth callback")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Query params: {dict(request.query_params)}")
    
    try:
        # Get the code from the query parameters
        code = request.query_params.get('code')
        error = request.query_params.get('error')
        error_description = request.query_params.get('error_description')
        
        # Log all parameters for debugging
        logger.info(f"OAuth callback parameters - code: {'present' if code else 'missing'}, error: {error}, error_description: {error_description}")
        
        if error:
            logger.error(f"OAuth error received: {error} - {error_description}")
            return RedirectResponse(
                url=f"/signin?error={error}&error_description={error_description or ''}",
                status_code=302
            )
        
        if not code:
            logger.error("No code parameter in callback")
            return RedirectResponse(
                url="/signin?error=missing_code",
                status_code=302
            )

        logger.info(f"Found authorization code: {code[:20]}... (length: {len(code)})")
        
        try:
            # URL encode the code to handle any special characters
            encoded_code = quote(code, safe='')
            
            logger.info(f"Original code: {code[:30]}... (length: {len(code)})")
            logger.info(f"Encoded code: {encoded_code[:30]}... (length: {len(encoded_code)})")
            logger.info("Redirecting to signin page with authorization code")
            
            redirect_url = f"/signin?code={encoded_code}"
            logger.info(f"Final redirect URL: {redirect_url}")
            
            return RedirectResponse(
                url=redirect_url,
                status_code=302
            )
            
        except Exception as e:
            logger.error(f"Error processing code: {str(e)}")
            return RedirectResponse(
                url=f"/signin?error=exchange_failed&error_description={str(e)}",
                status_code=302
            )
        
    except Exception as e:
        logger.error(f"Error in callback handler: {str(e)}")
        return RedirectResponse(
            url=f"/signin?error=callback_error&error_description={str(e)}",
            status_code=302
        )

@app.get("/profile")
async def read_profile():
    """Serve the profile page."""
    return FileResponse("frontend/src/profile.html")

@app.get("/privacy")
async def read_privacy():
    """Serve the privacy policy page."""
    return FileResponse("frontend/src/privacy.html")

@app.post("/api/auth/signin")
async def signin(signin_data: SignInRequest):
    """
    Sign in a user with email and password using Supabase Auth.
    
    Args:
        signin_data: User's email and password
        
    Returns:
        dict: Auth session data including access token
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        email = signin_data.email.lower()
        logger.info(f"[SIGNIN] Starting sign-in process for email: {email}")
        
        try:
            # Attempt to sign in with email/password
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": signin_data.password
            })
            
            if not auth_response or not auth_response.user:
                logger.error("[SIGNIN] No user data in auth response")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password"
                )
            
            # Get user profile data
            user_data = supabase.table("users").select("*").eq("email", email).single().execute()
            
            logger.info(f"[SIGNIN] User {email} signed in successfully")
            
            return {
                "success": True,
                "session": auth_response.session,
                "user": user_data.data if user_data else None
            }
            
        except Exception as auth_e:
            logger.error(f"[SIGNIN] Auth error for {email}: {str(auth_e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[SIGNIN] Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

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
        # Test Supabase connection using admin client
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
    """Create a new user and send welcome email."""
    try:
        # Prepare user data for Supabase Auth
        signup_data = {
            "email": user_data.email.lower(),
            "user_metadata": {
                "name": user_data.name,
                "target_language": user_data.language
            }
        }
        
        # Create user using service role key
        auth_response = supabase.auth.admin.create_user(signup_data)
        
        if not auth_response or not auth_response.user:
            logger.error("Failed to create user in Supabase Auth")
            raise HTTPException(status_code=500, detail="Failed to create user")
            
        # Insert user into our users table
        try:
            user_insert_data = {
                "auth_user_id": auth_response.user.id,
                "email": user_data.email.lower(),
                "name": user_data.name,
                "target_language": user_data.language,
                "created_at": "now()",
                "updated_at": "now()"
            }
            
            logger.info(f"Inserting user into users table: {user_insert_data}")
            user_insert_response = supabase.table("users").insert(user_insert_data).execute()
            
            if not user_insert_response.data:
                logger.error("Failed to insert user into users table")
                raise HTTPException(status_code=500, detail="Failed to create user profile")
                
            logger.info("Successfully created user in both auth and users tables")
        except Exception as e:
            logger.error(f"Failed to insert user into users table: {e}")
            # Try to clean up auth user if users table insert fails
            try:
                supabase.auth.admin.delete_user(auth_response.user.id)
            except:
                pass
            raise HTTPException(status_code=500, detail="Failed to create user profile")
        
        # Generate magic link
        sign_in_token = supabase.auth.admin.generate_link(
            {
                "email": user_data.email,
                "type": "magiclink",
                "redirect_to": "https://itsbennie.com/onboard"
            }
        )
        
        if not sign_in_token:
            logger.error("Failed to generate magic link")
            raise HTTPException(status_code=500, detail="Failed to generate magic link")
        
        # Schedule welcome email
        background_tasks.add_task(
            send_welcome_email,
            user_data.email,
            user_data.name,
            sign_in_token
        )
        
        return {
            "success": True,
            "user": {
                "email": user_data.email,
                "name": user_data.name,
                "target_language": user_data.language
            },
            "user_id": auth_response.user.id
        }
        
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

@app.post("/api/auth/reset-password")
async def reset_password(reset_data: dict):
    """
    Send a password reset email to the user.
    
    Args:
        reset_data: Dict containing email
        
    Returns:
        dict: Success response
    """
    try:
        email = reset_data.get("email", "").lower()
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
            
        logger.info(f"[PASSWORD RESET] Sending reset email to: {email}")
        
        # Send password reset email
        auth_response = supabase.auth.reset_password_email(email)
        
        logger.info(f"[PASSWORD RESET] Reset email sent successfully to: {email}")
        
        return {
            "success": True,
            "message": "Password reset instructions sent to your email"
        }
        
    except Exception as e:
        logger.error(f"[PASSWORD RESET] Error sending reset email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send password reset email"
        )

@app.get("/api/auth/config")
async def get_auth_config():
    """
    Provide Supabase configuration for client-side authentication.
    Only returns the public anon key and URL, never the service role key.
    """
    logger.info("Auth config requested")
    logger.info(f"SUPABASE_URL configured: {bool(SUPABASE_URL)}")
    logger.info(f"SUPABASE_ANON_KEY configured: {bool(SUPABASE_ANON_KEY)}")
    
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        logger.error("Missing required Supabase configuration")
        raise HTTPException(
            status_code=500,
            detail="Authentication service configuration error"
        )
    
    config = {
        "supabaseUrl": SUPABASE_URL,
        "supabaseKey": SUPABASE_ANON_KEY
    }
    
    logger.info("Auth config provided successfully")
    return config

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