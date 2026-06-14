import db
from services import auth_service
from schemas import level
from fastapi import APIRouter
from fastapi import Depends, HTTPException

levels_router = APIRouter(prefix="/levels", tags=["levels"])

@levels_router.get("/all")
async def get_all_levels():
    levels = db.fetch_all("""
    SELECT levels.*, level_positions.level_pos
    FROM levels
    INNER JOIN level_positions
    ON levels.id = level_positions.level_id
    ORDER BY level_pos ASC;
    """)
    
    return levels

@levels_router.get("/{level_id}")
async def get_a_level_and_its_records(level_id: int):
    levels = db.fetch_one("""
    SELECT levels.*, level_positions.level_pos
    FROM levels
    INNER JOIN level_positions
    ON levels.id = level_positions.level_id
    WHERE levels.level_id = %s
    """, (level_id,))

    level_records = db.fetch_all(
        """
        SELECT user_record_submissions.progress,
        user_record_submissions.video_url,
        user_record_submissions.created_at,
        users.username
        FROM levels
        INNER JOIN user_record_submissions
        ON user_record_submissions.level_id = levels.level_id AND user_record_submissions.status = 'approved'
        INNER JOIN users
        ON user_record_submissions.user_id = users.discord_id
        WHERE levels.level_id = %s;
        """, (level_id,)
    )
    
    return {
        "Level": levels,
        "Records": level_records
    }

@levels_router.get("/{level_type}/all")
async def get_all_levels_speific_type(level_type: level.LevelType):
    levels = db.fetch_all("""
    SELECT levels.*, level_positions.level_pos
    FROM levels
    INNER JOIN level_positions
    ON levels.id = level_positions.level_id
    WHERE levels.type_of_level = %s
    ORDER BY level_pos ASC;
    """, (level_type.value,))
    
    return levels

@levels_router.delete("/{level_id}")
def delete_level(
    level_id: int,
    discord_id: str = Depends(auth_service.get_current_user)):

    find_level = db.fetch_one(
        """
        SELECT 
        levels.*, 
        level_positions.level_pos 
        FROM levels 
        INNER JOIN level_positions
        ON levels.id = level_positions.level_id
        WHERE levels.level_id = %s;
        """, (level_id,)
    )

    print(find_level)

    deleted_pos = find_level["level_pos"]
    deleted_type = find_level["type_of_level"]

    db.execute(
    """
    DELETE FROM levels
    WHERE level_id = %s
    """, (level_id,)
    )


    db.execute(
    """
    UPDATE level_positions
    SET level_pos = level_pos - 1
    WHERE type_of_level = %s
    AND level_pos > %s
    """, (
        deleted_type,
        deleted_pos,
    ))


    return {"Success": True}




@levels_router.post("/")
async def add_level(
    level: level.CreateLevel,
    discord_id: str = Depends(auth_service.get_current_user)
    ):
    if level.level_pos <= 0:
        level.level_pos = 1

    try:
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
    except Exception:
        print("DB insert failed:", Exception)
        raise HTTPException(status_code=400, detail="Invalid level data")

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

