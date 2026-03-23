from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.base.middleware import LoggingMiddleware
from app.core.config import settings
from app.core.exceptions import (
    BaseAPIException, 
    custom_exception_handler, 
    global_exception_handler
)


from app.api.api import api_router
from app.core.log import setup_logging
from fastapi.middleware.cors import CORSMiddleware 


@asynccontextmanager        
async def lifespan(app: FastAPI):
    setup_logging()
    yield

app = FastAPI(
    title="Sample FastAPI",
    description="Sample FastAPI",
    version="0.1.0",
    lifespan=lifespan
)

# 미들웨어 등록
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 배포 시 수정 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router)

# 에러 핸들러 등록
# 1. 커스텀 에러(우리가 던진 에러) 담당자 배정
app.exception_handler(BaseAPIException)(custom_exception_handler)
# 2. 그 외 파이썬 최상위 에러(예상치 못한 버그) 담당자 배정
app.exception_handler(Exception)(global_exception_handler)

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/api/hello")
def hello():
    return {"message": "hello from fastapi"}

