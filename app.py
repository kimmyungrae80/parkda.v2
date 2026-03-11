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

# 1. 페이지 설정 및 상태 관리
st.set_page_config(page_title="PARKDA 파크골프 통합관제플랫폼", layout="wide")

# 구글 시트 웹 앱 URL
DEPLOY_URL = "https://script.google.com/macros/s/AKfycbxxa5VMQJXNKrxuuEZsqRQGzy7qBlDu9_M-Q2BlQhNs69LRYRERescREiI-sjCnOPz5/exec"

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'menu_select' not in st.session_state:
    st.session_state.menu_select = "HOME"

# 로고 클릭 시 홈으로 이동하는 함수
def go_home():
    st.session_state.menu_select = "HOME"

# 2. 로고 로드
logo_wide = Image.open("파크다가로형한글2@600x.png") if os.path.exists("파크다가로형한글2@600x.png") else None
logo_sq = Image.open("파크다세로형한글2@600x.png") if os.path.exists("파크다세로형한글2@600x.png") else None

# 3. 🛠️ 프리미엄 다크 & 반응형 UI 디자인
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* 딥 다크 배경 */
    [data-testid="stAppViewContainer"] { 
        background-color: #030A07 !important; 
        color: #E2E8F0 !important;
        font-family: 'Pretendard', sans-serif !important;
    }
    
    [data-testid="stSidebar"] { 
        background-color: #010503 !important; 
        border-right: 1px solid #143D30;
    }

    /* 반응형 로고 버튼 스타일 */
    .logo-btn { cursor: pointer; transition: 0.3s; width: 100%; border-radius: 10px; }
    .logo-btn:hover { opacity: 0.8; transform: scale(0.98); }

    /* 대형 메뉴 버튼 (주황, 파랑, 녹색) */
    .stButton>button {
        width: 100%; height: 95px !important; font-size: 24px !important; font-weight: 800 !important;
        border-radius: 16px !important; border: 1px solid rgba(255,255,255,0.1) !important;
        transition: 0.4s; box-shadow: 0 8px 20px rgba(0,0,0,0.5);
    }
    div[data-testid="column"]:nth-child(1) button { background: linear-gradient(135deg, #FF6F00, #E65100) !important; color: white !important; }
    div[data-testid="column"]:nth-child(2) button { background: linear-gradient(135deg, #007AFF, #004494) !important; color: white !important; }
    div[data-testid="column"]:nth-child(3) button { background: linear-gradient(135deg, #1B5E20, #0D2E10) !important; color: white !important; }

    /* 뒤로가기 버튼 스타일 */
    .back-btn button {
        height: 45px !important; font-size: 16px !important; background: #334155 !important; border: none !important;
    }

    /* AI 조 편성 결과 디자인 */
    .ai-card {
        padding: 20px; background: linear-gradient(145deg, #0A1F16, #05120D);
        border-radius: 15px; border-left: 10px solid #2E7D32;
        margin-bottom: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.4);
    }
    .team-label { color: #8DBDA8; font-size: 14px; margin-bottom: 5px; }
    .team-members { color: #FFFFFF; font-size: 22px; font-weight: 800; letter-spacing: 1px; }

    /* 뉴스 독립 스크롤 영역 */
    .news-box {
        height: 480px; overflow-y: scroll; padding: 15px;
        background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid #143D30;
    }
    .news-item { padding: 10px 0; border-bottom: 1px solid #143D30; }
    .news-item a { color: #78A695 !important; text-decoration: none; font-size: 15px; }

    /* 모바일 반응형 대응 */
    @media (max-width: 768px) {
        .stButton>button { height: 80px !important; font-size: 20px !important; }
        .team-members { font-size: 18px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 4. 핵심 로직 (뉴스, 데이터, 조편성)
def get_clean_news(query):
    try:
        safe_query = urllib.parse.quote(f"{query} 네이버뉴스")
        rss_url = f"https://news.google.com/rss/search?q={safe_query}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        return feed.entries
    except: return []

# 5. 사이드바 (로그인 및 뉴스)
with st.sidebar:
    # [기획] 성함 입력 위에 로고 배치 + 클릭 시 홈 리셋
    if logo_wide:
        if st.button("🏠 PARKDA HOME (RESET)", use_container_width=True):
            go_home()
            st.rerun()
        st.image(logo_wide, use_container_width=True)
    
    st.divider()

    if not st.session_state.logged_in:
        st.subheader("👤 멤버십 인증")
        u_name = st.text_input("성함", placeholder="성함을 입력하세요")
        u_phone = st.text_input("연락처", placeholder="01012345678")
        if st.button("🚀 PARKDA 입장"):
            if u_name and u_phone.startswith("010"):
                st.session_state.logged_in = True
                st.session_state.user_info = {"name": u_name, "phone": u_phone}
                try: requests.post(DEPLOY_URL, json={"type":"JOIN", "name":u_name, "phone":u_phone}, timeout=5)
                except: pass
                st.rerun()
            else: st.error("성함과 010 번호를 확인해주세요.")
    else:
        st.success(f"✅ {st.session_state.user_info['name']} 회원님")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()
    st.subheader("📰 실시간 파크골프 뉴스")
    news_html = "<div class='news-box'>"
    for n in get_clean_news("파크골프")[:15]:
        news_html += f"<div class='news-item'><a href='{n.link}' target='_blank'>• {n.title}</a></div>"
    news_html += "</div>"
    st.markdown(news_html, unsafe_allow_html=True)

# 6. 메인 화면
if not st.session_state.logged_in:
    st.title("⛳ PARKDA 파크골프")
    st.info("왼쪽 인증창에서 회원 인증을 진행해 주세요.")
else:
    # 상단 내비게이션 (홈 이동 및 뒤로가기 대용)
    if st.session_state.menu_select != "HOME":
        if st.button("⬅️ 뒤로가기 (메뉴판으로)", key="back_btn"):
            st.session_state.menu_select = "HOME"
            st.rerun()

    if st.session_state.menu_select == "HOME":
        st.title("⛳ PARKDA 통합관제플랫폼")
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🏆 대회정보"): st.session_state.menu_select = "대회정보"; st.rerun()
        with c2:
            if st.button("📍 전국지도"): st.session_state.menu_select = "전국지도"; st.rerun()
        with c3:
            if st.button("👥 조편성"): st.session_state.menu_select = "조편성"; st.rerun()

    # --- 각 기능 페이지 ---
    elif st.session_state.menu_select == "대회정보":
        st.header("🏆 최신 대회 공고")
        for e in get_clean_news("파크골프 대회 공고")[:10]:
            st.markdown(f"<div class='ai-card'><a href='{e.link}' target='_blank' style='color:#FFD700; font-size:18px; font-weight:bold; text-decoration:none;'>{e.title}</a><br><small>{e.published[:16]}</small></div>", unsafe_allow_html=True)

    elif st.session_state.menu_select == "전국지도":
        st.header("📍 전국 구장 현황")
        # 지도 기능 (간략화된 예시)
        m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
        folium_static(m, width=1000)

    elif st.session_state.menu_select == "조편성":
        st.header("👥 AI 지능형 조 편성")
        st.markdown("<p style='color:#78A695'>이름을 띄어쓰기 없이 나열해도 AI가 분석하여 랜덤하게 편성합니다.</p>", unsafe_allow_html=True)
        
        # [수정] 띄어쓰기 없는 입력 처리 강화
        raw_input = st.text_area("명단 입력", height=150, placeholder="홍길동김철수이영희박찬호 (이름만 쭉 써도 됩니다)")
        
        if st.button("🚀 지능형 조 편성 실행"):
            # 정규표현식: 2~4글자 한글 이름을 찾아내서 리스트화
            name_list = re.findall(r'[가-힣]{2,4}', raw_input)
            
            if name_list:
                random.shuffle(name_list) # 완전 랜덤 셔플
                st.subheader("🎯 편성 결과")
                
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
                kakao_res = f"⛳ [PARKDA AI 조편성]\n📅 {now_str}\n"
                match_history = ""
                
                for i in range(0, len(name_list), 4):
                    group = name_list[i:i+4]
                    group_str = ", ".join(group)
                    st.markdown(f"""
                        <div class='ai-card'>
                            <div class='team-label'>{i//4 + 1}조</div>
                            <div class='team-members'>{group_str}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    kakao_res += f"{i//4+1}조: {group_str}\n"
                    match_history += f"{i//4+1}조:{group_str} | "
                
                st.text_area("📋 카톡 전달용", kakao_res, height=150)
                
                # 구글 시트 전송
                try: requests.post(DEPLOY_URL, json={"type":"MATCH", "organizer":st.session_state.user_info['name'], "match_result":match_history}, timeout=5)
                except: pass
            else:
                st.error("올바른 이름을 입력해주세요.")