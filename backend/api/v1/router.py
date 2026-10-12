from fastapi import APIRouter
from routes.v1 import users, authentication, two_factor

api_v1_router = APIRouter()

api_v1_router.include_router(users.userRoute)
api_v1_router.include_router(authentication.authRoute)
api_v1_router.include_router(two_factor.twoFactorRoute)
