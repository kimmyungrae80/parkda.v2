import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import feedparser

# 페이지 설정
st.set_page_config(page_title="PARKDA 2.0", layout="wide")

# 스타일 설정 (사이드바 뉴스 스크롤 기능 추가)
st.markdown("""
    <style>
    .reportview-container { background: #0e1117; color: white; }
    /* 뉴스 리스트 스크롤 박스 */
    .news-container {
        max-height: 400px;
        overflow-y: auto;
        padding-right: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 1. 데이터 로드
@st.cache_data
def load_data():
    df = pd.read_excel("경기장_정보.xlsx")
    return df

df = load_data()

# --- 사이드바: 실시간 뉴스 (3개 노출, 스크롤 10개) ---
st.sidebar.title("📰 실시간 파크골프 뉴스")
feed_url = "https://news.google.com/rss/search?q=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84&hl=ko&gl=KR&ceid=KR:ko"
rss_feed = feedparser.parse(feed_url)

if rss_feed.entries:
    st.sidebar.markdown('<div class="news-container">', unsafe_allow_html=True)
    # 최대 10개까지만 가져와서 리스트업
    for entry in rss_feed.entries[:10]:
        st.sidebar.markdown(f"**[{entry.title}]({entry.link})**")
        st.sidebar.write(f"📅 {entry.published[:16]}")
        st.sidebar.markdown("---")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
else:
    st.sidebar.write("최신 뉴스를 불러올 수 없습니다.")

st.sidebar.title("👥 스마트 조 편성")
player_names = st.sidebar.text_area("명단 입력", "홍길동, 김철수, 이영희, 박지성")

# --- 메인 화면 ---
st.title("⛳ PARKDA 2.0: 지능형 통합 관제 플랫폼")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📍 전국 구장 실시간 맵 (마커를 클릭하세요)")
    
    # 지도 생성 (한국 중심)
    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
    
    # 2. 마커 추가 (구장 정보 팝업 기능 추가)
    for _, row in df.iterrows():
        # 팝업에 표시될 HTML 구성
        popup_html = f"""
        <div style="width:200px; font-family: 'Malgun Gothic';">
            <h4 style="margin-bottom:5px; color:#2E7D32;">{row['구장명']}</h4>
            <p style="font-size:12px; margin:2px 0;"><b>주소:</b> {row['주소']}</p>
            <p style="font-size:12px; margin:2px 0;"><b>홀 수:</b> {row['홀수']}홀</p>
        </div>
        """
        popup = folium.Popup(popup_html, max_width=250)
        
        folium.Marker(
            location=[row['위도'], row['경도']],
            popup=popup,
            tooltip=row['구장명'],  # 마우스만 올려도 이름이 보임
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    folium_static(m, width=800, height=500)

with col2:
    st.subheader("📊 데이터 통계")
    st.metric("총 등록 구장", f"{len(df)}개")
    st.metric("운영 상태", "정상 (Open-Loop)")
    
    st.info("💡 지도 위의 마커를 클릭하면 구장의 상세 정보(주소, 홀 수 등)를 확인할 수 있습니다.")