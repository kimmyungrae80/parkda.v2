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

# 1. 데이터 로드 (컬럼명 자동 매칭 로직 추가)
@st.cache_data
def load_data():
    file_name = "park_data.xlsx"
    if os.path.exists(file_name):
        df = pd.read_excel(file_name)
        # 컬럼명 자동 매칭 (사용자가 '구장이름'이라 썼든 '구장명'이라 썼든 찾아냄)
        cols = df.columns
        mapping = {
            'name': [c for c in cols if '구장' in c or '이름' in c or '명칭' in c][0],
            'addr': [c for c in cols if '주소' in c or '위치' in c][0],
            'lat': [c for c in cols if '위도' in c or 'lat' in c.lower()][0],
            'lon': [c for c in cols if '경도' in c or 'lng' in c.lower() or 'lon' in c.lower()][0],
            'hole': [c for c in cols if '홀' in c or 'hole' in c.lower()][0]
        }
        return df, mapping
    return None, None

df, col_map = load_data()

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
            # 매칭된 컬럼명으로 데이터 추출
            name = row[col_map['name']]
            addr = row[col_map['addr']]
            hole = row[col_map['hole']]
            lat = row[col_map['lat']]
            lon = row[col_map['lon']]
            
            popup_html = f"<b>{name}</b><br>{addr}<br>{hole}홀"
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=name
            ).add_to(m)
        folium_static(m, width=800, height=500)
    else:
        st.error("⚠️ 'park_data.xlsx' 파일을 찾을 수 없습니다.")

with col2:
    st.subheader("📊 데이터 통계")
    if df is not None:
        st.metric("총 등록 구장", f"{len(df)}개")
    st.metric("운영 상태", "정상 (Open-Loop)")
    st.info("💡 마커를 클릭하면 구장 상세 정보가 나타납니다.")