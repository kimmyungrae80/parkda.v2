import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, date
import random
import re
import uuid

# =========================================================
# 1. 기본 설정
# =========================================================
st.set_page_config(
    page_title="PARKDA 파크골프 통합관제플랫폼",
    page_icon="⛳",
    layout="wide"
)

# =========================================================
# 2. 샘플 데이터
#    실제 운영 시 DB/구글시트/API로 교체
# =========================================================
COURSES = [
    {
        "name": "김해 파크골프장",
        "region": "경남",
        "address": "경남 김해시 예시로 101",
        "holes": 18,
        "lat": 35.2281,
        "lon": 128.8894,
        "fee": "5,000원",
        "phone": "055-000-0001",
    },
    {
        "name": "부산 강서 파크골프장",
        "region": "부산",
        "address": "부산 강서구 예시로 55",
        "holes": 18,
        "lat": 35.1796,
        "lon": 128.9400,
        "fee": "4,000원",
        "phone": "051-000-0002",
    },
    {
        "name": "대구 금호강 파크골프장",
        "region": "대구",
        "address": "대구 북구 예시로 77",
        "holes": 18,
        "lat": 35.8714,
        "lon": 128.6014,
        "fee": "4,000원",
        "phone": "053-000-0003",
    },
    {
        "name": "창원 파크골프장",
        "region": "경남",
        "address": "경남 창원시 예시로 88",
        "holes": 9,
        "lat": 35.2283,
        "lon": 128.6811,
        "fee": "3,000원",
        "phone": "055-000-0004",
    },
]

YOUTUBE_CHANNELS = [
    {
        "title": "파크골프 레슨 채널",
        "url": "https://www.youtube.com/results?search_query=파크골프+레슨"
    },
    {
        "title": "파크골프 대회 영상",
        "url": "https://www.youtube.com/results?search_query=파크골프+대회"
    },
    {
        "title": "전국 파크골프장 소개",
        "url": "https://www.youtube.com/results?search_query=파크골프장+소개"
    },
]

PAR_9_DEFAULT = [4, 3, 4, 3, 4, 3, 4, 3, 4]
PAR_18_DEFAULT = [4, 3, 4, 3, 4, 3, 4, 3, 4, 4, 3, 4, 3, 4, 3, 4, 3, 4]

