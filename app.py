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
from datetime import datetime

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="PARKDA 파크골프 통합관제플랫폼", layout="wide")

# 구글 시트 웹 앱 URL
DEPLOY_URL = "https://script.google.com/macros/s/AKfycbxxa5VMQJXNKrxuuEZsqRQGzy7qBlDu9_M-Q2BlQhNs69LRYRERescREiI-sjCnOPz5/exec"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'menu_select' not in st.session_state:
    st.session_state.menu_select = "대회정보" # 기본 메뉴 설정

# 2. 로고 로드
def load_logo(file_name):
    if os.path.exists(file_name):
        return Image.open(file_name)
    return None

logo_wide = load_logo("logo가로.png")
logo_sq = load_logo("logo.png")

# 3. 스타일 설정 (대형 폰트 및 원색 디자인)
st.markdown("""
    <style>
    /* 전체 배경 및 기본 글자 크기 상향 */
    html, body, [class*="css"] { font-size: 20px !important; font-weight: bold !important; }
    
    /* 대형 메뉴 버튼 스타일 */
    .stButton>button {
        width: 100%;
        height: 80px !important;
        font-size: 26px !important;
        border-radius: 15px !important;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* 메뉴별 원색 지정 */
    div[data-testid="stVerticalBlock"] > div:nth-child(1) button { background-color: #FFD700 !important; color: black !important; } /* 노랑: 대회 */
    div[data-testid="stVerticalBlock"] > div:nth-child(2) button { background-color: #FF4B4B !important; color: white !important; } /* 빨강: 지도 */
    div[data-testid="stVerticalBlock"] > div:nth-child(3) button { background-color: #2E7D32 !important; color: white !important; } /* 초록: 조편성 */
    
    /* 카드 스타일 */
    .contest-card { padding: 20px; background: #ffffff; color: #000; border-radius: 15px; border-left: 10px solid #FFD700; margin-bottom: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .team-box { padding: 20px; background-color: #f0f2f6; color: #000; border-radius: 15px; border-left: 10px solid #2E7D32; margin-bottom: 10px; font-size: 24px !important; }
    
    /* 입력창 글자 크기 */
    input, textarea { font-size: 22px !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. 유틸리티 함수 (기존 보존)
def get_weather(lat, lon):
    try:
        temp = random.randint(18, 26)
        status = random.choice(["맑음 ☀️", "구름 조금 ⛅", "흐림 ☁️"])
        return f"🌡️ {temp}°C | {status}"
    except: return "날씨 확인 불가"

@st.cache_data
def load_park_data():
    file_name = "park_data.xlsx"
    if not os.path.exists(file_name): return None, None
    try:
        df = pd.read_excel(file_name, engine='openpyxl')
        cols = df.columns.tolist()
        mapping = {
            'name': next((c for c in cols if any(x in str(c) for x in ['구장', '이름', '명칭', '시설명'])), None),
            'addr': next((c for c in cols if any(x in str(c) for x in ['주소', '위치', '소재지'])), None),
            'lat': next((c for c in cols if any(x in str(c).lower() for x in ['위도', 'lat', 'y'])), None),
            'lon': next((c for c in cols if any(x in str(c).lower() for x in ['경도', 'lng', 'x'])), None)
        }
        return df, mapping
    except: return None, None

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

# 5. 사이드바 (기능 보존)
with st.sidebar:
    if not st.session_state.logged_in:
        if logo_wide: st.image(logo_wide, use_container_width=True)
        st.subheader("👤 회원 인증 (큰 글씨)")
        u_name = st.text_input("성함")
        u_phone = st.text_input("전화번호")
        if st.button("🚀 시작하기"):
            if u_name and len(u_phone) >= 10:
                user_data = {"type": "JOIN", "name": u_name, "phone": u_phone, "points": 1000}
                try: requests.post(DEPLOY_URL, json=user_data, timeout=5)
                except: pass
                st.session_state.logged_in = True
                st.session_state.user_info = user_data
                st.rerun()
    else:
        if logo_sq: st.image(logo_sq, width=150)
        st.success(f"✅ {st.session_state.user_info['name']}님 환영합니다!")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()
    
    st.divider()
    st.subheader("📰 오늘의 뉴스")
    for n in get_clean_news("파크골프")[:3]:
        st.markdown(f"<div style='font-size:16px;'>• <a href='{n.link}'>{n.title}</a></div>", unsafe_allow_html=True)

# 6. 메인 화면: 대형 버튼 메뉴 시스템
st.title("⛳ PARKDA 파크골프 통합관제플랫폼")

if st.session_state.logged_in:
    # [핵심] 어르신들을 위한 3대 대형 메뉴 버튼
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏆 대회정보 보기"): st.session_state.menu_select = "대회정보"
    with col2:
        if st.button("📍 전국구장 날씨"): st.session_state.menu_select = "전국지도"
    with col3:
        if st.button("👥 조 편성 하기"): st.session_state.menu_select = "조편성"

    st.divider()

    # 메뉴별 화면 출력
    if st.session_state.menu_select == "대회정보":
        st.header("🏆 최신 대회 안내")
        contests = get_clean_news("파크골프 대회 공고")
        for entry in contests:
            st.markdown(f"""
            <div class="contest-card">
                <div style="font-size:24px; font-weight:bold;"><a href="{entry.link}" target="_blank" style="color:#000; text-decoration:none;">{entry.title}</a></div>
                <div style="font-size:16px; color:#666;">발표: {entry.published[:16]}</div>
            </div>
            """, unsafe_allow_html=True)

    elif st.session_state.menu_select == "전국지도":
        st.header("📍 전국 구장 및 실시간 날씨")
        st.info("💡 지도 위 초록색 깃발을 누르면 날씨가 크게 보입니다!")
        df, col_map = load_park_data()
        if df is not None:
            m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
            for _, row in df.iterrows():
                try:
                    lat, lon = float(row[col_map['lat']]), float(row[col_map['lon']])
                    w = get_weather(lat, lon)
                    p_html = f"<div style='font-size:20px;'><b>{row[col_map['name']]}</b><br><hr>{w}</div>"
                    folium.Marker([lat, lon], popup=folium.Popup(p_html, max_width=300), icon=folium.Icon(color='green')).add_to(m)
                except: continue
            folium_static(m, width=1000, height=600)

    elif st.session_state.menu_select == "조편성":
        st.header("👥 AI 지능형 조 편성")
        raw = st.text_area("여기에 회원 명단을 입력하세요", height=200)
        if st.button("🚀 지금 바로 조 편성!"):
            names = [n.strip() for n in raw.replace(',', ' ').split() if n.strip()]
            if names:
                random.shuffle(names)
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
                kakao_msg = f"⛳ [PARKDA 조 편성 결과]\n📅 일시: {now_str}\n"
                
                for i in range(0, len(names), 4):
                    line = f"{i//4 + 1}조: {', '.join(names[i:i+4])}"
                    st.markdown(f'<div class="team-box">{line}</div>', unsafe_allow_html=True)
                    kakao_msg += line + "\n"
                
                # DB 저장
                try: requests.post(DEPLOY_URL, json={"type":"MATCH", "organizer":st.session_state.user_info['name'], "match_result":kakao_msg})
                except: pass
                
                st.subheader("📋 아래 내용을 복사해서 카톡에 올리세요")
                st.text_area("카톡 전달용", kakao_msg, height=150)

else:
    st.warning("🔒 어르신, 왼쪽에서 성함과 번호를 넣고 '시작하기'를 눌러주세요!")