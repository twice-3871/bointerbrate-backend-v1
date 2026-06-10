import db

def get_user_by_discord_id(discord_id: int):
    return db.fetch_one(
    """
    SELECT discord_id, username, avatar
    FROM users
    WHERE discord_id = %s
    """, (discord_id,))


def upsert_user(
    discord_id: int,
    username: str,
    avatar: str | None
):
    return db.fetch_one(
        """
        INSERT INTO users 
        (discord_id, username, avatar)
        VALUES (%s, %s, %s)
        ON CONFLICT (discord_id)
        DO UPDATE SET
            username = EXCLUDED.username,
            avatar = EXCLUDED.avatar
        RETURNING discord_id, username, avatar
        """,
        (
            discord_id,
            username,
            avatar
        ))