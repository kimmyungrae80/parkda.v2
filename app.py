import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import feedparser
import os

# 페이지 설정
st.set_page_config(page_title="PARKDA 2.0", layout="wide")

# 1. 데이터 로드 (더 강력한 자동 매칭)
@st.cache_data
def load_data():
    file_name = "park_data.xlsx"
    if os.path.exists(file_name):
        # 첫 번째 시트를 강제로 읽음
        df = pd.read_excel(file_name, sheet_name=0)
        cols = df.columns.tolist()
        
        # 컬럼 매칭 로직 (이름이 조금 달라도 찾아냄)
        try:
            name_col = [c for c in cols if any(x in str(c) for x in ['구장', '이름', '명칭'])][0]
            addr_col = [c for c in cols if any(x in str(c) for x in ['주소', '위치'])][0]
            lat_col = [c for c in cols if any(x in str(c).lower() for x in ['위도', 'lat'])][0]
            lon_col = [c for c in cols if any(x in str(c).lower() for x in ['경도', 'lng', 'lon'])][0]
            hole_col = [c for c in cols if any(x in str(c) for x in ['홀', 'hole'])][0]
            return df, {'name': name_col, 'addr': addr_col, 'lat': lat_col, 'lon': lon_col, 'hole': hole_col}
        except:
            return df, None # 매칭 실패 시 원본만 반환
    return None, None

df, col_map = load_data()

# --- 사이드바 및 메인 레이아웃 (기존과 동일) ---
st.sidebar.title("📰 실시간 파크골프 뉴스")
# ... (뉴스 코드 생략) ...

st.title("⛳ PARKDA 2.0: 지능형 통합 관제 플랫폼")
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📍 전국 구장 실시간 맵")
    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="cartodbpositron")
    
    if df is not None and col_map is not None:
        for _, row in df.iterrows():
            try:
                # 숫자 데이터로 변환 시도 (공백 제거 등)
                lat = float(str(row[col_map['lat']]).strip())
                lon = float(str(row[col_map['lon']]).strip())
                name = str(row[col_map['name']])
                
                folium.Marker(
                    location=[lat, lon],
                    popup=f"<b>{name}</b><br>{row[col_map['addr']]}",
                    tooltip=name
                ).add_to(m)
            except:
                continue # 한 줄 에러 나도 무시하고 다음 마커 그리기
        folium_static(m, width=800, height=500)
    else:
        st.warning("⚠️ 데이터를 불러왔으나 좌표 정보를 찾을 수 없습니다. 엑셀 제목을 확인해 주세요.")

with col2:
    st.subheader("📊 데이터 통계")
    if df is not None:
        st.metric("총 등록 구장", f"{len(df)}개")
    st.metric("운영 상태", "정상 (Open-Loop)")