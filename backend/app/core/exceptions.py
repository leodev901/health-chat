from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

# 1. 우리 프로젝트의 '모든 에러'들의 어머니가 될 부모 클래스입니다.
class BaseAPIException(Exception):
    def __init__(self, status_code: int, error_code:str, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message

# 2. 부모 클래스를 상속받아, 실무에서 자주 쓸 "자식 에러"들을 양산해 둡니다.
class NotFoundException(BaseAPIException):
    def __init__(self, message: str = "요청하신 데이터를 찾을 수 없습니다."):
        # 2. 부모 클래스를 상속받아, 실무에서 자주 쓸 "자식 에러"들을 양산해 둡니다.
        super().__init__(status_code=404, error_code="NOT_FOUND", message=message)

class BadRequestException(BaseAPIException):
    def __init__(self, message: str = "잘못된 요청입니다."):
        super().__init__(status_code=400, error_code="BAD_REQUEST", message=message)

class UnauthorizedException(BaseAPIException):
    def __init__(self, message: str = "인증되지 않은 요청입니다."):
        super().__init__(status_code=401, error_code="UNAUTHORIZED", message=message)

class ForbiddenException(BaseAPIException):
    def __init__(self, message: str = "권한이 없는 요청입니다."):
        super().__init__(status_code=403, error_code="FORBIDDEN", message=message)


# =====================================================================
# 3. 이제, 위에서 만든 에러(불량 딱지)가 던져졌을 때 가로채서 처리할 "에러 전담반(Handler)" 함수들입니다.

async def custom_exception_handler(request: Request, exc: BaseAPIException):
    """의도하고 던진 에러(BaseAPIException)를 처리하는 전담"""
    # 미들웨어에서 넣어둔 요청 ID를 로그 추적용으로 꺼내옵니다.
    request_id = getattr(request.state, "request_id", "Unknown")

    # 여기서 경고(Warning) 로그를 남기면 디버깅이 편해집니다.
    logger.error(
        f"[Request ID: {request_id}] "
        f"Client Error: {exc.status_code} - {exc.error_code} | "
        f"Message: {exc.message}"
    )

    # 프론트엔드나 클라이언트가 파싱하기 좋은 형태(JSON)로 예쁘게 포장해서 돌려줍니다.
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message
            },
            "meta": {"request_id": request_id}
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    """예상치 못한 500번대 진짜 버그(예: DB 터짐, NoneType 에러 등)를 처리하는 전담"""
    request_id = getattr(request.state, "request_id", "Unknown")

    # 500번대는 심각한 오류이므로 Error 레벨로 남깁니다.
    logger.error(
        f"[Request ID: {request_id}] "
        f"Internal Server Error: {type(exc).__name__} | "
        f"Message: {str(exc)}"
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            },
            "meta": {"request_id": request_id}
        }
    )