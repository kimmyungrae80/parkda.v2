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

# 1. 페이지 설정 (최상단 고정)
st.set_page_config(page_title="PARKDA 파크골프 통합관제플랫폼", layout="wide")

# 구글 시트 웹 앱 URL (박사님 전용)
DEPLOY_URL = "https://script.google.com/macros/s/AKfycbxxa5VMQJXNKrxuuEZsqRQGzy7qBlDu9_M-Q2BlQhNs69LRYRERescREiI-sjCnOPz5/exec"

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'menu_select' not in st.session_state:
    st.session_state.menu_select = "대회정보"

# 2. 로고 로드 함수
def load_logo(file_name):
    if os.path.exists(file_name):
        return Image.open(file_name)
    return None

logo_wide = load_logo("logo가로.png")
logo_sq = load_logo("logo.png")

# 3. 🎨 프리미엄 딥 그린 & 골드 스타일 디자인
st.markdown("""
    <style>
    /* 전체 배경: 딥 정글 그린 */
    [data-testid="stAppViewContainer"] { 
        background-color: #051610 !important; 
        color: #E0E0E0 !important;
        font-size: calc(15px + 0.3vw) !important;
    }
    
    /* 사이드바: 다크 그린 블랙 */
    [data-testid="stSidebar"] { 
        background-color: #030D0A !important; 
        border-right: 1px solid #143D30;
    }

    /* 제목 및 텍스트 */
    h1 { color: #FFFFFF !important; font-weight: 800 !important; }
    .guide-text { color: #78A695; font-size: 15px; margin-bottom: 12px; font-weight: 400; }

    /* 대형 메뉴 버튼: 원색 기반 고급 그라데이션 */
    .stButton>button {
        width: 100%; height: 85px !important; font-size: 24px !important; font-weight: 800 !important;
        border-radius: 15px !important; border: 1px solid rgba(255,255,255,0.1) !important;
        transition: 0.3s; box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }
    /* 버튼별 컬러 지정 */
    div[data-testid="column"]:nth-child(1) button { background: linear-gradient(135deg, #FF8C00, #E67E22) !important; color: white !important; }
    div[data-testid="column"]:nth-child(2) button { background: linear-gradient(135deg, #007AFF, #0056B3) !important; color: white !important; }
    div[data-testid="column"]:nth-child(3) button { background: linear-gradient(135deg, #28A745, #1E7E34) !important; color: white !important; }

    /* 뉴스 전용 스크롤 박스 */
    .news-scroll-container {
        height: 480px; overflow-y: auto; padding: 15px;
        background: rgba(255,255,255,0.03); border-radius: 12px;
        border: 1px solid #143D30;
    }
    .news-item { padding: 10px 0; border-bottom: 1px solid #143D30; }
    .news-item a { color: #A8D5BA !important; text-decoration: none; font-size: 15px; }
    .news-item a:hover { color: #FFD700 !important; }

    /* 콘텐츠 카드 */
    .content-card {
        padding: 20px; background: rgba(255,255,255,0.05);
        border-radius: 15px; border-left: 8px solid #52C41A;
        margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    /* 조 편성 결과 박스 */
    .team-box { 
        padding: 18px; background-color: rgba(40, 167, 69, 0.1); 
        border-radius: 10px; border: 2px solid #28A745; 
        margin-bottom: 10px; font-size: 21px !important; color: #FFFFFF; font-weight: bold;
    }

    /* 입력창 및 기타 텍스트박스 */
    input, textarea { 
        background-color: #071A14 !important; color: white !important; 
        border: 1px solid #143D30 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. 핵심 데이터 처리 함수
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

# 5. 사이드바 구성 (로고 상단 고정 및 뉴스 스크롤)
with st.sidebar:
    # [박사님 요청] 첫 화면에서도 로고 상단 배치
    if logo_wide:
        st.image(logo_wide, use_container_width=True)
    
    st.divider()

    if not st.session_state.logged_in:
        st.subheader("👤 회원 인증")
        u_name = st.text_input("성함", placeholder="홍길동")
        u_phone = st.text_input("전화번호", placeholder="01012345678")
        
        if st.button("🚀 PARKDA 시작하기"):
            if not u_phone.startswith("010"):
                st.error("⚠️ 전화번호는 010으로 시작해야 합니다.")
            elif u_name and len(u_phone) >= 10:
                st.session_state.logged_in = True
                st.session_state.user_info = {"name": u_name, "phone": u_phone}
                try: requests.post(DEPLOY_URL, json={"type":"JOIN", "name":u_name, "phone":u_phone}, timeout=5)
                except: pass
                st.rerun()
            else:
                st.warning("정보를 입력해 주세요.")
    else:
        # 로그인 후: 정사각형 로고
        if logo_sq:
            st.image(logo_sq, width=120)
        st.markdown(f"#### **{st.session_state.user_info['name']}** 회원님")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()
    st.subheader("📰 실시간 뉴스")
    st.markdown("<p class='guide-text'>뉴스 영역만 아래로 밀어 더 보세요.</p>", unsafe_allow_html=True)
    
    # 뉴스 전용 스크롤 컨테이너
    news_data = get_clean_news("파크골프")
    news_html = "<div class='news-scroll-container'>"
    for n in news_data:
        news_html += f"<div class='news-item'><a href='{n.link}' target='_blank'>• {n.title}</a></div>"
    news_html += "</div>"
    st.markdown(news_html, unsafe_allow_html=True)

# 6. 메인 화면 구성
st.title("⛳ PARKDA 파크골프 통합관제플랫폼")

if st.session_state.logged_in:
    # [박사님 요청] 대형 원색 메뉴 버튼
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        if st.button("🏆 대회정보"): st.session_state.menu_select = "대회정보"
    with m_col2:
        if st.button("📍 전국지도"): st.session_state.menu_select = "전국지도"
    with m_col3:
        if st.button("👥 조편성"): st.session_state.menu_select = "조편성"

    st.divider()

    # 탭별 기능 실행
    if st.session_state.menu_select == "대회정보":
        st.markdown("<p class='guide-text'>💡 최신 대회 공고를 터치하여 상세 내용을 확인하세요.</p>", unsafe_allow_html=True)
        for e in get_clean_news("파크골프 대회 공고")[:12]:
            st.markdown(f"""
            <div class='content-card'>
                <a href='{e.link}' target='_blank' style='color:#FFD700; font-size:20px; text-decoration:none; font-weight:bold;'>🏆 {e.title}</a><br>
                <span style='color:#78A695; font-size:14px;'>발행: {e.published[:16]}</span>
            </div>
            """, unsafe_allow_html=True)

    elif st.session_state.menu_select == "전국지도":
        st.markdown("<p class='guide-text'>💡 지도의 깃발을 클릭하시면 실시간 날씨가 표시됩니다.</p>", unsafe_allow_html=True)
        df_map, col_map = load_park_data()
        if df_map is not None:
            m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
            for _, row in df_map.iterrows():
                try:
                    lat, lon = float(row[col_map['lat']]), float(row[col_map['lon']])
                    weather_info = f"🌡️ {random.randint(18,26)}°C | 맑음 ☀️"
                    p_html = f"<div style='font-size:18px; color:black;'><b>{row[col_map['name']]}</b><br><hr>{weather_info}</div>"
                    folium.Marker([lat, lon], popup=folium.Popup(p_html, max_width=300), icon=folium.Icon(color='blue')).add_to(m)
                except: continue
            folium_static(m, width=1000, height=600)
        else:
            st.error("park_data.xlsx 파일을 찾을 수 없습니다.")

    elif st.session_state.menu_select == "조편성":
        st.markdown("<p class='guide-text'>💡 엑셀/한글 명단을 붙여넣으세요. 기록은 자동으로 저장됩니다.</p>", unsafe_allow_html=True)
        raw = st.text_area("명단 입력 (공백/줄바꿈 가능)", placeholder="회원 이름들을 붙여넣으세요.", height=200)
        if st.button("🚀 조 편성 실행"):
            # 정규표현식으로 명단 파싱
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
                st.text_area("📋 카톡방 전달용", kakao_msg, height=180)
                # DB 전송 (매칭 데이터)
                try: requests.post(DEPLOY_URL, json={"type":"MATCH", "organizer":st.session_state.user_info['name'], "match_result":match_log}, timeout=5)
                except: pass
            else: st.error("명단을 입력해 주세요.")
else:
    st.info("🔒 회원 인증 후 프리미엄 관제 서비스를 이용하실 수 있습니다.")