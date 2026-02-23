from fastapi import APIRouter, Depends


health_router = APIRouter(prefix="/health", tags=["Health"], dependencies=[])

user_router = APIRouter(prefix="/users", tags=["Users"], dependencies=[])
