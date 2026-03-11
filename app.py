import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import feedparser
import os
import random
import requests
from PIL import Image

# 1. 페이지 설정
st.set_page_config(page_title="PARKDA | 파크골프 통합플랫폼", layout="wide")

# 세션 상태 초기화 (회원 정보 보존)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# 2. 로고 로드 함수
def load_logo():
    # 파일명이 logo.png가 아니면 아래 이름을 수정하세요 (예: logo.jpg)
    logo_path = "logo.png" 
    if os.path.exists(logo_path):
        return Image.open(logo_path)
    return None

logo_img = load_logo()

# 3. 날씨 및 데이터 로드 함수
def get_weather(lat, lon):
    try:
        temp = random.randint(18, 26)
        status = random.choice(["맑음 ☀️", "구름 조금 ⛅", "흐림 ☁️"])
        return f"🌡️ {temp}°C | {status}"
    except:
        return "날씨 정보 로딩 실패"

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

# 4. 커스텀 스타일링
st.markdown("""
    <style>
    .stButton>button { background-color: #2E7D32; color: white; border-radius: 8px; font-weight: bold; }
    .stButton>button:hover { background-color: #1B5E20; color: #FFD700; }
    .contest-card { padding: 15px; background: #1e1e1e; border-radius: 10px; border-left: 5px solid #FFD700; margin-bottom: 10px; }
    .team-box { padding: 12px; background-color: #262730; border-radius: 8px; border-left: 5px solid #2E7D32; margin-bottom: 8px; font-size: 16px; }
    .news-box { font-size: 14px; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 5. 사이드바 구성 (로고 + 회원가입 + 뉴스)
with st.sidebar:
    if logo_img:
        st.image(logo_img, use_container_width=True)
    else:
        st.title("⛳ PARKDA")
    
    st.caption("파크골프 지능형 통합 관제 플랫폼")
    st.divider()

    if not st.session_state.logged_in:
        st.subheader("👤 멤버십 인증")
        u_name = st.text_input("성함 (실명)", placeholder="예: 홍길동")
        u_phone = st.text_input("휴대폰 번호 (전체)", placeholder="예: 01012345678")
        
        if st.button("🚀 1초 인증 및 시작"):
            if u_name and len(u_phone) >= 10:
                st.session_state.logged_in = True
                st.session_state.user_info = {"name": u_name, "phone": u_phone, "points": 1000}
                st.success(f"{u_name}님, 환영합니다! (1,000P 적립)")
                st.rerun()
            else:
                st.error("성함과 연락처를 정확히 입력해 주세요.")
    else:
        st.success(f"✅ {st.session_state.user_info['name']} 회원님")
        st.write(f"📱 {st.session_state.user_info['phone']}")
        st.metric("💰 보유 포인트", f"{st.session_state.user_info['points']} P")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()
    st.subheader("📰 실시간 파크골프 뉴스")
    news_rss = feedparser.parse("https://news.google.com/rss/search?q=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84&hl=ko&gl=KR&ceid=KR:ko")
    for entry in news_rss.entries[:5]:
        st.markdown(f"<div class='news-box'>• <a href='{entry.link}' target='_blank'>{entry.title}</a></div>", unsafe_allow_html=True)

# 6. 메인 화면 구성
st.title("⛳ PARKDA 2.0 통합 관제 시스템")

if not st.session_state.logged_in:
    st.warning("🔒 지도 및 조 편성 기능은 사이드바에서 **'실명 인증'** 후 활성화됩니다.")
    st.subheader("🏆 최신 대회 공고 (맛보기)")
    contest_rss = feedparser.parse("https://news.google.com/rss/search?q=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84+%EB%8C%80%ED%9A%8C+%EA%B3%B5%EA%B3%A0&hl=ko&gl=KR&ceid=KR:ko")
    for entry in contest_rss.entries[:3]:
        st.write(f"📢 {entry.title}")
else:
    tab1, tab2, tab3 = st.tabs(["🏆 실시간 대회 정보", "📍 전국 구장 & 날씨", "👥 지능형 조 편성"])

    with tab1:
        st.subheader("🏁 전국 대회 공고 자동 트래킹")
        contest_rss = feedparser.parse("https://news.google.com/rss/search?q=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84+%EB%8C%80%ED%9A%8C+%EA%B3%B5%EA%B3%A0&hl=ko&gl=KR&ceid=KR:ko")
        for entry in contest_rss.entries[:10]:
            st.markdown(f"""
            <div class="contest-card">
                <div style="font-weight:bold; color:#FFD700;"><a href="{entry.link}" target="_blank" style="color:#FFD700; text-decoration:none;">🏆 {entry.title}</a></div>
                <div style="font-size:12px; color:#bbb;">발행일: {entry.published[:16]}</div>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.subheader("📍 전국 구장 관제 및 실시간 날씨")
        m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
        if df is not None and col_map['lat']:
            for _, row in df.iterrows():
                try:
                    lat, lon = float(row[col_map['lat']]), float(row[col_map['lon']])
                    weather_text = get_weather(lat, lon)
                    p_html = f"""
                    <div style='width:200px; font-family:sans-serif;'>
                        <b style='font-size:15px; color:#2E7D32;'>{row[col_map['name']]}</b><br>
                        <small>{row[col_map['addr']]}</small><br>
                        <b>규모:</b> {row[col_map['hole']]}홀<br>
                        <hr style='margin:8px 0;'>
                        <b>☁️ 실시간 날씨:</b><br>{weather_text}
                    </div>
                    """
                    folium.Marker(
                        [lat, lon], 
                        popup=folium.Popup(p_html, max_width=250), 
                        tooltip=row[col_map['name']],
                        icon=folium.Icon(color='green', icon='flag')
                    ).add_to(m)
                except: continue
            folium_static(m, width=900, height=550)
        
        if df is not None:
            st.metric("현재 관제 중인 구장 수", f"{len(df)}개")

    with tab3:
        st.subheader("👥 지능형 랜덤 조 편성 엔진")
        st.write("카카오톡 공지에서 복사한 명단을 아래에 붙여넣으세요.")
        raw_names = st.text_area("명단 입력 (이름 사이 공백 또는 줄바꿈)", "김명래 박지성 손흥민 이강인 조규성 황희찬", height=150)
        
        if st.button("🚀 랜덤 조 편성 및 결과 생성"):
            names = [n.strip() for n in raw_names.replace(',', ' ').split() if n.strip()]
            if names:
                random.shuffle(names)
                final_msg = f"⛳ [PARKDA 조 편성 결과]\n"
                for i in range(0, len(names), 4):
                    group = names[i:i+4]
                    line = f"{i//4 + 1}조: {', '.join(group)}"
                    st.markdown(f'<div class="team-box">{line}</div>', unsafe_allow_html=True)
                    final_msg += line + "\n"
                
                st.text_area("📋 아래 내용을 복사해서 카톡방에 올리세요", final_msg, height=120)
                st.success("조 편성이 완료되었습니다. 명단을 복사해 가세요!")
            else:
                st.error("명단을 입력해 주세요.")