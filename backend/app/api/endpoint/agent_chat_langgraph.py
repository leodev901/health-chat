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
from langgraph.graph import StateGraph, START, END

from typing import TypedDict, List, Tuple, Optional


from app.api.prompt import (
    SYSTEM_PROMPT,
    INTENT_PLAN_PROMPT,
    SUMMURAIZE_ANSER_PROMPT
)


from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException

agent_chat_graph_router = APIRouter(prefix="/api", tags=["agent"])

# PROVIDER = settings.PROVIDER.upper()
PROVIDER = "GEMINI"

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


class AgentState(TypedDict, total=False):
    # API 요청에서 들어오는 기본 값 초기 세팅 
    session_id:str
    user_id:str
    query:str
    memory:list[tuple[str,str]] # 이번 seesion_id의 메모리

    # planner가 채우는 값
    intent: str
    tool_plan: list[tuple[str, str]]
    reason: str

    # excutor가 채우는 값
    steps: list[dict] 
    has_error: bool 
    error_message: Optional[str]

    # executor 실행 제어
    current_step:int
    next:str

    #reporter가 채우는 값
    final_answer: str


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




def planner_node(state: AgentState) -> AgentState:
    # planner의 책임:
    # 1) 사용자 질문과 memory를 읽는다.
    # 2) intent를 분류한다.
    # 3) 어떤 tool들을 어떤 순서로 실행할지 계획(tool_plan)을 만든다.
    #
    # 중요한 점:
    # LangGraph 노드는 "state 전체를 수정"하는 느낌보다
    # "내가 갱신한 필드만 반환"한다고 생각하면 이해가 쉽습니다.

    query=state["query"]
    memory=state["memory"]

    prompt = INTENT_PLAN_PROMPT.format(
        query=query,
        memory=build_memory(memory),
    )

    response = call_llm(prompt)
    clean_response = extract_json_text(response)
    print(response)

    try:
        data = json.loads(clean_response)
        pared = PlanResult(**data)
    except Exception as e:
        raise ValueError(f"intent JSON 파싱 실패: {clean_response}") from e

    tool_plan = pared.tool_plan
    next="executor" if len(tool_plan) > 0 else "reporter"
    
    return {
        "intent":pared.intent,
        "tool_plan":pared.tool_plan,
        "reason":pared.reason,
        "next":next,
    }


    

def executor_node(state: AgentState) -> AgentState:
    # executor의 책임:
    # planner가 만든 tool_plan을 순서대로 실행해서
    # steps 리스트에 실행 결과를 누적합니다.
    # [주의] 더 이상 실행 할 tool이 없다면 reptorter로 넘어갑니다.

    current_step = state["current_step"]
    tool_name, tool_input = state["tool_plan"][current_step]
    
    has_error=False

    try:
        answer = tool_dispatch(tool_name, tool_input, state["memory"])
    except Exception as e:
        answer = "[tool_error] 잠시 후 다시 시도해주세요."
        has_error = True
        error_message = str(e)
    
    steps = state["steps"]
    steps.append(
        {
            "tool_name":tool_name,
            "tool_input":tool_input,
            "tool_result":answer
        }
    )

    if has_error:
        return {
            "next":"reporter",
            "steps":steps,
            "has_error":has_error,
            "error_message":error_message
        }
    
    # 다음 step 판단
    current_step+=1
    next = "executor" if current_step < len(state["tool_plan"]) else "reporter"

    return {
        "next":next,
        "steps":steps,
        "current_step":current_step,
    }

def reporter_node(state: AgentState) -> AgentState:
    # reporter의 책임:
    # executor 결과(steps)와 intent를 읽어서
    # 사용자에게 보여줄 최종 final_answer를 만듭니다.

    if state["has_error"]:
        return {
            "final_answer":"Tool 도구 사용 중 오류가 발생했습니다."
        }
    elif state["intent"] == "기타":
        return {
            "final_answer":"처리 가능한 문의가 없습니다."
        }
    
    
    prompt = SUMMURAIZE_ANSER_PROMPT.format(
        query=state["query"],
        intent=state["intent"],
        steps=state["steps"],
        memory=build_memory(state["memory"])
    )
    
    final_answer = call_llm(prompt)
    return {
        "final_answer":final_answer
    }


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


def tool_dispatch(tool_name: str, tool_input: str, memory: list[tuple[str,str]]) -> str:
    TOOLS_CALL_MAP = {
        "appointment_tool":appointment_tool,
        "insurance_tool":insurance_tool,
        "info_tool":info_tool,
    }
    if tool_name not in TOOLS_CALL_MAP:
        raise ValueError(f"지원하지 않는 도구: {tool_name}")
    
    return TOOLS_CALL_MAP[tool_name](tool_input, memory)




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



def get_graph():
    
    # StateGraph는 "이 그래프가 어떤 sate 스키마를 공유할지" 먼저 정의합니다.
    graph = StateGraph(AgentState)

    # 먼저 graph에 노드를 등록한다.
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reporter", reporter_node)

    # graph의 흐름(workflow)를 정의합니다.
    # 시작은 planner
    graph.add_edge(START,"planner")
    graph.add_conditional_edges(
        "planner",
        lambda state : state["next"],
        ["executor","reporter"]
    )
    graph.add_conditional_edges(
        "executor",
        lambda state : state["next"],
        ["executor","reporter"]
    )
    graph.add_edge("reporter",END)
    
    return graph.compile()



@agent_chat_graph_router.post("/agent/chat/graph", response_model=AgentResponse)
async def agent_chat(request:Request, payload:AgentRequest):
    logger.info(f"요청 시작 payload: {payload}")

    session_id = payload.session_id
    user_id=payload.user_id
    query = payload.query.strip()
    clean_query = query.lower()

    # SESSION_MEMORY 초기화
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = []
    
    memory = SESSION_MEMORY[session_id][:] # 해당 세션의 대화 히스톨 복제

    # 초기 스테이트 생성
    state = AgentState(
        session_id=session_id,
        user_id=user_id,
        query=clean_query,
        memory=memory,
        current_step=0,
        steps=[],
        has_error=False,
        error_message=None,
    )

    # langgraph 실행
    graph = get_graph()
    final_state = graph.invoke(state)


    # To-Do session memory 유지
    SESSION_MEMORY[session_id].append(("user",query))
    SESSION_MEMORY[session_id].append(("assistant",final_state["final_answer"]))

    if len(SESSION_MEMORY[session_id])> 10:
        SESSION_MEMORY[session_id].pop(0)
        SESSION_MEMORY[session_id].pop(0)
        

    # API 반환 structured output 반환
    return AgentResponse(
        session_id= session_id,
        intent= final_state["intent"],
        tools_used= [tool_name for tool_name, tool_input in final_state["tool_plan"]],
        steps= final_state["steps"],
        final_answer= final_state["final_answer"],
        memory_size= len(SESSION_MEMORY[session_id])
    )

    
