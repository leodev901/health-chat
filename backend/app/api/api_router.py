from fastapi import APIRouter, FastAPI
from loguru import logger


from app.api.endpoint.agent_chat import agent_chat_router
from app.api.endpoint.agent_chat_langgraph import agent_chat_langgraph_router

def register_routers(app: FastAPI):
    app.include_router(agent_chat_router)
    app.include_router(agent_chat_langgraph_router)
    logger.info("라우터 등록 완료")