# =========================================================
# 3. 세션 상태 초기화
# =========================================================
def init_session():
    defaults = {
        "logged_in": False,
        "user_name": "",
        "menu": "HOME",
        "matches": {},        # match_id -> match data
        "current_match_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# =========================================================
# 4. 스타일
# =========================================================
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [class*="css"] {
    font-family: 'Pretendard', sans-serif !important;
}
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
.kpi-card {
    padding: 18px;
    border-radius: 18px;
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
    border: 1px solid rgba(255,255,255,0.08);
}
.section-card {
    padding: 18px;
    border-radius: 18px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
}
.match-card {
    padding: 16px;
    border-radius: 16px;
    background: #f8fafc;
    border-left: 8px solid #16a34a;
    margin-bottom: 10px;
}
.title-main {
    font-size: 32px;
    font-weight: 800;
}
.sub-main {
    color: #475569;
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 5. 유틸 함수
# =========================================================
def parse_names(raw_text: str) -> list[str]:
    """
    참가자 이름 입력 파싱
    - 쉼표, 줄바꿈, 슬래시, 공백 기준
    - 2~4글자 한글 이름 위주
    """
    cleaned = raw_text.replace("/", "\n").replace(",", "\n")
    parts = re.split(r"[\n\t ]+", cleaned)
    names = []

    for p in parts:
        p = p.strip()
        if not p:
            continue

        # 한글 2~4자 이름만 우선 채택
        if re.fullmatch(r"[가-힣]{2,4}", p):
            names.append(p)
        else:
            # 띄어쓰기 없이 붙어온 경우 대비: 3글자씩 잘라보는 위험한 방식은 배제
            # 안정성을 위해 무시
            continue

    # 중복 제거(입력 순서 유지)
    unique_names = []
    seen = set()
    for n in names:
        if n not in seen:
            seen.add(n)
            unique_names.append(n)
    return unique_names


def generate_groups(players: list[str], group_size: int) -> list[list[str]]:
    shuffled = players[:]
    random.shuffle(shuffled)
    return [shuffled[i:i+group_size] for i in range(0, len(shuffled), group_size)]


def assign_start_holes(num_groups: int, total_holes: int) -> list[int]:
    """
    샷건/분산 출발처럼 시작 홀 배정
    그룹 수가 홀 수보다 많으면 다시 순환
    """
    holes = list(range(1, total_holes + 1))
    starts = []
    idx = 0
    for _ in range(num_groups):
        starts.append(holes[idx])
        idx = (idx + 1) % len(holes)
    return starts


def build_empty_score_df(players: list[str], hole_count: int) -> pd.DataFrame:
    hole_labels = [f"{i}홀" for i in range(1, hole_count + 1)]
    rows = []
    for player in players:
        row = {"선수명": player}
        for h in hole_labels:
            row[h] = 0
        rows.append(row)
    return pd.DataFrame(rows)


def compute_score_result(score_df: pd.DataFrame, hole_count: int) -> pd.DataFrame:
    hole_cols = [f"{i}홀" for i in range(1, hole_count + 1)]
    result = score_df.copy()

    for col in hole_cols:
        result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0).astype(int)

    result["합계"] = result[hole_cols].sum(axis=1)
    result = result.sort_values(by=["합계", "선수명"], ascending=[True, True]).reset_index(drop=True)
    result["순위"] = result["합계"].rank(method="min", ascending=True).astype(int)
    result = result[["순위", "선수명"] + hole_cols + ["합계"]]
    return result


def get_course_by_name(course_name: str):
    for c in COURSES:
        if c["name"] == course_name:
            return c
    return None


def build_share_text(match: dict, result_df: pd.DataFrame) -> str:
    lines = []
    lines.append("⛳ [PARKDA 경기결과]")
    lines.append(f"대회명: {match['title']}")
    lines.append(f"일시: {match['match_date']}")
    lines.append(f"구장: {match['course_name']}")
    lines.append(f"홀수: {match['hole_count']}홀")
    lines.append("")

    for _, row in result_df.iterrows():
        lines.append(f"{row['순위']}위 {row['선수명']} - {row['합계']}타")

    return "\n".join(lines)


def match_kpis():
    total_matches = len(st.session_state.matches)
    total_players = 0
    total_score_entries = 0

    for m in st.session_state.matches.values():
        total_players += len(m["players"])
        if m.get("score_df") is not None:
            total_score_entries += 1

    return total_matches, total_players, total_score_entries

# =========================================================
# 6. 로그인 UI
# =========================================================
with st.sidebar:
    st.markdown("## ⛳ PARKDA")
    st.caption("파크골프 통합관제플랫폼 MVP 1차")

    if not st.session_state.logged_in:
        name = st.text_input("성함", placeholder="홍길동")
        phone = st.text_input("연락처", placeholder="01012345678")

        if st.button("로그인", use_container_width=True):
            if name.strip() and phone.startswith("010") and len(phone) >= 10:
                st.session_state.logged_in = True
                st.session_state.user_name = name.strip()
                st.rerun()
            else:
                st.error("성함과 010 번호를 확인해주세요.")
    else:
        st.success(f"✅ {st.session_state.user_name} 님")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_name = ""
            st.session_state.menu = "HOME"
            st.rerun()

        st.divider()
        st.markdown("### 메뉴")
        if st.button("🏠 HOME", use_container_width=True):
            st.session_state.menu = "HOME"
            st.rerun()
        if st.button("📝 경기 생성", use_container_width=True):
            st.session_state.menu = "CREATE_MATCH"
            st.rerun()
        if st.button("📋 경기 목록", use_container_width=True):
            st.session_state.menu = "MATCH_LIST"
            st.rerun()
        if st.button("📍 전국 구장 지도", use_container_width=True):
            st.session_state.menu = "COURSE_MAP"
            st.rerun()
        if st.button("🎥 유튜브 채널", use_container_width=True):
            st.session_state.menu = "YOUTUBE"
            st.rerun()

# =========================================================
# 7. 로그인 전 메인
# =========================================================
if not st.session_state.logged_in:
    st.markdown("<div class='title-main'>⛳ PARKDA 파크골프 통합관제플랫폼</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-main'>경기 생성 · 자동 조편성 · 9홀/18홀 스코어 · 결과 공유</div>", unsafe_allow_html=True)
    st.write("")
    st.info("왼쪽 사이드바에서 로그인 후 이용해주세요.")
    st.stop()

# =========================================================
# 8. HOME
# =========================================================
if st.session_state.menu == "HOME":
    total_matches, total_players, total_score_entries = match_kpis()

    st.markdown("<div class='title-main'>⛳ PARKDA 통합관제 대시보드</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-main'>사용자 MVP 1차 + 운영 관점 핵심 지표</div>", unsafe_allow_html=True)
    st.write("")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"<div class='kpi-card'><h4>전체 경기 수</h4><h2>{total_matches}</h2></div>",
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"<div class='kpi-card'><h4>누적 참가자 수</h4><h2>{total_players}</h2></div>",
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f"<div class='kpi-card'><h4>스코어 입력 경기</h4><h2>{total_score_entries}</h2></div>",
            unsafe_allow_html=True
        )

    st.write("")
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        if st.button("📝 경기 생성", use_container_width=True):
            st.session_state.menu = "CREATE_MATCH"
            st.rerun()
    with m2:
        if st.button("📋 경기 목록", use_container_width=True):
            st.session_state.menu = "MATCH_LIST"
            st.rerun()
    with m3:
        if st.button("📍 전국 구장 지도", use_container_width=True):
            st.session_state.menu = "COURSE_MAP"
            st.rerun()
    with m4:
        if st.button("🎥 유튜브 채널", use_container_width=True):
            st.session_state.menu = "YOUTUBE"
            st.rerun()

    st.write("")
    st.subheader("최근 생성 경기")
    if not st.session_state.matches:
        st.caption("아직 생성된 경기가 없습니다.")
    else:
        recent_matches = list(st.session_state.matches.values())[-5:][::-1]
        for match in recent_matches:
            st.markdown(
                f"""
                <div class='match-card'>
                    <b>{match['title']}</b><br>
                    날짜: {match['match_date']} / 구장: {match['course_name']} / 홀수: {match['hole_count']}홀 / 참가자: {len(match['players'])}명
                </div>
                """,
                unsafe_allow_html=True
            )

