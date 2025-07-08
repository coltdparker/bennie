#!/usr/bin/env python3
"""
Main application entry point for Bennie.
This file serves the frontend and provides API endpoints.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Debug: Print environment variables (mask key)
print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY:", SUPABASE_KEY[:6] + "..." if SUPABASE_KEY else None)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create FastAPI app
app = FastAPI(
    title="Bennie - AI Language Learning",
    description="AI-powered language learning through personalized emails",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
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

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    return {"status": "healthy", "service": "bennie"}

class UserCreate(BaseModel):
    email: str
    name: str
    language: str

@app.post("/api/users")
async def create_user(user_data: UserCreate):
    try:
        response = supabase.table("users").select("id").eq("email", user_data.email).execute()
        if response.data and len(response.data) > 0:
            raise HTTPException(status_code=400, detail="User already exists")
        insert_data = {
            "email": user_data.email,
            "name": user_data.name,
            "target_language": user_data.language.lower()
        }
        response = supabase.table("users").insert(insert_data).execute()
        if response.error:
            print("Supabase error:", response.error)
            raise HTTPException(status_code=500, detail=str(response.error))
        user_id = response.data[0]["id"] if response.data else None
        return {
            "success": True,
            "user_id": user_id,
            "message": "User created successfully"
        }
    except Exception as e:
        print("Exception in /api/users:", e)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    ) 