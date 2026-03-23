from fastapi import FastAPI
from contextlib import asynccontextmanager
from base.middleware import LoggingMiddleware
from core.config import settings
from core.exceptions import (
    BaseAPIException, 
    custom_exception_handler, 
    global_exception_handler
)


from core.log import setup_logging 


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


from core.exceptions import NotFoundException # [추가] 임포트 잊지마세요!

@app.get("/api/test-custom-error")
def test_custom_error():
    # 1. 우리가 의도하고 에러를 던질 때 (raise)
    # 이제부터 실무에서 데이터가 없으면 무조건 raise NotFoundException() 한 줄만 치면 끝납니다!
    raise NotFoundException(message="사용자님의 장바구니 데이터를 찾지 못했어요.")
@app.get("/api/test-fatal-error")
def test_fatal_error():
    # 2. 주니어 개발자의 실수로 터진 버그 (0으로 나누기)
    return 10 / 0

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.APP_HOST, 
        port=settings.APP_PORT,
        log_level=settings.APP_LOG_LEVEL
    )