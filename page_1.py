
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
    당신은 친절한 환율 조회 AI 챗봇입니다.

    환율 질문을 받으면 반드시 get_exchange_rate 도구를 사용하세요.
    별도 언급이 없다면 대상 통화는 KRW로 설정하세요.
    이전 대화를 참고해 후속 질문을 이해하세요.

    답변은 다음과 같이 정리하세요.
    - 기준 통화
    - 대상 통화
    - 1단위 환율
    - 환산 금액
    - 환율 기준일

    조회에 실패하면 환율을 추측하지 마세요.
    Frankfurter는 최신 일별 기준 환율을 제공하며,
    실시간 금융시장 체결가는 아니라는 점을 안내하세요.

    한국어로 자연스럽고 친절하게 답변하세요.
    """
)



# 3. 화면 구성
st.title("💱 Exchange Mate")
st.caption("AI CURRENCY ASSISTANT")
st.write("AI와 대화하며 전 세계 환율을 간편하게 확인하세요.")
st.divider()

# 4. 채팅 기록 저장
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. 사이드바
with st.sidebar:
    st.header("💱 Exchange Mate")
    st.write("AI 환율 조회 서비스")
    st.divider()

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("데이터 제공: Frankfurter API")
    st.caption("최신 일별 기준 환율을 사용합니다.")

# 6. 첫 화면 안내
prompt = None

if not st.session_state.messages:
    with st.container(border=True):
        st.subheader("👋 안녕하세요!")
        st.write("어떤 환율이 궁금하신가요?")
        st.write("궁금한 내용을 직접 입력하거나 아래 질문을 선택해 보세요.")

    st.write("**💡 추천 질문**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💵 100달러는 몇 원이야?", use_container_width=True):
            prompt = "100달러는 원화로 얼마야?"

        if st.button("🇪🇺 오늘 유로 환율 알려줘", use_container_width=True):
            prompt = "오늘 유로 환율 알려줘."

    with col2:
        if st.button("🇯🇵 1,000엔은 얼마야?", use_container_width=True):
            prompt = "1000엔은 원화로 얼마야?"

        if st.button("💱 50만원은 몇 달러야?", use_container_width=True):
            prompt = "50만원은 몇 달러야?"

# 7. 이전 대화 출력
for message in st.session_state.messages:
    if message["role"] == "user":
        avatar = "👤"
    else:
        avatar = "🤖"

    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 8. 사용자 질문 입력
chat_prompt = st.chat_input("환율에 대해 무엇이든 물어보세요...")

if chat_prompt:
    prompt = chat_prompt

# 9. AI Agent 실행
if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("💱 환율을 조회하고 있어요..."):
            response = agent.invoke({
                "messages": st.session_state.messages
            })

            answer = response["messages"][-1].content
            st.markdown(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

# 10. 하단 안내
st.caption("※ Frankfurter의 일별 기준 환율이며 실제 환전 시 적용 환율과 다를 수 있습니다.")
