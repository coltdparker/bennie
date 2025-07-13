from fastapi import FastAPI
import os
from openai import OpenAI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/test-openai")
def test_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return JSONResponse(status_code=500, content={"error": "OPENAI_API_KEY not set in environment"})
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        # Just return the first model's id to avoid huge payloads
        first_model = models.data[0].id if hasattr(models, 'data') and models.data else None
        return {"success": True, "first_model": first_model, "model_count": len(models.data) if hasattr(models, 'data') else 'unknown'}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)}) 