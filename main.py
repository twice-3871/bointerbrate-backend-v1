from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from level import CreateLevel
from level import LevelType
from dotenv import load_dotenv
from datetime import datetime, timedelta
import httpx
import jwt
import db
import os


app             = FastAPI()
security        = HTTPBearer()
CLIENT_ID       = os.getenv("CLIENT_ID")
CLIENT_SECRET   = os.getenv("CLIENT_SECRET")
CALLBACK_URL    = "http://localhost:8000/auth/callback"
SECRET_KEY      = os.getenv("SECERT_KEY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms="HS256")
    except jwt.InvalidTokenError:
        return None

@app.get("/auth/login")
async def login():
    return RedirectResponse(
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={CALLBACK_URL}"
        f"&response_type=code"
        f"&scope=identify"
    )

@app.get("/auth/callback")
async def callback(code: str):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": CALLBACK_URL
            }
        )
    
        token = token_response.json()["access_token"]
        user_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        discord_user = user_response.json()
        print(discord_user)
    

    user = db.fetch_one("""
    SELECT * FROM users WHERE discord_id = %s
    """, (discord_user["id"],))

    if not user:
        db.execute("""
        INSERT INTO users 
        (discord_id, username, avatar)
        VALUES (%s, %s, %s)
        """,
        (
            discord_user["id"],
            discord_user["username"],
            discord_user["avatar"]
        ))

        user = db.fetch_one("""
        SELECT * FROM users WHERE discord_id = %s
        """, (discord_user["id"],))

    jwt_token = jwt.encode(
        {
        "user_id": user["id"],
        "discord_id": discord_user["id"],
        "exp": datetime.utcnow() + timedelta(days=30)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    return RedirectResponse(
        url=f"http://localhost:5173/auth/callback?token={jwt_token}"
    )

@app.get("/me")
async def get_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    data = decode_token(token)
    print(data)

    if not data:
        raise HTTPException(status_code=401, detail="Invalid Token")
    
    discord_id = data["discord_id"]

    user = db.fetch_one(
        """
        SELECT discord_id, username, avatar
        FROM users
        WHERE discord_id = %s
        """, (discord_id,))
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    print(user)
    
    return {
        "id": user['discord_id'],
        "username": user['username'],
        "avatar": user['avatar']
    }


@app.get("/")
async def root():
    levels = db.fetch_all("""
    SELECT levels.*, level_positions.level_pos
    FROM levels
    INNER JOIN level_positions
    ON levels.id = level_positions.level_id
    ORDER BY level_pos ASC;
    """)
    
    return levels

@app.get("/{level_type}")
async def root(level_type: LevelType):
    levels = db.fetch_all("""
    SELECT levels.*, level_positions.level_pos
    FROM levels
    INNER JOIN level_positions
    ON levels.id = level_positions.level_id
    WHERE levels.type_of_level = %s
    ORDER BY level_pos ASC;
    """, (level_type.value,))
    
    return levels


@app.post("/")
async def add_level(level: CreateLevel):
    if level.level_pos <= 0:
        level.level_pos = 1


    level_row = db.fetch_one("""
    INSERT INTO levels 
    (type_of_level, 
    level_name, 
    creator, 
    level_id, 
    song, 
    verification_url) VALUES 
    (%s, %s, %s, %s, %s, %s) 
    RETURNING id""", (level.level_type, level.level_name, level.level_creator, level.level_id, level.level_song, level.level_verification_url,))


    find_other_lvls_pos = db.fetch_all("""
    SELECT * FROM level_positions 
    WHERE level_pos >= %s 
    AND type_of_level = %s
    """, (level.level_pos, level.level_type,))

    for level_pos_t in find_other_lvls_pos:
        level_pos_t['level_pos'] += 1

        db.execute("""
        UPDATE level_positions
        SET level_pos = %s
        WHERE level_id = %s
        """, (level_pos_t['level_pos'], level_pos_t['level_id']))

        print(level_pos_t)


    level_pos = db.fetch_one("""
    INSERT INTO level_positions (
    level_id, 
    level_pos,
    type_of_level
    ) VALUES (%s, %s, %s) 
    RETURNING level_pos""", (level_row['id'], level.level_pos, level.level_type,))

    return {
        "message": "Level added!",
        "level": level
    }