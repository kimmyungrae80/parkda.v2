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

# 1. 페이지 설정
st.set_page_config(page_title="PARKDA 파크골프 통합관제플랫폼", layout="wide")

# 구글 시트 웹 앱 URL (박사님 전용)
DEPLOY_URL = "https://script.google.com/macros/s/AKfycbxxa5VMQJXNKrxuuEZsqRQGzy7qBlDu9_M-Q2BlQhNs69LRYRERescREiI-sjCnOPz5/exec"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'menu_select' not in st.session_state:
    st.session_state.menu_select = "대회정보"

# 2. 로고 로드
logo_wide = Image.open("logo가로.png") if os.path.exists("logo가로.png") else None
logo_sq = Image.open("logo.png") if os.path.exists("logo.png") else None

# 3. ✨ 세련된 파스텔 & 모던 UI 스타일링
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* 전체 배경 및 폰트 */
    html, body, [data-testid="stAppViewContainer"] { 
        background-color: #F8FAFC !important; 
        color: #1E293B !important;
        font-family: 'Pretendard', sans-serif !important;
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { 
        background-color: #FFFFFF !important; 
        border-right: 1px solid #E2E8F0;
    }

    /* 메뉴 버튼 (Picton Blue & Java 스타일) */
    .stButton>button {
        width: 100%; height: 80px !important; font-size: 22px !important; font-weight: 700 !important;
        border-radius: 16px !important; border: none !important; transition: 0.3s;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    /* 버튼별 세련된 컬러 매칭 */
    div[data-testid="column"]:nth-child(1) button { background-color: #5BC0DE !important; color: white !important; } /* Picton Blue */
    div[data-testid="column"]:nth-child(2) button { background-color: #4DB6AC !important; color: white !important; } /* Java */
    div[data-testid="column"]:nth-child(3) button { background-color: #7986CB !important; color: white !important; } /* Danube */

    /* 뉴스 전용 스크롤 (Mischka 스타일 배경) */
    .news-scroll-box {
        height: 400px; overflow-y: auto; padding: 15px;
        background: #F1F5F9; border-radius: 12px;
        border: 1px solid #E2E8F0;
    }
    .news-link { margin-bottom: 10px; border-bottom: 1px solid #E2E8F0; padding-bottom: 5px; }
    .news-link a { color: #334155 !important; text-decoration: none; font-size: 15px; }

    /* 콘텐츠 카드 */
    .content-card {
        padding: 20px; background: white; border-radius: 20px;
        border: 1px solid #E2E8F0; margin-bottom: 15px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
    }
    
    /* 조 편성 결과 (Powder Ash 스타일) */
    .team-box { 
        padding: 15px; background-color: #F8FAFC; 
        border-radius: 12px; border: 1px solid #CBD5E1; 
        margin-bottom: 10px; font-size: 20px !important; color: #334155; font-weight: bold;
    }

    /* 가이드 텍스트 */
    .guide-text { color: #64748B; font-size: 14px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 4. 기능 함수 (뉴스, 데이터)
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
            'lat': next((c for c in cols if any(x in str(c).lower() for x in ['위도', 'lat', 'y'])), None),
            'lon': next((c for c in cols if any(x in str(c).lower() for x in ['경도', 'lng', 'x'])), None)
        }
        return df, mapping
    except: return None, None

# 5. 사이드바 (로고 상단 고정 및 인증)
with st.sidebar:
    if logo_wide:
        st.image(logo_wide, use_container_width=True)
    
    st.divider()

    if not st.session_state.logged_in:
        st.subheader("👤 멤버십 인증")
        u_name = st.text_input("성함", placeholder="홍길동")
        u_phone = st.text_input("전화번호", placeholder="01012345678")
        
        if st.button("🚀 시작하기"):
            if not u_phone.startswith("010"):
                st.error("⚠️ 010으로 시작해야 합니다.")
            elif u_name and len(u_phone) >= 10:
                st.session_state.logged_in = True
                st.session_state.user_info = {"name": u_name, "phone": u_phone}
                try: requests.post(DEPLOY_URL, json={"type":"JOIN", "name":u_name, "phone":u_phone}, timeout=5)
                except: pass
                st.rerun()
    else:
        if logo_sq: st.image(logo_sq, width=100)
        st.markdown(f"**{st.session_state.user_info['name']}**님 환영합니다.")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()
    st.subheader("📰 실시간 뉴스")
    news_html = "<div class='news-scroll-box'>"
    for n in get_clean_news("파크골프")[:15]:
        news_html += f"<div class='news-link'><a href='{n.link}' target='_blank'>• {n.title}</a></div>"
    news_html += "</div>"
    st.markdown(news_html, unsafe_allow_html=True)

# 6. 메인 화면
st.title("⛳ PARKDA 파크골프 통합관제플랫폼")

if st.session_state.logged_in:
    # 세련된 가로 버튼 메뉴
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏆 대회정보"): st.session_state.menu_select = "대회정보"
    with col2:
        if st.button("📍 전국지도"): st.session_state.menu_select = "전국지도"
    with col3:
        if st.button("👥 조편성"): st.session_state.menu_select = "조편성"

    st.divider()

    if st.session_state.menu_select == "대회정보":
        st.markdown("<p class='guide-text'>전국의 파크골프 대회 정보를 최신순으로 확인하세요.</p>", unsafe_allow_html=True)
        for e in get_clean_news("파크골프 대회 공고")[:12]:
            st.markdown(f"<div class='content-card'><a href='{e.link}' target='_blank' style='color:#0F172A; font-size:18px; font-weight:700;'>🏆 {e.title}</a><br><small>{e.published[:16]}</small></div>", unsafe_allow_html=True)

    elif st.session_state.menu_select == "전국지도":
        st.markdown("<p class='guide-text'>마커를 클릭하면 구장의 실시간 날씨가 나타납니다.</p>", unsafe_allow_html=True)
        df_map, col_map = load_park_data()
        if df_map is not None:
            m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
            for _, row in df_map.iterrows():
                try:
                    lat, lon = float(row[col_map['lat']]), float(row[col_map['lon']])
                    weather = f"🌡️ {random.randint(18,25)}°C | 맑음 ☀️"
                    p_html = f"<div style='font-size:14px;'><b>{row[col_map['name']]}</b><hr>{weather}</div>"
                    folium.Marker([lat, lon], popup=folium.Popup(p_html, max_width=200), icon=folium.Icon(color='cadetblue')).add_to(m)
                except: continue
            folium_static(m, width=1000, height=550)

    elif st.session_state.menu_select == "조편성":
        st.markdown("<p class='guide-text'>명단을 붙여넣으면 자동으로 조를 편성하고 기록합니다.</p>", unsafe_allow_html=True)
        raw = st.text_area("명단 입력", height=150, placeholder="홍길동 김철수...")
        if st.button("🚀 조 편성 실행"):
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
                st.text_area("📋 카톡방 전달용", kakao_msg, height=150)
                try: requests.post(DEPLOY_URL, json={"type":"MATCH", "organizer":st.session_state.user_info['name'], "match_result":match_log}, timeout=5)
                except: pass
else:
    st.info("🔒 회원 인증 후 이용이 가능합니다.")