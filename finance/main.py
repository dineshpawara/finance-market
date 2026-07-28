from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Finance Brain API")

from config import settings
from controllers import getDummy

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def root():
    return {"Status": "OK"} 

app.include_router