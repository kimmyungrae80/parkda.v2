import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import feedparser
import os

# 페이지 설정
st.set_page_config(page_title="PARKDA 2.0", layout="wide")

# 스타일 설정
st.markdown("""
    <style>
    .news-container { max-height: 400px; overflow-y: auto; padding-right: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 1. 데이터 로드 (에러 방지 로직 추가)
@st.cache_data
def load_data():
    file_name = "경기장_정보.xlsx"
    if os.path.exists(file_name):
        return pd.read_excel(file_name)
    else:
        return None

df = pd.read_excel("park_data.xlsx")

# --- 사이드바: 실시간 뉴스 ---
st.sidebar.title("📰 실시간 파크골프 뉴스")
feed_url = "https://news.google.com/rss/search?q=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84&hl=ko&gl=KR&ceid=KR:ko"
rss_feed = feedparser.parse(feed_url)

if rss_feed.entries:
    st.sidebar.markdown('<div class="news-container">', unsafe_allow_html=True)
    for entry in rss_feed.entries[:10]:
        st.sidebar.markdown(f"**[{entry.title}]({entry.link})**")
        st.sidebar.write(f"📅 {entry.published[:16]}")
        st.sidebar.markdown("---")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.title("👥 스마트 조 편성")
player_names = st.sidebar.text_area("명단 입력", "홍길동, 김철수, 이영희, 박지성")

# --- 메인 화면 ---
st.title("⛳ PARKDA 2.0: 지능형 통합 관제 플랫폼")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📍 전국 구장 실시간 맵")
    
    if df is not None:
        m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
        for _, row in df.iterrows():
            popup_html = f"<b>{row['구장명']}</b><br>{row['주소']}<br>{row['홀수']}홀"
            folium.Marker(
                location=[row['위도'], row['경도']],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=row['구장명']
            ).add_to(m)
        folium_static(m, width=800, height=500)
    else:
        st.error("⚠️ '경기장_정보.xlsx' 파일을 찾을 수 없습니다. GitHub 창고에 파일이 있는지 확인해 주세요.")
        st.info("💡 팁: 파일명이 정확히 '경기장_정보.xlsx'인지(공백 주의) 확인해 보세요.")

with col2:
    st.subheader("📊 데이터 통계")
    if df is not None:
        st.metric("총 등록 구장", f"{len(df)}개")
    else:
        st.metric("총 등록 구장", "데이터 없음")
    st.metric("운영 상태", "정상 (Open-Loop)")