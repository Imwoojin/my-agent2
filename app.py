import streamlit as st
from dotenv import load_dotenv

load_dotenv()

page_1 = st.Page("page_1.py", title="환율 조회 챗봇")

pages = st.navigation([page_1], position="top")

pages.run()