import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import feedparser
import os
import random

# 1. 페이지 설정
st.set_page_config(page_title="PARKDA 2.0 | 대회 정보 관제", layout="wide")

# 2. 커스텀 CSS (대회 리스트 디자인 강조)
st.markdown("""
    <style>
    .contest-card { padding: 15px; background: #1e1e1e; border-radius: 10px; border-left: 5px solid #FFD700; margin-bottom: 10px; }
    .contest-title { font-weight: bold; color: #FFD700; font-size: 16px; margin-bottom: 5px; }
    .contest-date { font-size: 13px; color: #bbb; }
    .news-container { max-height: 400px; overflow-y: auto; padding-right: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 지능형 데이터 로드 (구장 정보)
@st.cache_data
def load_park_data():
    file_name = "park_data.xlsx"
    if not os.path.exists(file_name): return None, None
    try:
        df = pd.read_excel(file_name, engine='openpyxl')
        cols = df.columns.tolist()
        mapping = {
            'name': next((c for c in cols if any(x in str(c) for x in ['구장', '이름', '명칭'])), None),
            'addr': next((c for c in cols if any(x in str(c) for x in ['주소', '위치'])), None),
            'lat': next((c for c in cols if any(x in str(c).lower() for x in ['위도', 'lat'])), None),
            'lon': next((c for c in cols if any(x in str(c).lower() for x in ['경도', 'lng', 'lon'])), None),
            'hole': next((c for c in cols if any(x in str(c) for x in ['홀', 'hole'])), None)
        }
        return df, mapping
    except: return None, None

df, col_map = load_park_data()

# --- 사이드바: 실시간 뉴스 및 조 편성 ---
with st.sidebar:
    st.title("📰 파크골프 주요 뉴스")
    news_rss = feedparser.parse("https://news.google.com/rss/search?q=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84&hl=ko&gl=KR&ceid=KR:ko")
    st.markdown('<div class="news-container">', unsafe_allow_html=True)
    if news_rss.entries:
        for entry in news_rss.entries[:8]:
            st.markdown(f"• [{entry.title}]({entry.link})")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    st.title("👥 4인 기준 조 편성")
    raw_names = st.text_area("이름을 입력하세요 (공백 구분)", "박사님 동호인1 동호인2 동호인3", height=120)
    if st.button("🚀 랜덤 조 편성"):
        names = [n.strip() for n in raw_names.replace(',', ' ').split() if n.strip()]
        if names:
            random.shuffle(names)
            for i in range(0, len(names), 4):
                st.info(f"⛳ {i//4 + 1}조: {', '.join(names[i:i+4])}")

# --- 메인 화면: 통합 관제 대시보드 ---
st.title("⛳ PARKDA 2.0: 전국 대회 & 구장 통합 관제")

tab1, tab2 = st.tabs(["🏆 실시간 대회 정보", "📍 전국 구장 위치"])

with tab1:
    st.subheader("🏁 전국 파크골프 대회 자동 서치 (최신)")
    # 대회 정보 전용 검색 (구글 뉴스/검색 결과를 활용한 대회 공고 트래킹)
    contest_rss = feedparser.parse("https://news.google.com/rss/search?q=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84+%EB%8C%80%ED%9A%8C+%EA%B3%B5%EA%B3%A0&hl=ko&gl=KR&ceid=KR:ko")
    
    if contest_rss.entries:
        for entry in contest_rss.entries[:10]: # 최신 대회 관련 이슈 10개
            # 대회 제목에서 장소나 주최 측 유추 가능
            st.markdown(f"""
            <div class="contest-card">
                <div class="contest-title">🏆 <a href="{entry.link}" target="_blank" style="color:#FFD700; text-decoration:none;">{entry.title}</a></div>
                <div class="contest-date">업데이트: {entry.published[:16]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("현재 등록된 새로운 대회 공고가 없습니다.")

with tab2:
    st.subheader("📍 전국 구장 운영 맵")
    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
    if df is not None and col_map['lat']:
        for _, row in df.iterrows():
            try:
                lat, lon = float(row[col_map['lat']]), float(row[col_map['lon']])
                popup_html = f"<b>{row[col_map['name']]}</b><br>{row[col_map['addr']]}<br>{row[col_map['hole']]}홀"
                folium.Marker([lat, lon], popup=folium.Popup(popup_html, max_width=250), tooltip=row[col_map['name']]).add_to(m)
            except: continue
        folium_static(m, width=900, height=550)
    
    if df is not None:
        st.metric("총 등록 구장", f"{len(df)}개")