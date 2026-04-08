import os
import sys
import logging
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("Booting up HeliX Coach Server...")

try:
    from google.adk.cli.fast_api import get_fast_api_app

    current_dir = os.path.dirname(os.path.abspath(__file__))

    app = get_fast_api_app(agents_dir=current_dir, web=True)
    logger.info("Agent loaded successfully via ADK FastAPI wrapper!")

except Exception as e:
    logger.critical(f"CRITICAL BOOT ERROR: {str(e)}")
    sys.exit(1)


FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/api/auth/verify")
async def verify_auth(request: Request):
    """Verify a Firebase ID token and return or create user profile.
    
    Expected body: { "idToken": "..." }
    """
    try:
        from helix_coach.firebase_auth import verify_firebase_token
        from helix_coach.database import init_pool_and_db, save_user_context, get_user_context

        body = await request.json()
        id_token = body.get("idToken")
        if not id_token:
            raise HTTPException(status_code=400, detail="Missing idToken")

        user_info = verify_firebase_token(id_token)
        user_id = user_info["uid"]
        email = user_info["email"]
        name = user_info.get("name", "")

        context = get_user_context(user_id)

        if "not found" in context.lower():
            save_user_context(user_id, email, name, "")
            return JSONResponse({
                "status": "new_user",
                "user_id": user_id,
                "email": email,
                "name": name,
            })
        else:
            return JSONResponse({
                "status": "existing_user",
                "user_id": user_id,
                "email": email,
                "name": name,
                "context": context,
            })

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Auth verification error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@app.get("/api/auth/calendar")
async def calendar_oauth_start(user_id: str):
    """Start the Google Calendar OAuth flow.
    
    Query params: ?user_id=<firebase_uid>
    Redirects to Google's consent screen.
    """
    try:
        from helix_coach.auth import get_authorization_url
        auth_url = get_authorization_url(user_id)
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Calendar OAuth start error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start calendar authorization")


@app.get("/api/auth/callback")
async def calendar_oauth_callback(code: str, state: str):
    """Handle the Google OAuth callback after user grants Calendar permission.
    
    Query params: ?code=<auth_code>&state=<user_id>
    """
    try:
        from helix_coach.auth import exchange_code_for_tokens, store_user_tokens
        from helix_coach.database import init_pool_and_db

        user_id = state
        tokens = exchange_code_for_tokens(code, user_id)

        db_pool = init_pool_and_db()
        store_user_tokens(user_id, tokens, db_pool)

        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}/dashboard?calendar=connected")

    except Exception as e:
        logger.error(f"Calendar OAuth callback error: {e}")
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}/dashboard?calendar=error")


@app.get("/api/auth/status")
async def calendar_auth_status(user_id: str):
    """Check if a user has connected their Google Calendar.
    
    Query params: ?user_id=<firebase_uid>
    """
    try:
        from helix_coach.auth import check_calendar_connected
        from helix_coach.database import init_pool_and_db

        db_pool = init_pool_and_db()
        connected = check_calendar_connected(user_id, db_pool)

        return JSONResponse({
            "user_id": user_id,
            "calendar_connected": connected,
        })
    except Exception as e:
        logger.error(f"Calendar status check error: {e}")
        raise HTTPException(status_code=500, detail="Failed to check calendar status")


@app.get("/api/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return JSONResponse({"status": "healthy", "service": "helix-coach"})



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Uvicorn on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port)