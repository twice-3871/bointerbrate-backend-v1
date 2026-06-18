import jwt
import os
import db
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security    = HTTPBearer()
SECRET_KEY  = os.getenv("SECRET_KEY")


def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms="HS256")
    except jwt.InvalidTokenError:
        return None

def is_allowed(discord_id: str):
    return db.fetch_one(
        """
        SELECT 1 FROM allowed_users WHERE discord_id = %s
        """, (discord_id,)
    ) is not None

def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security)
):
    token = creds.credentials

    try:
        payload = decode_token(token)
        discord_id = payload["discord_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token experied")
    except Exception:
        raise HTTPException(status_code=401, detail="Invaild token")

    
    return db.fetch_one(
        """
        SELECT discord_id, username FROM users WHERE discord_id = %s
        """, (discord_id)
    )

def require_allowed_user(user=Depends(get_current_user)):
    if not is_allowed(user["discord_id"]):
        raise HTTPException(403, "Not allowed")
    return user