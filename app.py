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
import re

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="PARKDA 파크골프 통합관제플랫폼", layout="wide")

# 구글 시트 웹 앱 URL (박사님 전용 주소)
DEPLOY_URL = "https://script.google.com/macros/s/AKfycbxxa5VMQJXNKrxuuEZsqRQGzy7qBlDu9_M-Q2BlQhNs69LRYRERescREiI-sjCnOPz5/exec"

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'menu_select' not in st.session_state:
    st.session_state.menu_select = "대회정보"

# 2. 로고 로드 (이원화)
logo_wide = Image.open("logo가로.png") if os.path.exists("logo가로.png") else None
logo_sq = Image.open("logo.png") if os.path.exists("logo.png") else None

# 3. 반응형 및 고급 UI 스타일 (정부24 스타일 + 모바일 최적화)
st.markdown("""
    <style>
    /* 폰트 반응형 설정 */
    html, body, [data-testid="stAppViewContainer"] { 
        background-color: #F2F4F7 !important; 
        color: #333 !important;
        font-size: calc(16px + 0.4vw) !important;
        font-family: 'Pretendard', -apple-system, sans-serif !important;
    }
    
    /* 사이드바 가시성 확보 */
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E5E5E5; }

    /* 대형 버튼 메뉴 스타일 (주황, 파랑, 녹색) */
    .stButton>button {
        width: 100%; height: 90px !important; font-size: 24px !important; font-weight: 800 !important;
        border-radius: 16px !important; border: none !important; transition: 0.2s;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    /* 버튼별 색상 강제 지정 */
    div[data-testid="column"]:nth-child(1) button { background-color: #FF8C00 !important; color: white !important; }
    div[data-testid="column"]:nth-child(2) button { background-color: #007AFF !important; color: white !important; }
    div[data-testid="column"]:nth-child(3) button { background-color: #28A745 !important; color: white !important; }

    /* 카드 및 박스 디자인 */
    .contest-card { padding: 25px; background: white; border-radius: 15px; margin-bottom: 15px; border-left: 8px solid #FF8C00; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    .team-box { padding: 18px; background-color: white; border-radius: 12px; border: 2px solid #28A745; margin-bottom: 10px; font-size: 22px !important; color: #1A1A1A; font-weight: bold; }
    
    /* 옅은 가이드 글씨 */
    .guide-text { color: #8E8E93; font-size: 16px; font-weight: 400; margin-bottom: 10px; }
    
    /* 뉴스 스크롤 영역 */
    .news-scroll { max-height: 450px; overflow-y: scroll; padding: 15px; border-radius: 12px; background: #FFFFFF; border: 1px solid #E5E5EA; }
    
    /* 모바일 미디어 쿼리 */
    @media (max-width: 768px) {
        .stButton>button { height: 75px !important; font-size: 20px !important; }
        .team-box { font-size: 18px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 4. 유틸리티 함수
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
        seen, unique = set(), []
        for e in feed.entries:
            key = e.title[:12].replace(" ", "")
            if key not in seen:
                seen.add(key)
                unique.append(e)
        unique.sort(key=lambda x: getattr(x, 'published_parsed', 0), reverse=True)
        return unique
    except: return []

# 5. 사이드바 (로그인 및 뉴스)
with st.sidebar:
    if not st.session_state.logged_in:
        if logo_wide: st.image(logo_wide, use_container_width=True)
        u_name = st.text_input("성함", placeholder="홍길동")
        u_phone = st.text_input("전화번호", placeholder="01012347890")
        if st.button("🚀 PARKDA 시작하기"):
            if not u_phone.startswith("010"):
                st.error("⚠️ 전화번호는 반드시 010으로 시작해야 합니다.")
            elif u_name and len(u_phone) >= 10:
                st.session_state.logged_in = True
                st.session_state.user_info = {"name": u_name, "phone": u_phone}
                try: requests.post(DEPLOY_URL, json={"type":"JOIN", "name":u_name, "phone":u_phone, "points":1000}, timeout=5)
                except: pass
                st.rerun()
            else: st.warning("정보를 정확히 입력해주세요.")
    else:
        if logo_sq: st.image(logo_sq, width=130)
        st.markdown(f"### **{st.session_state.user_info['name']}** 님")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()
    
    st.divider()
    st.subheader("📰 실시간 뉴스")
    st.markdown("<div class='news-scroll'>", unsafe_allow_html=True)
    for n in get_clean_news("파크골프")[:15]:
        st.markdown(f"• <a href='{n.link}' target='_blank' style='color:#333; text-decoration:none; font-size:15px;'>{n.title}</a><hr style='margin:10px 0; border:0.1px solid #eee;'>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# 6. 메인 화면
st.title("⛳ PARKDA 파크골프 통합관제플랫폼")

if st.session_state.logged_in:
    # 대형 메뉴 (반응형 가로 배치)
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        if st.button("🏆 대회정보"): st.session_state.menu_select = "대회정보"
    with m_col2:
        if st.button("📍 전국지도"): st.session_state.menu_select = "전국지도"
    with m_col3:
        if st.button("👥 조편성"): st.session_state.menu_select = "조편성"

    st.divider()

    if st.session_state.menu_select == "대회정보":
        st.markdown("<p class='guide-text'>전국의 파크골프 대회 정보를 최신순으로 보여드립니다.</p>", unsafe_allow_html=True)
        for e in get_clean_news("파크골프 대회 공고")[:12]:
            st.markdown(f"<div class='contest-card'><a href='{e.link}' target='_blank' style='color:#E65100; font-size:22px; text-decoration:none; font-weight:bold;'>🏆 {e.title}</a><br><span style='color:#999; font-size:15px;'>{e.published[:16]}</span></div>", unsafe_allow_html=True)

    elif st.session_state.menu_select == "전국지도":
        st.markdown("<p class='guide-text'>지도의 깃발을 클릭하시면 해당 구장의 날씨를 확인하실 수 있습니다.</p>", unsafe_allow_html=True)
        df_map, col_map = load_park_data()
        if df_map is not None:
            m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
            for _, row in df_map.iterrows():
                try:
                    lat, lon = float(row[col_map['lat']]), float(row[col_map['lon']])
                    w = get_weather(lat, lon)
                    p_html = f"<div style='font-size:18px;'><b>{row[col_map['name']]}</b><br><hr>{w}</div>"
                    folium.Marker([lat, lon], popup=folium.Popup(p_html, max_width=300), icon=folium.Icon(color='blue')).add_to(m)
                except: continue
            folium_static(m, width=1000, height=600)

    elif st.session_state.menu_select == "조편성":
        st.markdown("<p class='guide-text'>엑셀/한글 명단을 그대로 복사해서 붙여넣으세요. AI가 자동으로 이름을 분리합니다.</p>", unsafe_allow_html=True)
        raw = st.text_area("회원 명단 입력", placeholder="예: 홍길동 김철수 이영희 박지성...", height=200)
        if st.button("🚀 지금 바로 조 편성 시작"):
            # 엑셀/한글 특수구분자 완벽 대응 (정규표현식)
            names = re.split(r'[,\s\t\n]+', raw)
            names = [n.strip() for n in names if n.strip()]
            if names:
                random.shuffle(names)
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                kakao_msg = f"⛳ [PARKDA 조 편성 결과]\n📅 일시: {now_str}\n"
                match_log = ""
                for i in range(0, len(names), 4):
                    line = f"{i//4 + 1}조: {', '.join(names[i:i+4])}"
                    st.markdown(f"<div class='team-box'>{line}</div>", unsafe_allow_html=True)
                    kakao_msg += line + "\n"
                    match_log += line + " | "
                st.text_area("📋 카톡방 전달용 (복사해서 사용하세요)", kakao_msg, height=180)
                # DB 전송
                try: requests.post(DEPLOY_URL, json={"type":"MATCH", "organizer":st.session_state.user_info['name'], "match_result":match_log}, timeout=5)
                except: pass
            else: st.error("명단을 입력해주세요.")
else:
    st.info("🔒 회원 인증 후 이용이 가능합니다. 왼쪽 사이드바에서 정보를 입력해주세요.")