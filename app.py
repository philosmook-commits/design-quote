import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 1. 구글 시트 연결 함수 (Secrets 방식 적용)
def connect_google_sheet():
    try:
        # 스트림릿 웹 설정에 저장된 정보를 가져옵니다.
        creds_info = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        return client.open("design견적DB").sheet1
    except Exception as e:
        st.error(f"구글 시트 연결 오류: {e}")
        return None

# 2. 한글 깨짐 방지 설정 (웹 서버 환경 대응)
# 웹 서버에는 한글 폰트가 없으므로 그래프 요소를 영문으로 병기하거나 
# 기본 폰트 설정을 초기화하여 □ 깨짐 현상을 최소화합니다.
plt.rcParams['axes.unicode_minus'] = False 

# 3. 페이지 설정 및 제목
st.set_page_config(page_title="물류 견적 시뮬레이터", layout="wide")
st.title("📊 물류 영업용 AI 견적 자동화 시스템")

# 4. 사이드바 - 입력 데이터
st.sidebar.header("📋 견적 조건 설정")
user_name = st.sidebar.text_input("담당자 성함", "홍길동")
customer_name = st.sidebar.text_input("고객사명", "ABC 유통")
volume = st.sidebar.number_input("월 물동량 (건)", value=1000)
labor_rate = st.sidebar.slider("인건비 요율 (단가/건)", 500, 5000, 1500)
storage_fee = st.sidebar.number_input("보관료 (PL당)", value=15000)
insurance_rate = st.sidebar.number_input("보험료율 (%)", value=0.05) / 100
margin_rate = st.sidebar.slider("목표 마진율 (%)", 5, 50, 15) / 100

# 5. 계산 로직
total_labor = volume * labor_rate
total_insurance = total_labor * insurance_rate
storage_total = storage_fee * 10 
base_cost = total_labor + total_insurance + storage_total
final_quote = base_cost / (1 - margin_rate)
profit = final_quote - base_cost

# 6. 결과 출력
st.subheader(f"🏠 {customer_name} 견적 요약")
c1, c2, c3 = st.columns(3)
c1.metric("총 견적 금액", f"{int(final_quote):,} 원")
c2.metric("총 원가", f"{int(base_cost):,} 원")
c3.metric("예상 수익", f"{int(profit):,} 원")

# 7. 그래프 시각화 (한글 깨짐 방지를 위해 영문/한글 병기)
st.divider()
fig, ax = plt.subplots(figsize=(10, 4))

# 레이블을 영문으로 수정하여 어떤 환경에서도 글자가 보이게 합니다.
labels = ['Labor(인건)', 'Insure(보험)', 'Storage(보관)', 'Margin(마진)']
values = [total_labor, total_insurance, storage_total, profit]

ax.bar(labels, values, color=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
ax.set_title("Cost Structure (비용 구성)")
st.pyplot(fig)

# 8. 저장 버튼 (구글 시트 전송 전용)
if st.button("🚀 견적 확정 및 구글 시트 저장"):
    sheet = connect_google_sheet()
    if sheet:
        new_row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_name,
            customer_name,
            volume,
            int(final_quote),
            int(profit)
        ]
        sheet.append_row(new_row)
        st.success(f"✅ '{customer_name}' 견적 데이터가 구글 시트에 기록되었습니다!")
        st.balloons()