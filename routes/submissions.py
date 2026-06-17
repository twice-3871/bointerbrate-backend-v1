import db
from services import auth_service
from schemas import submission
from fastapi import APIRouter
from fastapi import Depends, HTTPException
from fastapi import Request

submission_router = APIRouter(prefix="/submit", tags=["submit"])

@submission_router.get("/")
def get_all_submissions():
    return  db.fetch_all(
        """
        SELECT 
            users.username, 
            levels.level_name, 
            user_record_submissions.*
        FROM user_record_submissions
        INNER JOIN users
        ON user_record_submissions.user_id = users.discord_id 
        INNER JOIN levels
        ON user_record_submissions.level_id = levels.level_id;
        """
    )

@submission_router.post("/")
def post_submission(
    User_submission: submission.CreateSubmissionModel,
    current_user = Depends(auth_service.get_current_user)):
    try:
        db.execute(
            """
            INSERT INTO user_record_submissions 
            (user_id,
            level_id,
            progress,
            video_url,
            status) VALUES (%s, %s, %s, %s, %s)
            """, (
                current_user["discord_id"],
                User_submission.level_id,
                User_submission.progress,
                User_submission.video_url,
                "pending",
            )
        )
    except Exception as e:
        print("DB insert failed:", e)
        raise HTTPException(status_code=400, detail="Invalid record submission data")
    
    submission = db.fetch_one(
        """
        SELECT * FROM user_record_submissions WHERE level_id = %s
        """, (User_submission.level_id,))
    
    return {
        "message": "Success!",
        "submission": submission
    }

@submission_router.patch("/{submission_id}/approve")
def approve_submission(
    submission_id: int,
    discord_id: str = Depends(auth_service.get_current_user)):

    db.execute(
        """
        UPDATE user_record_submissions
        SET status = 'approved'
        WHERE id = %s;
        """, (submission_id,)
    )

    return {"success": True}

@submission_router.patch("/{submission_id}/reject")
def reject_submission(
    submission_id: int,
    discord_id: str = Depends(auth_service.get_current_user)):
    db.execute(
        """
        UPDATE user_record_submissions
        SET status = 'rejected'
        WHERE id = %s;
        """, (submission_id,)
    )

    return {"success": True}