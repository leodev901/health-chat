import json
import re
from typing import Literal
from fastapi import APIRouter, Request
from loguru import logger
from pydantic import BaseModel
from loguru import logger
from openai import OpenAI
from google import genai
from google.genai import types


from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException

from app.api.prompt import (
    SYSTEM_PROMPT,
    INTENT_PLAN_PROMPT,
    SUMMURAIZE_ANSER_PROMPT
)


agent_chat_router = APIRouter(prefix="/api", tags=["agent"])


# PROVIDER = settings.PROVIDER.upper()
PROVIDER = "OPENAI"

if PROVIDER == "OPENAI":
    if not settings.OPENAI_API_KEY.strip():
        raise ServiceUnavailableException("OPENAI_API_KEY가 설정되지 않았습니다.")
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    MODEL = settings.OPENAI_MODEL
else: #GEMINI
    if not settings.GEMINI_API_KEY.strip():
        raise ServiceUnavailableException("GEMINI_API_KEY가 설정되지 않았습니다.")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    MODEL = settings.GEMINI_MODEL

SESSION_MEMORY: dict[str, list[tuple[str,str]]] = {}




class AgentRequest(BaseModel):
    session_id:str
    user_id:str
    query:str

class StepResult(BaseModel):
    tool_name:str
    tool_input:str
    tool_result:str

class AgentResponse(BaseModel):
    session_id:str
    intent:str
    # tool_used: str | None
    # answer: str
    tools_used: list[str]
    steps:list[StepResult]
    final_answer:str
    memory_size:int=0

class PlanResult(BaseModel):
    intent: Literal["예약", "보험", "안내", "복합", "기타"]
    tool_plan: list[tuple[str, str]]
    reason: str



def call_llm(prompt: str):
    print(prompt)
    if PROVIDER == "OPENAI":
        response = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return response.output_text.strip()
    else:
        # GEMINI
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                # 모델의 역할/행동 규칙을 지정
                system_instruction=SYSTEM_PROMPT,
                # 필요하면 생성 옵션도 같이 넣을 수 있음
                # temperature=0.1,
            ),
        )
        return response.text.strip()

def build_memory( memory:list[tuple[str,str]] ) -> str:  
    print("build_memory")
    history = []
    
    for mem in memory:
        print(f"{mem[0]}: {mem[1]}")
        history.append(f"{mem[0]}: {mem[1]}")

    # return "\n".join( memory if memory else "(없음)" )
    return "\n".join( history )  if history else "(없음)" 
    
    


def extract_json_text(response: str) -> str:
    response = response.strip()

    fenced_match = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        response,
        re.DOTALL | re.IGNORECASE,
    )
    if fenced_match:
        return fenced_match.group(1).strip()

    return response



# llm으로 의도 파악
def classify_intent_llm(query: str, memory: list[tuple[str,str]]) -> tuple[ str, list[tuple[str, str]] ]:
    prompt = INTENT_PLAN_PROMPT.format(
        memory=build_memory(memory),
        query=query
    )

    response = call_llm(prompt)
    print(response)
    clean_response = extract_json_text(response)

    try:
        data = json.loads(clean_response)
        pared = PlanResult(**data)
        # intent = data["intent"]
        # plan = [ (p[0],p[1]) for p in data["tool_plan"] ]

        return (pared.intent, pared.tool_plan)
    except Exception as e:
        raise ValueError(f"intent JSON 파싱 실패: {clean_response}") from e

def appointment_tool(query: str, memory: list[tuple[str,str]]) -> str:
    if "취소" in query:
        return "[예약] 예약 취소를 도와드릴게요."
    if "변경" in query:
        return "[예약] 예약 변경을 도와드릴게요."
    if "접수" in query:
        return "[예약] 예약 접수를 도와드릴게요."
    return "[예약] 내일 예약 가능합니다."

def insurance_tool(query: str, memory: tuple[str,str]) -> str:
    return "[보험] 실손보험 청구 서류는 신분증, 진료비 영수증입니다."

def info_tool(query: str, memory: tuple[str,str]) -> str:
    if "시간" in query or "운영" in query or "진료시간" in query:
        return f"[안내] 운영시간은 평일 09:00~18:00입니다."
    if "지도" in query or "위치" in query:
        return f"[안내] 병원 위치는 성북구 화랑로22길 입니다."
    return f"[안내] 기타 안내문의는 홈페이지를 확인해주세요."



def compose_final_answer(steps: list[StepResult], intent: str) -> str:
    if intent == "기타":
        return "처리 가능한 문의가 없습니다."
    final_answer = ""
    for step in steps:
        final_answer += f" {step.tool_result}"
    return final_answer.strip()


def summurize_final_anser(query:str, intent:str, steps:list[StepResult], memory:list[tuple[str,str]])->str:
    prompt = SUMMURAIZE_ANSER_PROMPT.format(
        query=query,
        intent=intent,
        steps=steps,
        memory=build_memory(memory)
    )
    return call_llm(prompt)
    

def tool_dispatch(tool_name: str, tool_input: str, memory: list[tuple[str,str]]) -> str:
    TOOLS_CALL_MAP = {
        "appointment_tool":appointment_tool,
        "insurance_tool":insurance_tool,
        "info_tool":info_tool,
    }
    if tool_name not in TOOLS_CALL_MAP:
        raise ValueError(f"지원하지 않는 도구: {tool_name}")
    
    return TOOLS_CALL_MAP[tool_name](tool_input, memory)



@agent_chat_router.post("/agent/chat", response_model=AgentResponse)
async def agent_chat(request:Request, payload:AgentRequest):
    logger.info(f"요청 시작 payload: {payload}")

    session_id = payload.session_id
    query = payload.query.strip()
    clean_query = query.lower()


    # 세션 메모리 확인
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = []
    
    memory = SESSION_MEMORY[session_id][:]

    # LLM으로 intent와 tool plan을 한 번에 세운다.
    intent, plan = classify_intent_llm(clean_query, memory)
    logger.info(f"intent 분류 결과: {intent}")
    logger.info(f"실행할 tool 목록: {plan}")
    

    # To-Do multi-step 처리
    steps = []
    has_error = False
    for tool_name, tool_input in plan:
        try:
            answer = tool_dispatch(tool_name, tool_input, memory)
        except Exception as e:
            answer = "[error ]잠시 후 다시 시도해주세요."
            has_error = True
            logger.error(f"error: {e}")

        steps.append(
                StepResult(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_result=answer,
                )
            )
        
    if has_error:
        final_answer = "처리중 오류가 발생했습니다."
    elif intent == "기타":
        final_answer = "처리 가능한 문의가 없습니다."
    else:
        final_answer = summurize_final_anser(query, intent, steps, memory)    

    logger.info(f"최종 응답 요약: {final_answer}")

    # To-Do session memory 유지
    SESSION_MEMORY[session_id].append(("user",query))
    SESSION_MEMORY[session_id].append(("assistant",final_answer))

    if len(SESSION_MEMORY[session_id])> 5:
        SESSION_MEMORY[session_id].pop(0)
    
    for session in SESSION_MEMORY:
        print(f"{session} : {SESSION_MEMORY[session]}")


    # To-Do structured output 반환
    return AgentResponse(
        session_id= session_id,
        intent= intent,
        tools_used= [tool_name for tool_name, tool_input in plan],
        steps= steps,
        final_answer= final_answer,
        memory_size= len(SESSION_MEMORY[session_id])
    )