# =========================================================
# 9. 경기 생성
# =========================================================
elif st.session_state.menu == "CREATE_MATCH":
    st.title("📝 경기 생성")

    with st.form("create_match_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("경기명", placeholder="예: 율하센터 친선 9홀 경기")
            match_date = st.date_input("경기일", value=date.today())
            course_name = st.selectbox("구장 선택", [c["name"] for c in COURSES])

        with col2:
            hole_count = st.selectbox("홀 수", [9, 18], index=0)
            group_size = st.selectbox("조당 인원", [3, 4], index=1)
            organizer = st.text_input("주최자", value=st.session_state.user_name)

        raw_players = st.text_area(
            "참가자 명단",
            height=180,
            placeholder="홍길동\n김철수\n이영희\n박민수\n...\n\n쉼표, 줄바꿈, 공백 구분 가능"
        )

        submitted = st.form_submit_button("🚀 경기 생성")

    if submitted:
        players = parse_names(raw_players)

        if not title.strip():
            st.error("경기명을 입력해주세요.")
        elif len(players) < 2:
            st.error("참가자는 최소 2명 이상 입력해주세요. 이름은 줄바꿈/쉼표로 구분해주세요.")
        else:
            groups = generate_groups(players, group_size)
            starts = assign_start_holes(len(groups), hole_count)

            group_info = []
            for idx, group in enumerate(groups):
                group_info.append({
                    "group_no": idx + 1,
                    "start_hole": starts[idx],
                    "players": group
                })

            match_id = str(uuid.uuid4())[:8]
            score_df = build_empty_score_df(players, hole_count)

            st.session_state.matches[match_id] = {
                "id": match_id,
                "title": title.strip(),
                "match_date": str(match_date),
                "course_name": course_name,
                "hole_count": hole_count,
                "group_size": group_size,
                "organizer": organizer.strip(),
                "players": players,
                "groups": group_info,
                "score_df": score_df,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "par_list": PAR_9_DEFAULT if hole_count == 9 else PAR_18_DEFAULT,
            }
            st.session_state.current_match_id = match_id
            st.success(f"경기가 생성되었습니다. 경기 ID: {match_id}")

    st.write("")
    st.subheader("생성된 조편성 미리보기")
    current_id = st.session_state.current_match_id

    if current_id and current_id in st.session_state.matches:
        match = st.session_state.matches[current_id]
        for g in match["groups"]:
            st.markdown(
                f"""
                <div class='match-card'>
                    <b>{g['group_no']}조</b> | 시작홀: {g['start_hole']}홀<br>
                    참가자: {", ".join(g['players'])}
                </div>
                """,
                unsafe_allow_html=True
            )

        if st.button("이 경기 스코어 입력하러 가기", use_container_width=True):
            st.session_state.menu = f"SCORE_{current_id}"
            st.rerun()

# =========================================================
# 10. 경기 목록
# =========================================================
elif st.session_state.menu == "MATCH_LIST":
    st.title("📋 경기 목록")

    if not st.session_state.matches:
        st.info("생성된 경기가 없습니다.")
    else:
        match_ids = list(st.session_state.matches.keys())[::-1]

        for mid in match_ids:
            match = st.session_state.matches[mid]
            col1, col2, col3 = st.columns([6, 2, 2])

            with col1:
                st.markdown(
                    f"""
                    <div class='match-card'>
                        <b>{match['title']}</b><br>
                        경기일: {match['match_date']} / 구장: {match['course_name']} / 홀수: {match['hole_count']}홀 / 참가자: {len(match['players'])}명
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                if st.button(f"스코어 입력 {mid}", key=f"score_{mid}", use_container_width=True):
                    st.session_state.current_match_id = mid
                    st.session_state.menu = f"SCORE_{mid}"
                    st.rerun()

            with col3:
                if st.button(f"결과 보기 {mid}", key=f"result_{mid}", use_container_width=True):
                    st.session_state.current_match_id = mid
                    st.session_state.menu = f"RESULT_{mid}"
                    st.rerun()

# =========================================================
# 11. 구장 지도
# =========================================================
elif st.session_state.menu == "COURSE_MAP":
    st.title("📍 전국 구장 지도")

    region_filter = st.selectbox("지역 선택", ["전체"] + sorted(list(set(c["region"] for c in COURSES))))
    filtered = COURSES if region_filter == "전체" else [c for c in COURSES if c["region"] == region_filter]

    if filtered:
        center_lat = sum(c["lat"] for c in filtered) / len(filtered)
        center_lon = sum(c["lon"] for c in filtered) / len(filtered)
    else:
        center_lat, center_lon = 36.5, 127.8

    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=7)

    for c in filtered:
        popup_html = f"""
        <b>{c['name']}</b><br>
        지역: {c['region']}<br>
        주소: {c['address']}<br>
        홀수: {c['holes']}홀<br>
        이용료: {c['fee']}<br>
        전화: {c['phone']}
        """
        folium.Marker(
            [c["lat"], c["lon"]],
            popup=popup_html,
            tooltip=c["name"],
        ).add_to(fmap)

    st_folium(fmap, width=1200, height=500)

    st.subheader("구장 정보")
    st.dataframe(pd.DataFrame(filtered), use_container_width=True)

# =========================================================
# 12. 유튜브
# =========================================================
elif st.session_state.menu == "YOUTUBE":
    st.title("🎥 파크골프 유튜브 채널")

    st.caption("초기 MVP에서는 검색 링크형으로 연결하고, 이후 YouTube API로 확장 가능합니다.")
    for item in YOUTUBE_CHANNELS:
        st.markdown(
            f"""
            <div class='match-card'>
                <b>{item['title']}</b><br>
                <a href="{item['url']}" target="_blank">{item['url']}</a>
            </div>
            """,
            unsafe_allow_html=True
        )

# =========================================================
# 13. SCORE_xxx / RESULT_xxx 동적 페이지 처리
# =========================================================
elif st.session_state.menu.startswith("SCORE_"):
    match_id = st.session_state.menu.replace("SCORE_", "")
    match = st.session_state.matches.get(match_id)

    if not match:
        st.error("경기 정보를 찾을 수 없습니다.")
        if st.button("HOME으로 이동"):
            st.session_state.menu = "HOME"
            st.rerun()
    else:
        st.title(f"📋 스코어 입력 - {match['title']}")
        st.caption(
            f"{match['match_date']} | {match['course_name']} | {match['hole_count']}홀 | 참가자 {len(match['players'])}명"
        )

        st.subheader("조편성")
        for g in match["groups"]:
            st.markdown(
                f"""
                <div class='match-card'>
                    <b>{g['group_no']}조</b> | 시작홀: {g['start_hole']}홀<br>
                    참가자: {", ".join(g['players'])}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.subheader("PAR 정보")
        par_df = pd.DataFrame({
            "홀": [f"{i}홀" for i in range(1, match["hole_count"] + 1)],
            "PAR": match["par_list"]
        })
        st.dataframe(par_df, use_container_width=True, hide_index=True)

        st.subheader("스코어 입력")
        edited_df = st.data_editor(
            match["score_df"],
            use_container_width=True,
            num_rows="fixed",
            key=f"editor_{match_id}"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 스코어 저장", use_container_width=True):
                st.session_state.matches[match_id]["score_df"] = edited_df
                st.success("스코어가 저장되었습니다.")

        with col2:
            if st.button("📊 결과 보기", use_container_width=True):
                st.session_state.matches[match_id]["score_df"] = edited_df
                st.session_state.menu = f"RESULT_{match_id}"
                st.rerun()

# =========================================================
# 14. RESULT_xxx 동적 페이지 처리
# =========================================================
elif st.session_state.menu.startswith("RESULT_"):
    match_id = st.session_state.menu.replace("RESULT_", "")
    match = st.session_state.matches.get(match_id)

    if not match:
        st.error("결과 정보를 찾을 수 없습니다.")
        if st.button("HOME으로 이동"):
            st.session_state.menu = "HOME"
            st.rerun()
    else:
        st.title(f"📊 경기 결과 - {match['title']}")
        st.caption(
            f"{match['match_date']} | {match['course_name']} | {match['hole_count']}홀 | 주최자: {match['organizer']}"
        )

        result_df = compute_score_result(match["score_df"], match["hole_count"])

        top3 = result_df.head(3)
        c1, c2, c3 = st.columns(3)

        labels = ["🥇 1위", "🥈 2위", "🥉 3위"]
        for idx, col in enumerate([c1, c2, c3]):
            with col:
                if idx < len(top3):
                    st.markdown(
                        f"""
                        <div class='kpi-card'>
                            <h4>{labels[idx]}</h4>
                            <h2>{top3.iloc[idx]['선수명']}</h2>
                            <p>{top3.iloc[idx]['합계']}타</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.write("")
        st.subheader("전체 결과")
        st.dataframe(result_df, use_container_width=True, hide_index=True)

        share_text = build_share_text(match, result_df)
        st.subheader("카톡 공유용 텍스트")
        st.text_area("복사해서 사용하세요", value=share_text, height=220)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ 다시 스코어 수정", use_container_width=True):
                st.session_state.menu = f"SCORE_{match_id}"
                st.rerun()

        with col2:
            if st.button("🏠 HOME", use_container_width=True):
                st.session_state.menu = "HOME"
                st.rerun()

# =========================================================
# 15. 예외적 fallback
# =========================================================
else:
    st.session_state.menu = "HOME"
    st.rerun()