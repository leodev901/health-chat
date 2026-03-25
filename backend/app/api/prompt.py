from langchain_core.prompts import PromptTemplate 


SYSTEM_PROMPT = """
너의 역할은 병원 고객지원 에이전트입니다.
"""


INTENT_PLAN_PROMPT = PromptTemplate.from_template(
    """
아래 사용자 질문의 intent와 실행할 tool 계획을 분류해라 

분류 가능한 intent 정의
- 예약
- 보험
- 안내
- 복합
- 기타

intent 분류 기준:
- 예약: 예약, 취소, 변경, 접수, 예약 가능 여부
- 보험: 보험, 실손보험, 청구, 서류
- 안내: 위치, 어디, 지도, 운영시간, 진료시간, 확인, 조회
- 복합: 위 세가지 중 2개 이상 해당하는 경우
- 기타: 위 기준에 해당하지 않는 질문


호출 가능한 도구 정의
- appointment_tool
- insurance_tool
- info_tool

도구 실행 계획 기준
- 예약/취소는 appointment_tool을 사용한다.
- 보험은 insurance_tool을 사용한다.
- 안내는 info_tool을 사용한다.
- 기타는 tool을 호출하지 않는다. (None)
- 두 개 이상의 도구가 필요한 경우 순차적으로 사용한다.


반드시 아래 JSON 형식으로만 답해라. 마크다운 코드블록으로 감싸지 않는다.
{{
  "intent": "예약|보험|안내|복합|기타 중 하나",
  "tool_plan": [
    ["도구이름1", "질문1"],
    ["도구이름2", "질문2"]
  ],
  "reason": "왜 그렇게 분류 했는지 이유를 짧게 설명"
}}

사용자질문: {query}

최근대화: 
{memory}
""".strip()
)

SUMMURAIZE_ANSER_PROMPT = PromptTemplate.from_template(
    """
다음 주어진 정보를 종합하여 사용자 질문의 최종 답변을 간략하게 생성하라. (도구 실행 과정 간략한 요약 포함)

사용자질문:: {query}
intent:: {intent}
steps: {steps}
최근 대화: 
{memory}

""".strip()
)