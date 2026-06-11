import jwt
import os
import db
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security    = HTTPBearer()
SECRET_KEY  = os.getenv("SECERT_KEY")


def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms="HS256")
    except jwt.InvalidTokenError:
        return None

def is_allowed(discord_id: str):
    user = db.fetch_one(
        """
        SELECT discord_id FROM allowed_users WHERE discord_id = %s
        """, (discord_id,)
    )

    return user is not None

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
    

    if not is_allowed(discord_id):
        raise HTTPException(status_code=403, detail="Not allowed")
    
    return discord_id