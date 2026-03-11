import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import feedparser
import os
import random

# 1. 페이지 설정
st.set_page_config(page_title="PARKDA 2.0", layout="wide")

# 2. 스타일 설정 (뉴스 스크롤 및 조 편성 디자인)
st.markdown("""
    <style>
    .news-container { max-height: 400px; overflow-y: auto; padding-right: 10px; }
    .team-box { padding: 10px; background-color: #262730; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #2E7D32; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 (지능형 컬럼 매칭)
@st.cache_data
def load_data():
    file_name = "park_data.xlsx"
    if not os.path.exists(file_name):
        return None, None
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
    except:
        return None, None

df, col_map = load_data()

# --- 사이드바: 뉴스 및 조 편성 ---
st.sidebar.title("📰 실시간 파크골프 뉴스")
rss_feed = feedparser.parse("https://news.google.com/rss/search?q=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84&hl=ko&gl=KR&ceid=KR:ko")
if rss_feed.entries:
    st.sidebar.markdown('<div class="news-container">', unsafe_allow_html=True)
    for entry in rss_feed.entries[:10]:
        st.sidebar.markdown(f"**[{entry.title}]({entry.link})**")
        st.sidebar.write(f"📅 {entry.published[:16]}")
        st.sidebar.markdown("---")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.title("👥 4인 기준 랜덤 조 편성")
# 박사님 요청: 쉼표 없이 이름만 계속 입력 가능
raw_names = st.sidebar.text_area("이름을 띄어쓰기나 줄바꿈으로 입력하세요", "홍길동 김철수 이영희 박지성 강호동 유재석", height=150)

if st.sidebar.button("랜덤 조 편성 시작"):
    # 입력된 텍스트에서 이름만 추출 (공백, 쉼표, 줄바꿈 모두 대응)
    name_list = [n.strip() for n in raw_names.replace(',', ' ').split() if n.strip()]
    
    if len(name_list) > 0:
        random.shuffle(name_list)
        st.sidebar.success(f"총 {len(name_list)}명 편성 완료")
        
        # 4명씩 조 나누기
        for i in range(0, len(name_list), 4):
            team_names = name_list[i:i+4]
            st.sidebar.markdown(f"""
            <div class="team-box">
                <b>⛳ {i//4 + 1}조:</b> {', '.join(team_names)}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.sidebar.error("이름을 입력해 주세요.")

# --- 메인 화면 ---
st.title("⛳ PARKDA 2.0: 통합 관제 플랫폼")
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📍 전국 구장 실시간 맵")
    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
    if df is not None and col_map['lat']:
        for _, row in df.iterrows():
            try:
                lat, lon = float(row[col_map['lat']]), float(row[col_map['lon']])
                popup_c = f"<b>{row[col_map['name']]}</b><br>{row[col_map['addr']]}<br>{row[col_map['hole']]}홀"
                folium.Marker([lat, lon], popup=folium.Popup(popup_c, max_width=250), tooltip=row[col_map['name']]).add_to(m)
            except: continue
        folium_static(m, width=850, height=550)

with col2:
    st.subheader("📊 통계")
    if df is not None: st.metric("총 등록 구장", f"{len(df)}개")
    st.info("💡 마커 클릭 시 상세 정보가 표시됩니다.")