from fastapi import APIRouter
from routes.v1 import users

api_v1_router = APIRouter()

api_v1_router.include_router(users.userRoute)
