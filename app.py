import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread
import altair as alt
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from fpdf import FPDF

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

# 2. PDF 생성 함수 (Bytes 변환 오류 수정 버전)
def generate_pdf(user_name, customer_name, final_quote, profit, total_labor, total_insurance, storage_total):
    pdf = FPDF()
    pdf.add_page()
    
    # 한글 폰트 등록 (GitHub에 올린 font.ttf 파일 사용)
    try:
        pdf.add_font('Hangul', '', 'font.ttf')
        pdf.set_font('Hangul', size=18)
    except:
        # 폰트 파일이 없을 경우 기본 폰트 사용
        pdf.set_font('Arial', size=18)

    # 견적서 내용 작성
    pdf.cell(200, 15, txt="물류 서비스 견적서", ln=1, align='C')
    pdf.ln(10)
    
    try: pdf.set_font('Hangul', size=12)
    except: pdf.set_font('Arial', size=12)
    
    pdf.cell(200, 10, txt=f"발행 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1)
    pdf.cell(200, 10, txt=f"담당자: {user_name}", ln=1)
    pdf.cell(200, 10, txt=f"고객사: {customer_name}", ln=1)
    pdf.ln(5)
    
    pdf.cell(200, 10, txt="-"*50, ln=1)
    pdf.cell(100, 10, txt=f"1. 인건비 합계: {int(total_labor):,} 원", ln=1)
    pdf.cell(100, 10, txt=f"2. 보험료 합계: {int(total_insurance):,} 원", ln=1)
    pdf.cell(100, 10, txt=f"3. 보관료 합계: {int(storage_total):,} 원", ln=1)
    pdf.cell(200, 10, txt="-"*50, ln=1)
    
    pdf.set_font(size=14)
    pdf.cell(200, 15, txt=f"최종 견적 총액: {int(final_quote):,} 원", ln=1)
    pdf.set_font(size=10)
    pdf.cell(200, 10, txt=f"(예상 수익: {int(profit):,} 원 포함)", ln=1)
    
    # 핵심 수정: output() 결과를 bytes 타입으로 명확히 변환하여 반환
    return bytes(pdf.output())

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

# 7. 그래프 시각화 (글자 가로 방향 강제 고정)
st.divider()
st.subheader("📊 항목별 비용 구성 분석")

chart_data = pd.DataFrame({
    "항목": ['인건비', '보험료', '보관료', '마진'],
    "금액": [total_labor, total_insurance, storage_total, profit]
})

chart = alt.Chart(chart_data).mark_bar(color="#66b3ff").encode(
    x=alt.X('항목:N', sort=None, axis=alt.Axis(labelAngle=0)),
    y=alt.Y('금액:Q'),
    tooltip=['항목', '금액']
).properties(width='container', height=400)

st.altair_chart(chart, use_container_width=True)

# 8. 하단 상세 내역 표
st.write("### 📋 상세 내역")
formatted_data = pd.DataFrame(
    [[f"{int(total_labor):,}원", f"{int(total_insurance):,}원", f"{int(storage_total):,}원", f"{int(profit):,}원"]],
    columns=['인건비', '보험료', '보관료', '마진'],
    index=['금액']
)
st.table(formatted_data)

# 9. 저장 및 PDF 다운로드 기능
st.divider()
col_save, col_pdf = st.columns(2)

with col_save:
    if st.button("🚀 견적 확정 및 구글 시트 저장"):
        sheet = connect_google_sheet()
        if sheet:
            new_row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                user_name, customer_name, volume, int(final_quote), int(profit)
            ]
            sheet.append_row(new_row)
            st.success("✅ 구글 시트에 기록되었습니다!")
            st.balloons()

with col_pdf:
    try:
        # PDF 데이터 생성 호출
        pdf_bytes = generate_pdf(user_name, customer_name, final_quote, profit, total_labor, total_insurance, storage_total)
        
        st.download_button(
            label="📥 PDF 견적서 다운로드",
            data=pdf_bytes,
            file_name=f"견적서_{customer_name}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"PDF 생성 중 오류 발생: {e}")