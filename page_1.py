
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


# 3. Streamlit 화면 구성
st.title("💱 Exchange Mate")
st.caption("AI와 대화하며 간편하게 환율을 확인하세요.")
st.divider()

# 안내 영역
with st.container(border=True):
    st.subheader("💬 무엇을 도와드릴까요?")
    st.write("궁금한 환율이나 환전할 금액을 자유롭게 질문해 보세요.")
    st.info("💡 예시: 100달러는 원화로 얼마야? / 1유로는 엔화로 얼마야?")


# 4. 채팅 기록 저장
if "messages" not in st.session_state:
    st.session_state.messages = []


# 5. 대화 초기화 버튼
col1, col2 = st.columns([4, 1])

with col2:
    if st.button("🗑️ 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# 6. 사용자 질문 입력
prompt = st.chat_input("환율이나 환전할 금액을 질문해 보세요.")

if prompt:
    with st.spinner("💱 최신 환율을 확인하고 있어요..."):
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


# 7. 채팅 내역 출력
for message in st.session_state.messages:

    if message["role"] == "user":
        avatar = "👤"
    else:
        avatar = "💱"

    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


# 8. 하단 안내 문구
st.divider()
st.caption("📊 환율 데이터 제공: Frankfurter API | 최신 일별 기준 환율")
