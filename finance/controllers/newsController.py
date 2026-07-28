from fastapi import APIRouter

from models.newsSchema import NewsItemResponse


router = APIRouter(prefix="/news", tags=["news"])

router.get("/latest", response_model=list[NewsItemResponse])