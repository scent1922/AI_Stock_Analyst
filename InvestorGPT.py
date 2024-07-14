import streamlit as st
import json
import os
import requests
import openai
from typing import Type
from langchain.agents import initialize_agent, Tool
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory



# Streamlit 앱 설정
st.title("주식 분석 및 추천 시스템")

# 사용자 입력
stock_symbol = st.text_input("주식 종목 심볼을 입력하세요 (예: TSLA)")
alpha_vantage_api_key = st.text_input("Alpha Vantage API 키를 입력하세요", type="password")
openai_api_key = st.text_input("OpenAI API 키를 입력하세요", type="password")

# OpenAI API 키 설정
if openai_api_key:
    openai.api_key = openai_api_key
else:
    st.warning("OpenAI API 키를 입력해주세요.")
    st.stop()

# Alpha Vantage API 키 확인
if not alpha_vantage_api_key:
    st.warning("Alpha Vantage API 키를 입력해주세요.")
    st.stop()

# API 요청 함수
def get_company_overview(symbol):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={alpha_vantage_api_key}"
    response = requests.get(url)
    return str(response.json())

def get_income_statement(symbol):
    url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={alpha_vantage_api_key}"
    response = requests.get(url)
    data = response.json()

    if 'quarterlyReports' in data:
        data['quarterlyReports'] = data['quarterlyReports'][:20]
    
    return json.dumps(data, indent=2)

def get_stock_performance(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol={symbol}&apikey={alpha_vantage_api_key}"
    response = requests.get(url)
    data = response.json()

    if 'Weekly Time Series' in data:
        weekly_data = data['Weekly Time Series']
        limited_data = dict(list(weekly_data.items())[:150])
        data['Weekly Time Series'] = limited_data
    
    return json.dumps(data, indent=2)

# Langchain 설정
try:
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7, openai_api_key=openai_api_key)
except Exception as e:
    st.error(f"OpenAI API 키 설정 중 오류가 발생했습니다: {str(e)}")
    st.stop()
    
# Tool 정의
tools = [
    Tool(
        name="Company Overview",
        func=lambda x: get_company_overview(stock_symbol),
        description="회사의 개요 정보를 얻습니다."
    ),
    Tool(
        name="Income Statement",
        func=lambda x: get_income_statement(stock_symbol),
        description="회사의 손익계산서 정보를 얻습니다."
    ),
    Tool(
        name="Stock Performance",
        func=lambda x: get_stock_performance(stock_symbol),
        description="주식의 성과 정보를 얻습니다."
    )
]

# Agent 초기화
memory = ConversationBufferMemory(memory_key="chat_history")
agent = initialize_agent(tools, llm, agent="conversational-react-description", memory=memory, verbose=True, handle_parsing_errors=True)

# 분석 실행 버튼
if st.button("주식 분석 실행"):
    if not stock_symbol or not alpha_vantage_api_key:
        st.error("주식 종목 심볼과 API 키를 모두 입력해주세요.")
    else:
        with st.spinner("데이터를 수집하고 분석 중입니다..."):
            # Agent를 사용한 분석
            result = agent.run(
                f"""
                You are a hedge fund manager.
                Evaluate the company {stock_symbol} and provide your opinion and reasons why the stock is a buy or not in Korean.
                Consider the performance of the stock, the company overview and the income statement.
                Be assertive in your judgement and recommend the stock or advise the user against it.
                Use the provided tools to gather necessary information. Please write down the very detail of your reasons in Korean.
                """
            )

        st.subheader("분석 결과")
        st.write(result)
    


# 주의사항
st.sidebar.warning("주의: 이 분석은 참고용이며, 실제 투자 결정은 전문가와 상담하세요.")