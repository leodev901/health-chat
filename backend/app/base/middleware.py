# app/base/middleware.py
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. CORS Preflight 요청 등 로깅이 불필요한 요청은 바로 패스
        if request.method == "OPTIONS":
            return await call_next(request)

        # 2. 고유 추적 ID 생성 및 요청 시작 시간 기록
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id  # 뒤에 실행될 라우터에서 쓸 수 있게 저장
        start_time = time.time()

        # [요청 껍데기 로깅] Query Parameter는 에러 안 나고 안전하게 읽음
        query_params = request.url.query
        logger.info(f"[{request_id}] ---> Request: {request.method} {request.url.path} | Query: {query_params}")

        # 3. 다음 미들웨어나 실제 API 함수 호출
        response = await call_next(request)

        # 4. 소요 시간 계산 및 상태값 산출
        duration = time.time() - start_time
        status_str = "SUCCESS" if response.status_code < 400 else "FAIL"

        # [응답 헤더 세팅] 클라이언트도 자기가 무슨 ID로 요청했는지 알도록 헤더에 박아줌
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Duration-Time"] = f"{duration:.4f}"

        # [응답 껍데기 로깅] 
        logger.info(f"[{request_id}] <--- Response: {status_str} ({response.status_code}) | Time: {duration:.4f}s")

        return response
