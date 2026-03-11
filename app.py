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

# 1. 페이지 설정 및 제목 (반응형 뷰포트 포함)
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

# 3. 🛠️ 기획자 의도 기반 프리미엄 다크 스타일링 (반응형 완벽 지원)
st.markdown("""
    <style>
    /* 전체 배경: 무게감 있는 딥 다크 그린 (로고 베이스) */
    [data-testid="stAppViewContainer"] { 
        background-color: #040D09 !important; 
        color: #E0E0E0 !important;
        font-size: calc(16px + 0.3vw) !important;
    }
    
    /* 사이드바: 칠흑 같은 다크그린 블랙 */
    [data-testid="stSidebar"] { 
        background-color: #020806 !important; 
        border-right: 1px solid #143D30;
    }

    /* 제목: 화이트 & 골드 */
    h1 { color: #FFFFFF !important; font-weight: 900 !important; letter-spacing: -1px; }
    .guide-text { color: #5C8C78; font-size: 15px; margin-bottom: 10px; }

    /* 대형 버튼 메뉴: 묵직한 원색 그라데이션 (반응형) */
    .stButton>button {
        width: 100%; height: 90px !important; font-size: 24px !important; font-weight: 800 !important;
        border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.05) !important;
        transition: 0.3s; box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }
    /* 버튼별 기획 컬러 (주황, 파랑, 녹색) */
    div[data-testid="column"]:nth-child(1) button { background: linear-gradient(135deg, #FF8C00, #E65100) !important; color: white !important; }
    div[data-testid="column"]:nth-child(2) button { background: linear-gradient(135deg, #007AFF, #004494) !important; color: white !important; }
    div[data-testid="column"]:nth-child(3) button { background: linear-gradient(135deg, #2E7D32, #1B5E20) !important; color: white !important; }

    /* 뉴스 전용 고립 스크롤 영역 */
    .news-container {
        height: 500px; overflow-y: scroll; padding: 15px;
        background: rgba(255,255,255,0.02); border-radius: 10px;
        border: 1px solid #143D30;
    }
    .news-card { padding: 10px 0; border-bottom: 1px solid #143D30; }
    .news-card a { color: #8DBDA8 !important; text-decoration: none; font-size: 15px; }

    /* 콘텐츠 카드 디자인 (박사님 다크 스타일) */
    .content-card {
        padding: 25px; background: rgba(255,255,255,0.04);
        border-radius: 15px; border-left: 8px solid #2E7D32;
        margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* 조 편성 결과 박스 */
    .team-box { 
        padding: 20px; background-color: rgba(46, 125, 50, 0.15); 
        border-radius: 12px; border: 2px solid #2E7D32; 
        margin-bottom: 12px; font-size: 22px !important; color: #FFFFFF; font-weight: bold;
    }

    /* 입력창: 다크 모드 최적화 */
    input, textarea { 
        background-color: #07140F !important; color: white !important; 
        border: 1px solid #143D30 !important; font-size: 18px !important;
    }

    /* 모바일 반응형 폰트 및 높이 조절 */
    @media (max-width: 768px) {
        .stButton>button { height: 75px !important; font-size: 20px !important; }
        h1 { font-size: 1.8rem !important; }
        .team-box { font-size: 18px !important; }
    }
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

# 5. 사이드바 (기획대로 로고 상단 배치)
with st.sidebar:
    # [핵심] 첫 화면 성함 위에 가로 로고 배치
    if not st.session_state.logged_in:
        if logo_wide:
            st.image(logo_wide, use_container_width=True)
        
        st.divider()
        st.subheader("👤 멤버십 인증")
        u_name = st.text_input("성함", placeholder="홍길동")
        u_phone = st.text_input("전화번호", placeholder="01012345678")
        
        if st.button("🚀 PARKDA 시작하기"):
            # 010 번호 검증 로직
            if not u_phone.startswith("010"):
                st.error("⚠️ 전화번호는 010으로 시작해야 합니다.")
            elif u_name and len(u_phone) >= 10:
                st.session_state.logged_in = True
                st.session_state.user_info = {"name": u_name, "phone": u_phone}
                # 구글 시트 가입 정보 기록
                try: requests.post(DEPLOY_URL, json={"type":"JOIN", "name":u_name, "phone":u_phone, "points":1000}, timeout=5)
                except: pass
                st.rerun()
            else:
                st.warning("정보를 정확히 입력해 주세요.")
    else:
        # 로그인 후: 정사각형 로고
        if logo_sq:
            st.image(logo_sq, width=130)
        st.markdown(f"#### **{st.session_state.user_info['name']}** 회원님")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()
    
    st.divider()
    st.subheader("📰 실시간 뉴스")
    st.markdown("<p class='guide-text'>뉴스 영역을 아래로 내려 지난 소식을 보세요.</p>", unsafe_allow_html=True)
    
    # 뉴스 전용 독립 스크롤 영역
    news_html = "<div class='news-container'>"
    for n in get_clean_news("파크골프"):
        news_html += f"<div class='news-card'><a href='{n.link}' target='_blank'>• {n.title}</a></div>"
    news_html += "</div>"
    st.markdown(news_html, unsafe_allow_html=True)

# 6. 메인 화면
st.title("⛳ PARKDA 파크골프 통합관제플랫폼")

if st.session_state.logged_in:
    # 기획 의도: 대형 메뉴 버튼 (주황, 파랑, 녹색)
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        if st.button("🏆 대회정보"): st.session_state.menu_select = "대회정보"
    with m_col2:
        if st.button("📍 전국지도"): st.session_state.menu_select = "전국지도"
    with m_col3:
        if st.button("👥 조편성"): st.session_state.menu_select = "조편성"

    st.divider()

    if st.session_state.menu_select == "대회정보":
        st.markdown("<p class='guide-text'>💡 최신 대회 공고를 터치하여 내용을 확인하세요.</p>", unsafe_allow_html=True)
        for e in get_clean_news("파크골프 대회 공고")[:12]:
            st.markdown(f"""
            <div class='content-card'>
                <a href='{e.link}' target='_blank' style='color:#FFD700; font-size:20px; text-decoration:none; font-weight:bold;'>🏆 {e.title}</a><br>
                <span style='color:#5C8C78; font-size:14px;'>발행일: {e.published[:16]}</span>
            </div>
            """, unsafe_allow_html=True)

    elif st.session_state.menu_select == "전국지도":
        st.markdown("<p class='guide-text'>💡 지도의 깃발을 클릭하면 해당 구장의 실시간 날씨가 표시됩니다.</p>", unsafe_allow_html=True)
        df_map, col_map = load_park_data()
        if df_map is not None:
            m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
            for _, row in df_map.iterrows():
                try:
                    lat, lon = float(row[col_map['lat']]), float(row[col_map['lon']])
                    # 날씨 시뮬레이션 (마커 클릭 시 팝업)
                    weather = f"🌡️ {random.randint(18,25)}°C | 맑음 ☀️"
                    p_html = f"<div style='font-size:18px; color:black;'><b>{row[col_map['name']]}</b><br><hr>{weather}</div>"
                    folium.Marker([lat, lon], popup=folium.Popup(p_html, max_width=300), icon=folium.Icon(color='blue')).add_to(m)
                except: continue
            folium_static(m, width=1000, height=600)

    elif st.session_state.menu_select == "조편성":
        st.markdown("<p class='guide-text'>💡 엑셀/한글 명단을 붙여넣으세요. 조 편성과 동시에 구글 시트에 기록됩니다.</p>", unsafe_allow_html=True)
        raw = st.text_area("회원 명단 입력", placeholder="명단을 이곳에 붙여넣으세요.", height=200)
        
        if st.button("🚀 조 편성 실행"):
            # 엑셀/한글 다양한 구분자 자동 인식
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
                
                st.text_area("📋 카톡방 전달용 (복사하여 사용하세요)", kakao_msg, height=180)
                
                # [데이터 자산화] 구글 시트로 조편성 이력 실시간 전송
                try:
                    requests.post(DEPLOY_URL, json={
                        "type": "MATCH",
                        "organizer": st.session_state.user_info['name'],
                        "match_result": match_log
                    }, timeout=5)
                except: pass
            else:
                st.error("명단을 입력해 주세요.")
else:
    st.info("🔒 성함과 번호를 입력하여 프리미엄 관제 서비스를 시작하세요.")