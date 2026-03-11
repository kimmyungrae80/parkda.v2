import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import feedparser
import os
import random
import requests # 날씨 API 호출을 위해 추가

# 1. 페이지 설정 및 세션 상태
st.set_page_config(page_title="PARKDA 2.0 | 지능형 관제", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# 2. 날씨 정보 가져오기 함수 (OpenWeatherMap API 활용 예시)
# API 키가 없어도 작동하도록 기본값(시뮬레이션)을 설정해두었습니다.
def get_weather(lat, lon):
    try:
        # 박사님이 나중에 API 키를 넣으시면 실시간으로 작동합니다.
        # api_key = "YOUR_API_KEY"
        # url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=kr"
        # res = requests.get(url).json()
        # return f"🌡️ {res['main']['temp']}°C | {res['weather'][0]['description']}"
        
        # 지금은 시뮬레이션용 데이터
        temp = random.randint(18, 25)
        status = random.choice(["맑음 ☀️", "구름 조금 ⛅", "흐림 ☁️"])
        return f"🌡️ 현재 {temp}°C | {status}"
    except:
        return "날씨 정보 로딩 실패"

# 3. 데이터 로드 로직 (보존)
@st.cache_data
def load_data():
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

df, col_map = load_data()

# --- 사이드바: 기존 기능 보존 ---
with st.sidebar:
    st.title("👤 PARKDA 멤버십")
    if not st.session_state.logged_in:
        u_name = st.text_input("성함", "홍길동")
        if st.button("카카오 로그인 (시뮬레이션)"):
            st.session_state.logged_in = True
            st.session_state.user_info = {"name": u_name, "club": "대전 동구 클럽", "points": 1000}
            st.rerun()
    else:
        st.success(f"어서오세요, {st.session_state.user_info['name']}님!")
        st.metric("💰 내 포인트", f"{st.session_state.user_info['points']} P")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()
    st.title("📰 실시간 뉴스")
    news_rss = feedparser.parse("https://news.google.com/rss/search?q=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84&hl=ko&gl=KR&ceid=KR:ko")
    for entry in news_rss.entries[:5]:
        st.markdown(f"• [{entry.title}]({entry.link})")

# --- 메인 화면: 탭 구조 보존 및 날씨 기능 삽입 ---
st.title("⛳ PARKDA 2.0: 지능형 통합 관제 플랫폼")

tab1, tab2, tab3 = st.tabs(["🏆 대회 정보", "📍 전국 지도 & 날씨", "👥 게임 & 조 편성"])

with tab1:
    st.subheader("🏁 최신 대회 공고 트래킹")
    contest_rss = feedparser.parse("https://news.google.com/rss/search?q=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84+%EB%8C%80%ED%9A%8C+%EA%B3%B5%EA%B3%A0&hl=ko&gl=KR&ceid=KR:ko")
    for entry in contest_rss.entries[:8]:
        st.markdown(f"🏆 **[{entry.title}]({entry.link})**")

with tab2:
    st.subheader("📍 전국 구장 실시간 관제 (날씨 정보 포함)")
    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
    if df is not None and col_map['lat']:
        for _, row in df.iterrows():
            try:
                lat, lon = float(row[col_map['lat']]), float(row[col_map['lon']])
                # [업데이트] 마커 클릭 시 날씨 정보를 실시간으로 생성
                weather_info = get_weather(lat, lon)
                
                p_html = f"""
                <div style='width:200px;'>
                    <b style='font-size:14px; color:#2E7D32;'>{row[col_map['name']]}</b><br><br>
                    <b>주소:</b> {row[col_map['addr']]}<br>
                    <b>규모:</b> {row[col_map['hole']]}홀<br>
                    <hr style='margin:10px 0;'>
                    <b style='color:#007BFF;'>☁️ 실시간 날씨:</b><br>{weather_info}
                </div>
                """
                folium.Marker(
                    [lat, lon], 
                    popup=folium.Popup(p_html, max_width=250), 
                    tooltip=row[col_map['name']],
                    icon=folium.Icon(color='blue', icon='cloud', prefix='fa')
                ).add_to(m)
            except: continue
        folium_static(m, width=900, height=550)

with tab3:
    # 기존 조 편성 로직 보존
    st.subheader("👥 실시간 조 편성 엔진")
    raw_names = st.text_area("명단 입력 (공백 구분)", "박사님 동호인1 동호인2 동호인3", height=150)
    if st.button("🚀 조 편성 실행"):
        names = [n.strip() for n in raw_names.replace(',', ' ').split() if n.strip()]
        if names:
            random.shuffle(names)
            for i in range(0, len(names), 4):
                st.info(f"⛳ {i//4 + 1}조: {', '.join(names[i:i+4])}")