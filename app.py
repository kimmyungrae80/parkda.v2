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

# 3. 가독성 중심 스타일 설정 (정부24 스타일: 화이트 배경 + 블루/네이비 포인트)
st.markdown("""
    <style>
    /* 전체 배경 흰색 및 폰트 설정 */
    html, body, [data-testid="stAppViewContainer"] { background-color: #F8F9FA !important; color: #333 !important; }
    
    /* 대형 버튼 메뉴 (원색 대신 세련된 포인트) */
    .stButton>button {
        width: 100%; height: 70px !important; font-size: 22px !important;
        border-radius: 12px !important; border: 2px solid #E9ECEF !important;
        background-color: white !important; color: #495057 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: 0.3s;
    }
    
    /* 메뉴 선택 시 강조색 (정부24 블루) */
    .stButton>button:active, .stButton>button:focus { border: 2px solid #0056b3 !important; background-color: #E7F1FF !important; color: #0056b3 !important; }

    /* 카드 스타일 (깔끔한 화이트 카드) */
    .contest-card { padding: 20px; background: white; border-radius: 12px; border: 1px solid #DEE2E6; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); }
    .team-box { padding: 15px; background-color: white; border-radius: 10px; border: 1px solid #CED4DA; margin-bottom: 8px; font-size: 20px; }
    
    /* 옅은 가이드 글씨 */
    .guide-text { color: #868E96; font-size: 16px; font-weight: normal; margin-bottom: 10px; }
    
    /* 뉴스 스크롤 영역 */
    .news-scroll { max-height: 450px; overflow-y: scroll; padding-right: 10px; border: 1px solid #E9ECEF; border-radius: 8px; background: white; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 유틸리티 함수 (기능 동일) ---
def get_clean_news(query):
    try:
        safe_query = urllib.parse.quote(f"{query} 네이버뉴스")
        rss_url = f"https://news.google.com/rss/search?q={safe_query}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        seen = set()
        unique = []
        for e in feed.entries:
            key = e.title[:12].replace(" ", "")
            if key not in seen:
                seen.add(key)
                unique.append(e)
        unique.sort(key=lambda x: getattr(x, 'published_parsed', 0), reverse=True)
        return unique
    except: return []

# 4. 사이드바
with st.sidebar:
    if not st.session_state.logged_in:
        if logo_wide: st.image(logo_wide)
        st.markdown("<p class='guide-text'>성함과 번호를 입력하여 플랫폼을 시작하세요.</p>", unsafe_allow_html=True)
        u_name = st.text_input("성함")
        u_phone = st.text_input("전화번호")
        if st.button("로그인"):
            if u_name and len(u_phone) >= 10:
                st.session_state.logged_in = True
                st.session_state.user_info = {"name": u_name, "phone": u_phone}
                requests.post(DEPLOY_URL, json={"type":"JOIN", "name":u_name, "phone":u_phone})
                st.rerun()
    else:
        if logo_sq: st.image(logo_sq, width=120)
        st.success(f"{st.session_state.user_info['name']} 회원님")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()
    
    st.divider()
    st.subheader("📰 실시간 뉴스")
    st.markdown("<p class='guide-text'>화면을 아래로 내리면 지난 뉴스를 볼 수 있습니다.</p>", unsafe_allow_html=True)
    news_data = get_clean_news("파크골프")
    # 뉴스 스크롤 기능 복구
    news_html = "<div class='news-scroll'>"
    for n in news_data:
        news_html += f"<p>• <a href='{n.link}' target='_blank' style='color:#333; text-decoration:none;'>{n.title}</a></p><hr style='border:0.1px solid #f0f0f0;'>"
    news_html += "</div>"
    st.markdown(news_html, unsafe_allow_html=True)

# 5. 메인 화면
st.title("⛳ PARKDA 파크골프 통합관제플랫폼")

if st.session_state.logged_in:
    # 대형 메뉴 (정부24 스타일 블루 포인트)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏆 대회정보"): st.session_state.menu_select = "대회정보"
    with col2:
        if st.button("📍 전국지도"): st.session_state.menu_select = "전국지도"
    with col3:
        if st.button("👥 조편성"): st.session_state.menu_select = "조편성"

    st.divider()

    if st.session_state.menu_select == "대회정보":
        st.markdown("<p class='guide-text'>전국의 파크골프 대회 공고를 최신순으로 확인하세요.</p>", unsafe_allow_html=True)
        for e in get_clean_news("파크골프 대회 공고")[:15]:
            st.markdown(f"<div class='contest-card'><a href='{e.link}' target='_blank' style='color:#0056b3; font-size:22px;'>{e.title}</a><br><span style='color:#999;'>{e.published[:16]}</span></div>", unsafe_allow_html=True)

    elif st.session_state.menu_select == "전국지도":
        st.markdown("<p class='guide-text'>지도의 깃발을 누르면 구장별 실시간 날씨가 나타납니다.</p>", unsafe_allow_html=True)
        # 지도 및 날씨 로직 (기존 동일)
        # ... [지도 코드 생략] ...

    elif st.session_state.menu_select == "조편성":
        st.markdown("<p class='guide-text'>이름을 넣고 버튼을 누르면 AI가 공정하게 조를 나누어 드립니다.</p>", unsafe_allow_html=True)
        raw = st.text_area("회원 명단 입력", height=150)
        if st.button("조 편성 시작"):
            names = [n.strip() for n in raw.replace(',', ' ').split() if n.strip()]
            if names:
                random.shuffle(names)
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
                kakao_msg = f"⛳ [PARKDA 조 편성 결과]\n📅 일시: {now_str}\n"
                for i in range(0, len(names), 4):
                    line = f"{i//4 + 1}조: {', '.join(names[i:i+4])}"
                    st.markdown(f"<div class='team-box'>{line}</div>", unsafe_allow_html=True)
                    kakao_msg += line + "\n"
                st.text_area("카톡 복사용", kakao_msg, height=150)
                # DB 전송 생략 (기존 동일)

else:
    st.info("🔒 회원 인증 후 이용이 가능합니다.")