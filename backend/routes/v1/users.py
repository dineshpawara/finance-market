from fastapi import APIRouter

from core.logging_config import app_logger

userRoute = APIRouter(prefix="/users", tags=["Users V1"])


@userRoute.get("/")
def get_users():
    app_logger.info("Fetching users list from API V1")
    return {"message": "Get Users from API V1", "users": []}
