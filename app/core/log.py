import sys
from loguru import logger
from core.config import settings

def setup_logging():
    """앱 시작 시 1번만 호출하여 전체 로거(Logger) 설정을 초기화합니다."""
    
    # 1. FastAPI나 Uvicorn이 기본적으로 찍어대는 기본 로거들을 싹 지웁니다. 
    # (우리가 만든 loguru 설정만 타도록 하기 위함)
    logger.remove() 
    
    # 2. 콘솔(터미널)에 찍힐 로그 포맷을 정의합니다.
    # (시간 | 레벨 | 모듈명:함수명:라인 - 메시지)
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | " \
                 "<level>{level: <8}</level> | " \
                 "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - " \
                 "<level>{message}</level>"
    
    # 3. 설정 적용 (sys.stderr는 콘솔(터미널)을 의미합니다.)
    logger.add(
        "logs/app.log",             # 저장될 파일 경로 (프로젝트 최상단 logs/ 폴더 하드디스크에 쌓임)
        rotation="10 MB",           # [핵심] 파일이 10MB가 넘어가면 쪼개서 새 파일을 만듦 (서버 용량 폭발 방지)
        retention="14 days",        # [핵심] 만들어진지 14일이 지난 오래된 로그 파일은 자동 삭제
        compression="zip",          # 다 쓴 로그는 압축해서 용량 절약
        serialize=True,             # [핵심] JSON 포맷으로 출력 (Datadog, ElasticSearch 등이 파싱하기 매우 쉬워짐)
        level=settings.APP_LOG_LEVEL.upper()
    )
    logger.info("Loguru 로깅 시스템 초기화 완료!")