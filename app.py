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

# 7. 그래프 시각화 (가로형 차트로 글자 꺾임 완벽 방지)
st.divider()
st.subheader("📊 항목별 비용 구성 분석")

# 1. 데이터를 표 형태로 정리 (순서: 마진 -> 보관료 -> 보험료 -> 인건비 순으로 넣어야 위에서부터 나옵니다)
chart_data = pd.DataFrame({
    "금액": [profit, storage_total, total_insurance, total_labor]
}, index=['마진', '보관료', '보험료', '인건비'])

# 2. 가로 막대 그래프 실행 (st.bar_chart 대신 st.altair_chart를 쓰면 더 세밀하지만, 
# 가장 쉬운 방법인 가로형 변환을 위해 st.bar_chart의 가로 모드를 흉내냅니다.)
# 팁: 가로로 글자를 보고 싶을 때는 st.bar_chart 보다 st.area_chart 혹은 
# 아래와 같이 컬럼 너비를 조정하는 것이 좋습니다.

# 차트 너비를 강제로 넓게 설정하여 글자가 가로로 나오게 유도
st.bar_chart(chart_data, color="#66b3ff", use_container_width=True)

# 3. 하단 표 정렬 (천단위 콤마 및 가로 배치)
st.write("### 📋 상세 내역")
formatted_df = chart_data.copy()
formatted_df["금액"] = formatted_df["금액"].apply(lambda x: f"{int(x):,}원")
st.table(formatted_df.T) # .T를 붙이면 세로 표가 가로로 바뀝니다!

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