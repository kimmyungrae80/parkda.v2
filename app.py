import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import feedparser
import os
import random
import requests
from PIL import Image
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="PARKDA | 파크골프 통합플랫폼", layout="wide")

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# 2. 로고 로드 (경로 및 오류 해결)
def load_logo():
    # 파일명이 소문자 'logo.png'인지 꼭 확인하세요!
    logo_path = "logo.png" 
    if os.path.exists(logo_path):
        return Image.open(logo_path)
    return None

logo_img = load_logo()

# 3. 날씨 함수 (기존 보존)
def get_weather(lat, lon):
    try:
        temp = random.randint(18, 26)
        status = random.choice(["맑음 ☀️", "구름 조금 ⛅", "흐림 ☁️"])
        return f"🌡️ {temp}°C | {status}"
    except: return "날씨 정보 로딩 실패"

# 4. 데이터 로드 (기존 보존)
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

# 5. 뉴스 및 대회 정보 통합 (중복 제거 & 네이버/구글 검색 최적화)
def get_clean_news(query):
    # 구글 뉴스 RSS는 네이버 뉴스 출처까지 포함합니다. 
    # 검색어에 '네이버뉴스'를 추가하여 데이터 범위를 넓힙니다.
    rss_url = f"https://news.google.com/rss/search?q={query}+네이버뉴스&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    
    seen_titles = set()
    unique_entries = []
    
    for entry in feed.entries:
        # 1. 제목 앞 12자리가 같으면 중복으로 간주 (보람그룹배... 중복 해결)
        title_key = entry.title[:12].replace(" ", "")
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_entries.append(entry)
            
    # 2. 발행 날짜순 정렬 (최신순)
    unique_entries.sort(key=lambda x: getattr(x, 'published_parsed', 0), reverse=True)
    return unique_entries[:10]

# 6. 스타일 설정
st.markdown("""
    <style>
    .stImage > img { border-radius: 10px; margin-bottom: 20px; }
    .contest-card { padding: 15px; background: #1e1e1e; border-radius: 10px; border-left: 5px solid #FFD700; margin-bottom: 10px; }
    .team-box { padding: 10px; background-color: #262730; border-radius: 8px; border-left: 5px solid #2E7D32; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 7. 사이드바 (로고 출력 보강)
with st.sidebar:
    if logo_img:
        st.image(logo_img, use_container_width=True)
    else:
        st.error("⚠️ logo.png 파일이 없습니다.")
    
    st.divider()
    if not st.session_state.logged_in:
        st.subheader("👤 멤버십 인증")
        u_name = st.text_input("성함", placeholder="홍길동")
        u_phone = st.text_input("휴대폰 번호", placeholder="01012345678")
        if st.button("🚀 인증 및 시작"):
            if u_name and len(u_phone) >= 10:
                st.session_state.logged_in = True
                st.session_state.user_info = {"name": u_name, "phone": u_phone, "points": 1000}
                st.rerun()
    else:
        st.success(f"✅ {st.session_state.user_info['name']}님")
        st.metric("💰 포인트", f"{st.session_state.user_info['points']} P")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()
    st.subheader("📰 실시간 뉴스")
    news = get_clean_news("파크골프")
    for n in news[:5]:
        st.markdown(f"• <a href='{n.link}' target='_blank' style='font-size:13px;'>{n.title}</a>", unsafe_allow_html=True)

# 8. 메인 화면
st.title("⛳ PARKDA 2.0 통합 관제 시스템")

if st.session_state.logged_in:
    tab1, tab2, tab3 = st.tabs(["🏆 실시간 대회 정보", "📍 전국 구장 & 날씨", "👥 지능형 조 편성"])
    
    with tab1:
        st.subheader("🏁 전국 대회 공고 (중복 제거 & 최신순)")
        contests = get_clean_news("파크골프 대회 공고")
        for entry in contests:
            st.markdown(f"""
            <div class="contest-card">
                <div style="font-weight:bold; color:#FFD700;"><a href="{entry.link}" target="_blank" style="color:#FFD700; text-decoration:none;">🏆 {entry.title}</a></div>
                <div style="font-size:12px; color:#bbb;">발행일: {entry.published[:16]}</div>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.subheader("📍 전국 구장 실시간 날씨 관제")
        m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
        if df is not None and col_map['lat']:
            for _, row in df.iterrows():
                try:
                    lat, lon = float(row[col_map['lat']]), float(row[col_map['lon']])
                    w = get_weather(lat, lon)
                    p_html = f"<b>{row[col_map['name']]}</b><br>{row[col_map['addr']]}<br><b>날씨:</b> {w}"
                    folium.Marker([lat, lon], popup=folium.Popup(p_html, max_width=250)).add_to(m)
                except: continue
            folium_static(m, width=900, height=550)

    with tab3:
        st.subheader("👥 지능형 랜덤 조 편성")
        raw = st.text_area("명단 입력", "회원1 회원2 회원3 회원4", height=150)
        if st.button("🚀 조 편성 실행"):
            names = [n.strip() for n in raw.replace(',', ' ').split() if n.strip()]
            random.shuffle(names)
            for i in range(0, len(names), 4):
                st.markdown(f'<div class="team-box">{i//4 + 1}조: {", ".join(names[i:i+4])}</div>', unsafe_allow_html=True)
else:
    st.warning("🔒 사이드바에서 실명 인증 후 전체 기능을 이용하세요.")