
import streamlit as st
import requests
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

# 1. 환율 조회 도구 생성
@tool
def get_exchange_rate(base: str, quote: str, amount: float = 1.0) -> str:
    """Frankfurter API로 환율과 환전 금액을 조회한다.
    통화는 USD, KRW, JPY 등 3자리 코드를 사용한다.
    """

    base = base.upper()
    quote = quote.upper()

    if base == quote:
        return f"{amount:,.2f} {base} = {amount:,.2f} {quote}"

    url = f"https://api.frankfurter.dev/v2/rate/{base}/{quote}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        rate = data["rate"]
        result = amount * rate

        return (
            f"기준 통화: {base}\n"
            f"대상 통화: {quote}\n"
            f"1 {base} 환율: {rate:,.4f} {quote}\n"
            f"환산 금액: {amount:,.2f} {base} = {result:,.2f} {quote}\n"
            f"환율 기준일: {data['date']}"
        )

    except (requests.exceptions.RequestException, ValueError, KeyError):
        return "환율 조회에 실패했습니다."


# 2. AI 모델 및 Agent 생성
model = init_chat_model("gpt-5.4-mini")

agent = create_agent(
    model,
    tools=[get_exchange_rate],
    system_prompt="""
    당신은 환율 조회 AI 챗봇입니다.
    환율 질문을 받으면 반드시 get_exchange_rate 도구를 사용하세요.
    별도 언급이 없다면 대상 통화는 KRW로 설정하세요.
    이전 대화를 참고해 후속 질문을 이해하세요.
    환율, 환산 금액, 환율 기준일을 보기 좋게 정리하세요.
    조회에 실패하면 환율을 추측하지 마세요.
    한국어로 친절하게 답변하세요.
    """
)

# 3. 화면 구성
st.title("💱 실시간 환율 챗봇")
st.caption("Frankfurter의 최신 일별 기준 환율을 조회합니다. 실시간 금융시장 체결가는 아닙니다.")
st.info("예시: 100달러는 원화로 얼마야?, 1유로는 엔화로 얼마야?")

# 4. 채팅 기록 저장
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. 사용자 질문 입력
prompt = st.chat_input("환율이나 환전할 금액을 질문해 보세요.")

if prompt:
    response = agent.invoke({
        "messages": st.session_state.messages + [
            {"role": "user", "content": prompt}
        ]
    })

    answer = response["messages"][-1].content

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

# 6. 채팅 내역 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
