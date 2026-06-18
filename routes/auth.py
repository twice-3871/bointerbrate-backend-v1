import db
import os
import httpx
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from datetime import datetime, timedelta
from fastapi import APIRouter
from services import user_service
from services import auth_service

security        = HTTPBearer()
CLIENT_ID       = os.getenv("CLIENT_ID")
CLIENT_SECRET   = os.getenv("CLIENT_SECRET")
CALLBACK_URL    = os.getenv("CALLBACK_URL")
SECRET_KEY      = os.getenv("SECRET_KEY")

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.get("/login")
async def login():
    return RedirectResponse(
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={CALLBACK_URL}"
        f"&response_type=code"
        f"&scope=identify"
    )

@auth_router.get("/callback")
async def callback(code: str):
    print("OAuth callback hit:", code)

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": CALLBACK_URL
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print("Status:", token_response.status_code)
        print("Headers:", token_response.headers)
        print("Body:", token_response.text)


        data = token_response.json()

        if "access_token" not in data:
            print("Discord OAuth failed: ", data)
            raise HTTPException(status_code=400, detail="OAuth failed")

        token = data["access_token"]

        user_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )


        discord_user = user_response.json()
        print(discord_user)
    

    user = user_service.upsert_user(
            discord_user["id"],
            discord_user["username"],
            discord_user["avatar"]
            )
    
    jwt_token = jwt.encode(
        {
        "user_id": user["discord_id"],
        "discord_id": discord_user["id"],
        "exp": datetime.utcnow() + timedelta(days=30)
        },
        SECRET_KEY,
        algorithm="HS256"
    )


    return RedirectResponse(
        url=f"https://test.bointerbrate.meme/auth/callback?token={jwt_token}"
    )

@auth_router.get("/me")
async def get_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    data = auth_service.decode_token(token)

    if not data:
        raise HTTPException(status_code=401, detail="Invalid Token")
    
    discord_id = data["discord_id"]

    user = user_service.get_user_by_discord_id(discord_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    
    return {
        "id": user['discord_id'],
        "username": user['username'],
        "avatar": user['avatar']
    }


