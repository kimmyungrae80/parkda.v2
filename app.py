import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import feedparser
import random

# 1. 페이지 설정
st.set_page_config(page_title="PARKDA 2.0 Admin", layout="wide")
st.title("⛳ PARKDA 2.0: 지능형 통합 관제 플랫폼")

# 2. 데이터 자동 로드 함수
@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('~')]
    if not files: return None
    target = files[0]
    df = pd.read_excel(target, engine='openpyxl') if target.endswith('.xlsx') else pd.read_csv(target)
    
    # GPS 좌표가 문자열 '35.xxx / 128.xxx' 형태라면 분리
    if 'gps' in df.columns:
        df = df.dropna(subset=['gps'])
        df[['lat', 'lon']] = df['gps'].str.split('/', expand=True).astype(float)
    return df

# 3. 뉴스 수집 함수
def get_news():
    feed = feedparser.parse("https://news.google.com/rss/search?q=파크골프&hl=ko&gl=KR&ceid=KR:ko")
    return feed.entries[:5]

# --- 화면 구성 ---
df = load_data()

# [사이드바] 뉴스 및 조 편성
with st.sidebar:
    st.header("📰 실시간 파크골프 뉴스")
    news = get_news()
    for n in news:
        st.markdown(f"**[{n.title}]({n.link})**")
        st.divider()
    
    st.header("👥 스마트 조 편성")
    names = st.text_area("명단 입력", "홍길동, 김철수, 이영희, 박지성")
    if st.button("편성 실행"):
        n_list = [n.strip() for n in names.split(',') if n.strip()]
        random.shuffle(n_list)
        st.success(f"결과: {n_list}")

# [메인 화면] 지도와 데이터 요약
if df is not None:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📍 전국 구장 실시간 맵")
        # GPS 정보가 있다면 지도 표시, 없다면 안내 메시지
        if 'lat' in df.columns:
            m = folium.Map(location=[36.5, 127.5], zoom_start=7)
            for _, row in df.iterrows():
                folium.Marker([row['lat'], row['lon']], popup=row['name'], tooltip=row['name']).add_to(m)
            st_folium(m, width="100%", height=500)
        else:
            st.warning("데이터에 'gps' 컬럼이 없어서 지도를 표시할 수 없습니다. 대신 표를 보여드릴게요.")
            st.dataframe(df)

    with col2:
        st.subheader("📊 데이터 통계")
        st.metric("총 등록 구장", f"{len(df)}개")
        st.metric("운영 상태", "정상 (Open-Loop)")
        st.info("💡 오른쪽 마커를 클릭하면 구장 정보를 확인할 수 있습니다.")