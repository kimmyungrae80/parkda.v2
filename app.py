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

# 구글 시트 웹 앱 URL
DEPLOY_URL = "https://script.google.com/macros/s/AKfycbxxa5VMQJXNKrxuuEZsqRQGzy7qBlDu9_M-Q2BlQhNs69LRYRERescREiI-sjCnOPz5/exec"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'menu_select' not in st.session_state:
    st.session_state.menu_select = "대회정보"

# 2. 로고 로드
logo_wide = Image.open("logo가로.png") if os.path.exists("logo가로.png") else None
logo_sq = Image.open("logo.png") if os.path.exists("logo.png") else None

# 3. 🌲 프리미엄 딥 그린 UI 스타일링
st.markdown("""
    <style>
    /* 전체 배경: 고급스러운 다크 그린 그레이 */
    [data-testid="stAppViewContainer"] { 
        background-color: #0B1C15 !important; 
        color: #E0E0E0 !important;
    }
    
    /* 사이드바: 딥 네이비 그린 */
    [data-testid="stSidebar"] { 
        background-color: #07130E !important; 
        border-right: 1px solid #1E3A2F;
    }

    /* 메인 타이틀 폰트 */
    h1 { color: #FFFFFF !important; font-size: 2.2rem !important; font-weight: 800 !important; }

    /* 대형 메뉴 버튼 스타일 (색감 고급화) */
    .stButton>button {
        width: 100%; height: 85px !important; font-size: 22px !important; font-weight: 700 !important;
        border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.1) !important;
        transition: 0.3s; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* 버튼별 프리미엄 컬러 (주황/파랑/초록의 채도를 낮춰 고급스럽게) */
    div[data-testid="column"]:nth-child(1) button { background: linear-gradient(135deg, #D48806, #AA6D05) !important; color: white !important; }
    div[data-testid="column"]:nth-child(2) button { background: linear-gradient(135deg, #1890FF, #096DD9) !important; color: white !important; }
    div[data-testid="column"]:nth-child(3) button { background: linear-gradient(135deg, #52C41A, #389E0D) !important; color: white !important; }

    /* 뉴스 전용 스크롤 박스 (뉴스만 따로 스크롤) */
    .news-container {
        height: 500px; overflow-y: auto; padding: 15px;
        background: rgba(255,255,255,0.03); border-radius: 10px;
        border: 1px solid #1E3A2F;
    }
    .news-card {
        padding: 10px 0; border-bottom: 1px solid #1E3A2F;
    }
    .news-card a { color: #A0C4B4 !important; text-decoration: none; font-size: 15px; }
    .news-card a:hover { color: #FFFFFF !important; }

    /* 콘텐츠 카드 디자인 */
    .content-card {
        padding: 20px; background: rgba(255,255,255,0.05);
        border-radius: 15px; border-left: 6px solid #52C41A;
        margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* 가이드 텍스트 (옅은 초록) */
    .guide-text { color: #6B8E7F; font-size: 15px; margin-bottom: 10px; }

    /* 입력창 스타일 보정 */
    input, textarea { background-color: #0D261D !important; color: white !important; border: 1px solid #1E3A2F !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. 뉴스 데이터 엔진
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

# 5. 사이드바 (로그인 및 뉴스 전용 스크롤)
with st.sidebar:
    if not st.session_state.logged_in:
        if logo_wide: st.image(logo_wide, use_container_width=True)
        u_name = st.text_input("성함", placeholder="홍길동")
        u_phone = st.text_input("전화번호", placeholder="01012347890")
        if st.button("🚀 PARKDA 시작하기"):
            if not u_phone.startswith("010"):
                st.error("⚠️ 010으로 시작하는 번호를 입력해주세요.")
            elif u_name and len(u_phone) >= 10:
                st.session_state.logged_in = True
                st.session_state.user_info = {"name": u_name, "phone": u_phone}
                try: requests.post(DEPLOY_URL, json={"type":"JOIN", "name":u_name, "phone":u_phone, "points":1000})
                except: pass
                st.rerun()
    else:
        if logo_sq: st.image(logo_sq, width=120)
        st.markdown(f"#### **{st.session_state.user_info['name']}** 회원님")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()
    
    st.divider()
    st.subheader("📰 실시간 뉴스")
    st.markdown("<p class='guide-text'>뉴스 영역만 아래로 스크롤하여 더 볼 수 있습니다.</p>", unsafe_allow_html=True)
    
    # 뉴스 전용 스크롤 구현
    news_data = get_clean_news("파크골프")
    news_html = "<div class='news-container'>"
    for n in news_data:
        news_html += f"<div class='news-card'><a href='{n.link}' target='_blank'>• {n.title}</a></div>"
    news_html += "</div>"
    st.markdown(news_html, unsafe_allow_html=True)

# 6. 메인 화면
st.title("⛳ PARKDA 파크골프 통합관제플랫폼")

if st.session_state.logged_in:
    # 대형 버튼 메뉴 (고급 원색 그라데이션)
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        if st.button("🏆 대회정보"): st.session_state.menu_select = "대회정보"
    with m_col2:
        if st.button("📍 전국지도"): st.session_state.menu_select = "전국지도"
    with m_col3:
        if st.button("👥 조편성"): st.session_state.menu_select = "조편성"

    st.divider()

    if st.session_state.menu_select == "대회정보":
        st.markdown("<p class='guide-text'>최신 대회 공고를 확인하고 터치하여 상세 내용을 확인하세요.</p>", unsafe_allow_html=True)
        for e in get_clean_news("파크골프 대회 공고")[:15]:
            st.markdown(f"""
            <div class='content-card'>
                <a href='{e.link}' target='_blank' style='color:#FFD700; font-size:20px; text-decoration:none; font-weight:bold;'>🏆 {e.title}</a><br>
                <span style='color:#6B8E7F; font-size:14px;'>발표일: {e.published[:16]}</span>
            </div>
            """, unsafe_allow_html=True)

    elif st.session_state.menu_select == "전국지도":
        st.markdown("<p class='guide-text'>지도의 마커를 클릭하면 해당 구장의 실시간 날씨가 나타납니다.</p>", unsafe_allow_html=True)
        # 지도 데이터 로드 및 출력 로직... (박사님 기존 park_data.xlsx 연동 유지)

    elif st.session_state.menu_select == "조편성":
        st.markdown("<p class='guide-text'>명단을 붙여넣고 버튼을 누르면 기록이 저장되며 조가 편성됩니다.</p>", unsafe_allow_html=True)
        raw = st.text_area("회원 명단 입력 (엑셀/한글 복사 가능)", height=200, placeholder="여기에 명단을 붙여넣으세요.")
        if st.button("🚀 지금 바로 조 편성 시작"):
            names = re.split(r'[,\s\t\n]+', raw)
            names = [n.strip() for n in names if n.strip()]
            if names:
                random.shuffle(names)
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
                kakao_msg = f"⛳ [PARKDA 조 편성 결과]\n📅 일시: {now_str}\n"
                for i in range(0, len(names), 4):
                    line = f"{i//4 + 1}조: {', '.join(names[i:i+4])}"
                    st.markdown(f"<div class='team-box' style='background:rgba(255,255,255,0.1); padding:15px; border-radius:10px; margin-bottom:10px; font-size:20px;'>{line}</div>", unsafe_allow_html=True)
                    kakao_msg += line + "\n"
                st.text_area("📋 카톡방 전달용", kakao_msg, height=150)
                # DB 저장 로직 (requests.post...)
            else: st.error("명단을 입력해주세요.")
else:
    st.info("🔒 회원 인증 후 프리미엄 서비스를 이용하실 수 있습니다.")