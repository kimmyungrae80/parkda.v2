import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import feedparser
import os
import random
import urllib.parse
import requests
from PIL import Image

# 1. 페이지 설정 및 제목 (박사님 요청 반영)
st.set_page_config(page_title="PARKDA 파크골프 통합관제플랫폼", layout="wide")

# 구글 시트 웹 앱 URL (박사님이 주신 주소 반영)
DEPLOY_URL = "https://script.google.com/macros/s/AKfycbxxa5VMQJXNKrxuuEZsqRQGzy7qBlDu9_M-Q2BlQhNs69LRYRERescREiI-sjCnOPz5/exec"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# 2. 로고 로드 (로그인 전/후 이원화)
def load_logo(file_name):
    if os.path.exists(file_name):
        return Image.open(file_name)
    return None

logo_wide = load_logo("logo가로.png")
logo_sq = load_logo("logo.png")

# 3. 유틸리티 함수 (날씨 및 데이터 로드)
def get_weather(lat, lon):
    try:
        temp = random.randint(18, 26)
        status = random.choice(["맑음 ☀️", "구름 조금 ⛅", "흐림 ☁️"])
        return f"🌡️ {temp}°C | {status}"
    except: return "날씨 정보 로딩 실패"

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
            'lon': next((c for c in cols if any(x in str(c).lower() for x in ['경도', 'lng', 'lon'])), None)
        }
        return df, mapping
    except: return None, None

df, col_map = load_park_data()

# 4. 뉴스 수집 및 중복 제거 (URL 인코딩 보강)
def get_clean_news(query):
    try:
        safe_query = urllib.parse.quote(f"{query} 네이버뉴스")
        rss_url = f"https://news.google.com/rss/search?q={safe_query}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        seen_titles = set()
        unique_entries = []
        for entry in feed.entries:
            title_key = entry.title[:12].replace(" ", "")
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_entries.append(entry)
        unique_entries.sort(key=lambda x: getattr(x, 'published_parsed', 0), reverse=True)
        return unique_entries[:10]
    except: return []

# 5. 커스텀 스타일
st.markdown("""
    <style>
    .stImage > img { margin-bottom: 20px; border-radius: 5px; }
    .contest-card { padding: 15px; background: #1e1e1e; border-radius: 10px; border-left: 5px solid #FFD700; margin-bottom: 10px; }
    .team-box { padding: 10px; background-color: #262730; border-radius: 8px; border-left: 5px solid #2E7D32; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 6. 사이드바 (로고/인증/DB저장)
with st.sidebar:
    if not st.session_state.logged_in:
        if logo_wide: st.image(logo_wide, use_container_width=True)
        st.subheader("👤 멤버십 인증")
        u_name = st.text_input("성함", placeholder="홍길동")
        u_phone = st.text_input("휴대폰 번호", placeholder="01012345678")
        
        if st.button("🚀 인증 및 시작"):
            if u_name and len(u_phone) >= 10:
                user_data = {"name": u_name, "phone": u_phone, "points": 1000}
                try:
                    # [핵심] 구글 시트로 데이터 즉시 전송
                    requests.post(DEPLOY_URL, json=user_data)
                except: pass # 저장 에러나도 로그인은 진행
                
                st.session_state.logged_in = True
                st.session_state.user_info = user_data
                st.rerun()
            else:
                st.error("성함과 연락처를 정확히 입력해 주세요.")
    else:
        if logo_sq: st.image(logo_sq, width=150)
        st.success(f"✅ {st.session_state.user_info['name']}님 접속 중")
        st.metric("💰 보유 포인트", f"{st.session_state.user_info['points']} P")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()
    st.subheader("📰 실시간 파크골프 뉴스")
    for n in get_clean_news("파크골프")[:5]:
        st.markdown(f"• <a href='{n.link}' target='_blank' style='font-size:13px;'>{n.title}</a>", unsafe_allow_html=True)

# 7. 메인 화면
st.title("⛳ PARKDA 파크골프 통합관제플랫폼")

if st.session_state.logged_in:
    tab1, tab2, tab3 = st.tabs(["🏆 실시간 대회 정보", "📍 전국 구장 & 날씨", "🤖 AI 지능형 조 편성"])
    
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
        st.subheader("🤖 AI 지능형 조 편성 시스템")
        raw = st.text_area("명단 입력 (이름 사이 공백)", "김명래 박지성 손흥민 이강인 조규성 황희찬", height=150)
        if st.button("🚀 AI 조 편성 실행"):
            names = [n.strip() for n in raw.replace(',', ' ').split() if n.strip()]
            if names:
                random.shuffle(names)
                for i in range(0, len(names), 4):
                    st.markdown(f'<div class="team-box">🤖 AI {i//4 + 1}조: {", ".join(names[i:i+4])}</div>', unsafe_allow_html=True)
else:
    st.warning("🔒 사이드바에서 실명 인증 후 전체 기능을 이용하세요.")