from fastapi import APIRouter


health_router = APIRouter(prefix="/health", tags=["Health"], dependencies=[])

user_router = APIRouter(prefix="/users", tags=["Users"], dependencies=[])

auth_router = APIRouter(prefix="/auth", tags=["Authentication"], dependencies=[])

claims_router = APIRouter(prefix="/claims", tags=["Claims"], dependencies=[])
