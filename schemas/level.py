from pydantic import BaseModel
from enum import Enum

class LevelType(str, Enum):
    classic = "classic"
    challenge = "challenge"
    platformer = "platformer"

class CreateLevel(BaseModel):
    level_type: LevelType
    level_name: str
    level_creator: str
    level_song: str
    level_verification_url: str
    level_pos: int
    level_id: int