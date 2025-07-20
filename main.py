#!/usr/bin/env python3
"""
Main application entry point for Bennie.
This file serves the frontend and provides API endpoints.
"""

import os
import logging
import secrets
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Header, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

def generate_verification_token() -> str:
    """Generate a secure verification token for onboarding."""
    return secrets.token_urlsafe(32)

# Note: Scheduler has been moved to Railway cron jobs for reliability
# See railway.json for cron job configurations

# Create FastAPI app
app = FastAPI(
    title="Bennie - AI Language Learning",
    description="AI-powered language learning through personalized emails",
    version="1.0.0"
)

# Note: Scheduler is now handled by Railway cron jobs

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

@app.get("/onboard")
async def read_onboard():
    """Serve the onboarding page."""
    return FileResponse("onboard.html")

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
        
        # Find user by verification token
        response = supabase.table("users").select("id, email, name, target_language, is_verified").eq("verification_token", token).execute()
        
        if hasattr(response, 'status_code') and response.status_code >= 400:
            logger.error(f"Error verifying token: {response}")
            raise HTTPException(status_code=500, detail=f"Database error: {response}")
        
        if not response.data or len(response.data) == 0:
            logger.warning(f"Invalid token: {token[:10]}...")
            raise HTTPException(status_code=404, detail="Invalid or expired token")
        
        user = response.data[0]
        
        # Check if user is already verified
        if user.get("is_verified", False):
            logger.warning(f"User already verified: {user['email']}")
            raise HTTPException(status_code=400, detail="User already completed onboarding")
        
        return {
            "success": True,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "target_language": user["target_language"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in verify_token: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

class OnboardingData(BaseModel):
    token: str
    skill_level: int = Field(..., ge=1, le=10)  # Must be between 1 and 10
    learning_goal: str = Field(..., min_length=1, max_length=1000)  # Descriptive text from slider
    target_proficiency: int = Field(..., ge=20, le=100)  # Numeric level 20-100 from slider mapping
    motivation_goal: str = Field(..., min_length=1, max_length=1000)
    topics_of_interest: str = Field(..., min_length=1, max_length=1000)

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
        logger.info(f"Completing onboarding for token: {onboarding_data.token[:10]}... with target_proficiency: {onboarding_data.target_proficiency}")
        logger.info(f"Full onboarding data received: {onboarding_data}")
        
        # First verify the token and get user
        verify_response = supabase.table("users").select("id").eq("verification_token", onboarding_data.token).execute()
        
        if not verify_response.data or len(verify_response.data) == 0:
            raise HTTPException(status_code=404, detail="Invalid or expired token")
        
        user_id = verify_response.data[0]["id"]
        
        # Update user with onboarding information
        update_data = {
            "proficiency_level": onboarding_data.skill_level,
            "learning_goal": onboarding_data.learning_goal,
            "target_proficiency": onboarding_data.target_proficiency,  # Store numeric level 1-5
            "motivation_goal": onboarding_data.motivation_goal,
            "topics_of_interest": onboarding_data.topics_of_interest,
            "is_verified": True,
            "verification_token": None,  # Clear the token after use
            "updated_at": "now()"
        }
        
        update_response = supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        if hasattr(update_response, 'status_code') and update_response.status_code >= 400:
            logger.error(f"Error updating user: {update_response}")
            raise HTTPException(status_code=500, detail=f"Failed to update user: {update_response}")
        
        logger.info(f"Onboarding completed successfully for user ID: {user_id}")
        
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
        
        # Generate verification token
        verification_token = generate_verification_token()
        
        # Prepare data for insertion
        insert_data = {
            "email": user_data.email.lower().strip(),
            "name": user_data.name.strip(),
            "target_language": user_data.language.lower().strip(),
            "verification_token": verification_token
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

        # Send welcome email in the background with the verification token
        background_tasks.add_task(
            send_welcome_email,
            user_data.name.strip(),
            user_data.email.lower().strip(),
            user_data.language.lower().strip(),
            verification_token
        )

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
        user.pop("verification_token", None)
        
        return {"success": True, "user": user}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

SENDGRID_WEBHOOK_SECRET = os.getenv("SENDGRID_WEBHOOK_SECRET", "changeme")

@app.post("/api/sendgrid-inbound")
async def sendgrid_inbound(request: Request, secret: Optional[str] = Query(None)):
    """
    Endpoint to receive SendGrid Inbound Parse Webhook POSTs.
    Expects multipart/form-data with at least 'from' and 'text' fields.
    Secured with a 'secret' query parameter.
    """
    logger.info("=== SendGrid Inbound Webhook Received ===")
    logger.info(f"Secret provided: {secret[:10] + '...' if secret else 'None'}")
    logger.info(f"Expected secret: {SENDGRID_WEBHOOK_SECRET[:10] + '...' if SENDGRID_WEBHOOK_SECRET else 'None'}")
    
    # Basic security check
    if secret != SENDGRID_WEBHOOK_SECRET:
        logger.error(f"Unauthorized webhook attempt. Secret mismatch.")
        return {"success": False, "error": "Unauthorized"}

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

        # Find user by email
        logger.info(f"Looking up user with email: {sender_email.lower()}")
        user_resp = supabase.table("users").select("id, name, target_language, proficiency_level, instant_reply").eq("email", sender_email.lower()).execute()
        
        if hasattr(user_resp, 'status_code') and user_resp.status_code >= 400:
            logger.error(f"Database error looking up user: {user_resp}")
            return {"success": False, "error": f"Database error: {user_resp}"}
        
        if not user_resp.data or len(user_resp.data) == 0:
            logger.error(f"User not found for email: {sender_email}")
            return {"success": False, "error": "User not found"}
        
        user = user_resp.data[0]
        user_id = user["id"]
        user_name = user["name"]
        user_language = user["target_language"]
        user_level = user.get("proficiency_level", 1)
        instant_reply = user.get("instant_reply", False)
        logger.info(f"Found user: {user_name} (ID: {user_id}), instant_reply={instant_reply}")

        # Insert into email_history
        logger.info("Inserting reply into email_history table")
        try:
            insert_resp = supabase.table("email_history").insert({
                "user_id": user_id,
                "content": text_content,
                "is_from_bennie": False
            }).execute()
            logger.info(f"Supabase insert response: {insert_resp}")
            if hasattr(insert_resp, 'status_code') and insert_resp.status_code >= 400:
                logger.error(f"Database error inserting email: {insert_resp}")
                return {"success": False, "error": f"DB error: {insert_resp}"}
        except Exception as db_exc:
            logger.error(f"Exception during Supabase insert: {db_exc}")
            return {"success": False, "error": f"Supabase insert exception: {str(db_exc)}"}

        # DEV AUTO-EVAL: If instant_reply, check for 3+ replies since last eval and trigger eval if needed
        if instant_reply:
            try:
                # Find last evaluation email
                evals_resp = supabase.table("email_history").select("created_at").eq("user_id", user_id).eq("is_evaluation", True).order("created_at", desc=True).limit(1).execute()
                last_eval_time = None
                if evals_resp.data and len(evals_resp.data) > 0:
                    last_eval_time = evals_resp.data[0]["created_at"]
                # Count user replies since last eval
                replies_query = supabase.table("email_history").select("id").eq("user_id", user_id).eq("is_from_bennie", False)
                if last_eval_time:
                    replies_query = replies_query.gte("created_at", last_eval_time)
                replies_resp = replies_query.execute()
                reply_count = len(replies_resp.data) if replies_resp.data else 0
                logger.info(f"DEV AUTO-EVAL: User {user_name} ({sender_email}) has {reply_count} replies since last eval.")
                if reply_count >= 3:
                    from Backend.send_weekly_evaluation_email import send_weekly_evaluation_email
                    send_weekly_evaluation_email(sender_email)
                    logger.info(f"✓ DEV AUTO-EVAL: Evaluation email sent to {sender_email}")
            except Exception as e:
                logger.error(f"DEV AUTO-EVAL: Failed to check/send evaluation for {sender_email}: {e}")

        # If instant_reply is enabled, send a language learning email immediately
        if instant_reply:
            logger.info(f"User {user_name} has instant_reply enabled. Sending immediate response...")
            try:
                # Use the legacy wrapper to support the old signature
                from Backend.bennie_email_sender import send_language_learning_email_legacy
                send_language_learning_email_legacy(
                    user_name=user_name,
                    user_email=sender_email,
                    user_language=user_language,
                    user_level=user_level
                )
                logger.info(f"✓ Immediate language learning email sent to {user_name} ({sender_email})")
            except Exception as e:
                logger.error(f"Error sending instant reply email: {e}")

        logger.info(f"✓ Successfully saved reply from {user_name} ({sender_email})")
        return {"success": True, "message": "Reply saved"}

    except Exception as e:
        logger.error(f"Unexpected error in sendgrid_inbound: {e}")
        return {"success": False, "error": f"Internal error: {str(e)}"}

# ---
# Helper endpoint for AI: fetch all email history for a user (by email)
# This allows the AI agent to see the full conversation history for context and personalization.
# ---
@app.get("/api/email-history/{email}")
async def get_email_history(email: str):
    """
    Fetch all email history for a user by their email address.
    Returns a list of messages (from user and from Bennie) in chronological order.
    """
    logger.info(f"Fetching email history for user: {email}")
    user_resp = supabase.table("users").select("id").eq("email", email.lower().strip()).execute()
    if not user_resp.data or len(user_resp.data) == 0:
        logger.error(f"User not found for email: {email}")
        return {"success": False, "error": "User not found"}
    user_id = user_resp.data[0]["id"]
    history_resp = supabase.table("email_history").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
    logger.info(f"Fetched {len(history_resp.data) if history_resp.data else 0} messages for user_id {user_id}")
    return {"success": True, "history": history_resp.data or []}

@app.get("/api/test-webhook")
async def test_webhook():
    """
    Test endpoint to verify webhook URL is accessible.
    """
    logger.info("Webhook test endpoint accessed")
    return {
        "success": True,
        "message": "Webhook endpoint is accessible",
        "timestamp": "2025-01-27T00:00:00Z",
        "webhook_url": "/api/sendgrid-inbound",
        "secret_configured": bool(SENDGRID_WEBHOOK_SECRET and SENDGRID_WEBHOOK_SECRET != "changeme")
    }

@app.get("/test-httpbin")
def test_httpbin():
    try:
        r = httpx.get("https://httpbin.org/get", timeout=5)
        return {"success": True, "status_code": r.status_code, "json": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/trigger-dev-auto-eval")
async def trigger_dev_auto_eval():
    """Trigger dev auto-evaluation for instant_reply users."""
    try:
        logger.info("Running dev auto-eval check...")
        users_resp = supabase.table("users").select("id,email").eq("instant_reply", True).execute()
        
        if not users_resp.data:
            logger.info("No instant_reply users found for dev auto-eval.")
            return {"success": True, "message": "No instant_reply users found"}
        
        eval_count = 0
        for user in users_resp.data:
            user_id = user["id"]
            email = user["email"]
            
            # Find last evaluation email
            evals_resp = supabase.table("email_history").select("created_at").eq("user_id", user_id).eq("is_evaluation", True).order("created_at", desc=True).limit(1).execute()
            last_eval_time = None
            if evals_resp.data and len(evals_resp.data) > 0:
                last_eval_time = evals_resp.data[0]["created_at"]
            
            # Count user replies since last eval
            replies_query = supabase.table("email_history").select("id").eq("user_id", user_id).eq("is_from_bennie", False)
            if last_eval_time:
                replies_query = replies_query.gte("created_at", last_eval_time)
            replies_resp = replies_query.execute()
            reply_count = len(replies_resp.data) if replies_resp.data else 0
            
            if reply_count >= 3:
                try:
                    from Backend.send_weekly_evaluation_email import send_weekly_evaluation_email
                    send_weekly_evaluation_email(email)
                    eval_count += 1
                    logger.info(f"✓ Dev auto-eval sent to {email} (replies since last eval: {reply_count})")
                except Exception as e:
                    logger.error(f"Dev auto-eval failed for {email}: {e}")
        
        return {
            "success": True, 
            "message": f"Dev auto-eval completed. {eval_count} evaluations sent.",
            "evaluations_sent": eval_count
        }
        
    except Exception as e:
        logger.error(f"Dev auto-eval job failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dev auto-eval failed: {str(e)}")

# Register the /test-openai endpoint
app.add_api_route("/test-openai", test_openai, methods=["GET"])

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