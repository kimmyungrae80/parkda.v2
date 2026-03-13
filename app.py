import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, date
import random
import re
import uuid
import json
from pathlib import Path
import requests

# =========================================================
# 1. 기본 설정
# =========================================================
st.set_page_config(
    page_title="PARKDA 파크골프 통합관제플랫폼 v2",
    page_icon="⛳",
    layout="wide"
)

# =========================================================
# 2. Apps Script 웹앱 URL
# =========================================================
DEPLOY_URL = "https://script.google.com/macros/s/AKfycbyp_boO_2lakqlDT64cxFlmh_wtXcazzoXSjK2MMwUTrSryLzZWaAk7ozSz8sMGlXCG/exec"

# =========================================================
# 3. 로컬 저장 설정
# =========================================================
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
MATCHES_FILE = DATA_DIR / "matches.json"
USERS_FILE = DATA_DIR / "users.json"
COURSES_FILE = DATA_DIR / "courses.json"

DEFAULT_COURSES = [
    {
        "name": "김해 파크골프장",
        "region": "경남",
        "address": "경남 김해시 예시로 101",
        "holes": 18,
        "lat": 35.2281,
        "lon": 128.8894,
        "fee": "5,000원",
        "phone": "055-000-0001"
    },
    {
        "name": "부산 강서 파크골프장",
        "region": "부산",
        "address": "부산 강서구 예시로 55",
        "holes": 18,
        "lat": 35.1796,
        "lon": 128.9400,
        "fee": "4,000원",
        "phone": "051-000-0002"
    },
    {
        "name": "대구 금호강 파크골프장",
        "region": "대구",
        "address": "대구 북구 예시로 77",
        "holes": 18,
        "lat": 35.8714,
        "lon": 128.6014,
        "fee": "4,000원",
        "phone": "053-000-0003"
    },
    {
        "name": "창원 파크골프장",
        "region": "경남",
        "address": "경남 창원시 예시로 88",
        "holes": 9,
        "lat": 35.2283,
        "lon": 128.6811,
        "fee": "3,000원",
        "phone": "055-000-0004"
    }
]

YOUTUBE_CHANNELS = [
    {
        "title": "파크골프 레슨 채널",
        "url": "https://www.youtube.com/results?search_query=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84+%EB%A0%88%EC%8A%A8"
    },
    {
        "title": "파크골프 대회 영상",
        "url": "https://www.youtube.com/results?search_query=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84+%EB%8C%80%ED%9A%8C"
    },
    {
        "title": "전국 파크골프장 소개",
        "url": "https://www.youtube.com/results?search_query=%ED%8C%8C%ED%81%AC%EA%B3%A8%ED%94%84%EC%9E%A5+%EC%86%8C%EA%B0%9C"
    }
]

PAR_9_DEFAULT = [4, 3, 4, 3, 4, 3, 4, 3, 4]
PAR_18_DEFAULT = [4, 3, 4, 3, 4, 3, 4, 3, 4, 4, 3, 4, 3, 4, 3, 4, 3, 4]

# =========================================================
# 4. 저장/로드 유틸
# =========================================================
def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: Path, default):
    if not path.exists():
        save_json(path, default)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def ensure_course_file():
    if not COURSES_FILE.exists():
        save_json(COURSES_FILE, DEFAULT_COURSES)


ensure_course_file()
COURSES = load_json(COURSES_FILE, DEFAULT_COURSES)

# =========================================================
# 5. 세션 상태 초기화
# =========================================================
def init_session():
    defaults = {
        "logged_in": False,
        "user_name": "",
        "phone": "",
        "menu": "HOME",
        "matches": load_json(MATCHES_FILE, {}),
        "users": load_json(USERS_FILE, {}),
        "current_match_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()

# =========================================================
# 6. 스타일
# =========================================================
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
html, body, [class*="css"] {
    font-family: 'Pretendard', sans-serif !important;
}
.block-container {
    padding-top: 1.1rem;
    padding-bottom: 2rem;
}
.kpi-card {
    padding: 18px;
    border-radius: 18px;
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
    border: 1px solid rgba(255,255,255,0.08);
    min-height: 120px;
}
.match-card {
    padding: 16px;
    border-radius: 16px;
    background: #f8fafc;
    border-left: 8px solid #16a34a;
    margin-bottom: 10px;
}
.section-card {
    padding: 18px;
    border-radius: 18px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
}
.title-main {
    font-size: 32px;
    font-weight: 800;
}
.sub-main {
    color: #475569;
    font-size: 15px;
}
.small-muted {
    color: #64748b;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 7. 공용 유틸
# =========================================================
def persist_all():
    save_json(MATCHES_FILE, st.session_state.matches)
    save_json(USERS_FILE, st.session_state.users)


def post_to_gsheet(payload: dict):
    try:
        res = requests.post(DEPLOY_URL, json=payload, timeout=10)
        return res.status_code, res.text
    except Exception as e:
        st.warning(f"구글시트 전송 실패: {e}")
        return None, str(e)


def parse_names(raw_text: str) -> list:
    cleaned = raw_text.replace(",", "\n").replace("/", "\n")
    parts = re.split(r"[\n\t ]+", cleaned)
    names = []
    for p in parts:
        p = p.strip()
        if re.fullmatch(r"[가-힣]{2,4}", p):
            names.append(p)
    unique = []
    seen = set()
    for n in names:
        if n not in seen:
            unique.append(n)
            seen.add(n)
    return unique


def generate_groups(players: list, group_size: int) -> list:
    shuffled = players[:]
    random.shuffle(shuffled)
    return [shuffled[i:i + group_size] for i in range(0, len(shuffled), group_size)]


def assign_start_holes(num_groups: int, total_holes: int) -> list:
    holes = list(range(1, total_holes + 1))
    starts = []
    idx = 0
    for _ in range(num_groups):
        starts.append(holes[idx])
        idx = (idx + 1) % len(holes)
    return starts


def build_empty_score_df(players: list, hole_count: int) -> pd.DataFrame:
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
    return result[["순위", "선수명"] + hole_cols + ["합계"]]


def df_to_records(df: pd.DataFrame) -> list:
    return df.to_dict(orient="records")


def records_to_df(records: list) -> pd.DataFrame:
    return pd.DataFrame(records) if records else pd.DataFrame()


def build_share_text(match: dict, result_df: pd.DataFrame) -> str:
    lines = [
        "⛳ [PARKDA 경기결과]",
        f"대회명: {match['title']}",
        f"일시: {match['match_date']}",
        f"구장: {match['course_name']}",
        f"홀수: {match['hole_count']}홀",
        ""
    ]
    for _, row in result_df.iterrows():
        lines.append(f"{row['순위']}위 {row['선수명']} - {row['합계']}타")
    return "\n".join(lines)


def get_match_kpis():
    total_matches = len(st.session_state.matches)
    total_players = 0
    score_saved_matches = 0
    nine_hole_matches = 0
    eighteen_hole_matches = 0
    for match in st.session_state.matches.values():
        total_players += len(match.get("players", []))
        if match.get("score_df"):
            score_saved_matches += 1
        if match.get("hole_count") == 9:
            nine_hole_matches += 1
        if match.get("hole_count") == 18:
            eighteen_hole_matches += 1
    return {
        "total_matches": total_matches,
        "total_players": total_players,
        "score_saved_matches": score_saved_matches,
        "nine_hole_matches": nine_hole_matches,
        "eighteen_hole_matches": eighteen_hole_matches,
    }


def get_player_stats():
    all_rows = []
    for match in st.session_state.matches.values():
        score_records = match.get("score_df")
        if not score_records:
            continue
        df = records_to_df(score_records)
        if df.empty:
            continue
        result_df = compute_score_result(df, match["hole_count"])
        for _, row in result_df.iterrows():
            all_rows.append({
                "선수명": row["선수명"],
                "합계": int(row["합계"]),
                "순위": int(row["순위"]),
                "홀수": int(match["hole_count"]),
                "경기명": match["title"],
                "일자": match["match_date"],
                "구장": match["course_name"]
            })

    if not all_rows:
        return pd.DataFrame(columns=["선수명", "경기수", "평균타수", "최고성적", "최근경기"])

    base = pd.DataFrame(all_rows)
    grouped = base.groupby("선수명", as_index=False).agg(
        경기수=("합계", "count"),
        평균타수=("합계", "mean"),
        최고성적=("순위", "min")
    )
    grouped["평균타수"] = grouped["평균타수"].round(1)

    recent = base.sort_values(by=["일자"], ascending=False).drop_duplicates(subset=["선수명"])
    grouped = grouped.merge(recent[["선수명", "경기명"]], on="선수명", how="left")
    grouped = grouped.rename(columns={"경기명": "최근경기"})
    grouped = grouped.sort_values(by=["경기수", "평균타수"], ascending=[False, True]).reset_index(drop=True)
    return grouped


def get_course_stats():
    rows = []
    for match in st.session_state.matches.values():
        score_records = match.get("score_df")
        if not score_records:
            continue
        df = records_to_df(score_records)
        if df.empty:
            continue
        result_df = compute_score_result(df, match["hole_count"])
        avg_score = float(result_df["합계"].mean()) if not result_df.empty else 0.0
        rows.append({
            "구장": match["course_name"],
            "경기수": 1,
            "참가자수": len(match.get("players", [])),
            "평균타수": round(avg_score, 1)
        })
    if not rows:
        return pd.DataFrame(columns=["구장", "경기수", "참가자수", "평균타수"])
    df = pd.DataFrame(rows)
    out = df.groupby("구장", as_index=False).agg(
        경기수=("경기수", "sum"),
        참가자수=("참가자수", "sum"),
        평균타수=("평균타수", "mean")
    )
    out["평균타수"] = out["평균타수"].round(1)
    return out.sort_values(by=["경기수", "참가자수"], ascending=[False, False]).reset_index(drop=True)


def register_user(name: str, phone: str):
    key = f"{name}_{phone}"
    is_new = key not in st.session_state.users

    if is_new:
        st.session_state.users[key] = {
            "name": name,
            "phone": phone,
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "login_count": 1,
        }
    else:
        st.session_state.users[key]["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.users[key]["login_count"] = st.session_state.users[key].get("login_count", 0) + 1

    persist_all()

    post_to_gsheet({
        "type": "JOIN",
        "name": name,
        "phone": phone,
        "points": 0,
        "memo": "신규회원" if is_new else "재로그인"
    })

# =========================================================
# 8. 사이드바
# =========================================================
with st.sidebar:
    st.markdown("## ⛳ PARKDA")
    st.caption("파크골프 통합관제플랫폼 v2")

    if not st.session_state.logged_in:
        name = st.text_input("성함", placeholder="홍길동")
        phone = st.text_input("연락처", placeholder="01012345678")
        if st.button("로그인", use_container_width=True):
            if name.strip() and phone.startswith("010") and len(phone) >= 10:
                st.session_state.logged_in = True
                st.session_state.user_name = name.strip()
                st.session_state.phone = phone.strip()
                register_user(name.strip(), phone.strip())
                st.rerun()
            else:
                st.error("성함과 010 번호를 확인해주세요.")
    else:
        st.success(f"✅ {st.session_state.user_name} 님")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_name = ""
            st.session_state.phone = ""
            st.session_state.menu = "HOME"
            st.rerun()

        st.divider()
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
        if st.button("🎥 유튜브", use_container_width=True):
            st.session_state.menu = "YOUTUBE"
            st.rerun()
        if st.button("📈 관리자 KPI", use_container_width=True):
            st.session_state.menu = "ADMIN_KPI"
            st.rerun()
        if st.button("🏅 누적 랭킹", use_container_width=True):
            st.session_state.menu = "RANKING"
            st.rerun()

# =========================================================
# 9. 로그인 전 화면
# =========================================================
if not st.session_state.logged_in:
    st.markdown("<div class='title-main'>⛳ PARKDA 파크골프 통합관제플랫폼</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-main'>경기 생성 · 자동 조편성 · 9홀/18홀 스코어 · 결과 공유 · KPI 대시보드</div>", unsafe_allow_html=True)
    st.write("")
    st.info("왼쪽 사이드바에서 로그인 후 이용해주세요.")
    st.stop()

# =========================================================
# 10. HOME
# =========================================================
if st.session_state.menu == "HOME":
    kpi = get_match_kpis()
    st.markdown("<div class='title-main'>⛳ PARKDA 통합관제 대시보드</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-main'>MVP 2차: 경기 운영 + 누적 데이터 + 관리자 KPI</div>", unsafe_allow_html=True)
    st.write("")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='kpi-card'><h4>전체 경기 수</h4><h2>{kpi['total_matches']}</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='kpi-card'><h4>누적 참가자 수</h4><h2>{kpi['total_players']}</h2></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='kpi-card'><h4>스코어 저장 경기</h4><h2>{kpi['score_saved_matches']}</h2></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='kpi-card'><h4>회원 수</h4><h2>{len(st.session_state.users)}</h2></div>", unsafe_allow_html=True)

    st.write("")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.button("📝 경기 생성", use_container_width=True, on_click=lambda: st.session_state.update(menu="CREATE_MATCH"))
    with q2:
        st.button("📋 경기 목록", use_container_width=True, on_click=lambda: st.session_state.update(menu="MATCH_LIST"))
    with q3:
        st.button("📈 관리자 KPI", use_container_width=True, on_click=lambda: st.session_state.update(menu="ADMIN_KPI"))
    with q4:
        st.button("🏅 누적 랭킹", use_container_width=True, on_click=lambda: st.session_state.update(menu="RANKING"))

    st.write("")
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("최근 생성 경기")
        recent_matches = list(st.session_state.matches.values())[-5:][::-1]
        if not recent_matches:
            st.caption("아직 생성된 경기가 없습니다.")
        else:
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

    with right:
        st.subheader("빠른 현황")
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.write(f"- 9홀 경기 수: {kpi['nine_hole_matches']}")
        st.write(f"- 18홀 경기 수: {kpi['eighteen_hole_matches']}")
        top_courses = get_course_stats().head(3)
        if top_courses.empty:
            st.caption("아직 구장 통계가 없습니다.")
        else:
            st.write("**인기 구장 TOP 3**")
            for _, row in top_courses.iterrows():
                st.write(f"- {row['구장']} / 경기 {row['경기수']}회 / 참가 {row['참가자수']}명")
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 11. 경기 생성
# =========================================================
elif st.session_state.menu == "CREATE_MATCH":
    st.title("📝 경기 생성")
    with st.form("create_match_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("경기명", placeholder="예: 김해 친선 9홀 경기")
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
                    "players": group,
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
                "score_df": df_to_records(score_df),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "par_list": PAR_9_DEFAULT if hole_count == 9 else PAR_18_DEFAULT,
            }
            st.session_state.current_match_id = match_id
            persist_all()

            post_to_gsheet({
                "type": "GAME",
                "game_id": match_id,
                "game_name": title.strip(),
                "match_date": str(match_date),
                "course_name": course_name,
                "hole_count": hole_count,
                "group_size": group_size,
                "organizer": organizer.strip(),
                "players": players,
                "memo": ""
            })

            match_result_text = " | ".join([
                f"{g['group_no']}조({g['start_hole']}홀): {', '.join(g['players'])}"
                for g in group_info
            ])

            post_to_gsheet({
                "type": "MATCH",
                "organizer": organizer.strip(),
                "game_name": title.strip(),
                "course_name": course_name,
                "hole_count": hole_count,
                "match_result": match_result_text,
                "memo": ""
            })

            st.success(f"경기가 생성되었습니다. 경기 ID: {match_id}")

    current_id = st.session_state.current_match_id
    if current_id and current_id in st.session_state.matches:
        st.subheader("생성된 조편성 미리보기")
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
# 12. 경기 목록
# =========================================================
elif st.session_state.menu == "MATCH_LIST":
    st.title("📋 경기 목록")
    if not st.session_state.matches:
        st.info("생성된 경기가 없습니다.")
    else:
        search = st.text_input("경기명 검색", placeholder="예: 김해")
        all_matches = list(st.session_state.matches.values())[::-1]
        if search.strip():
            all_matches = [m for m in all_matches if search.strip() in m["title"] or search.strip() in m["course_name"]]

        for match in all_matches:
            mid = match["id"]
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
# 13. SCORE
# =========================================================
elif st.session_state.menu.startswith("SCORE_"):
    match_id = st.session_state.menu.replace("SCORE_", "")
    match = st.session_state.matches.get(match_id)
    if not match:
        st.error("경기 정보를 찾을 수 없습니다.")
    else:
        st.title(f"📋 스코어 입력 - {match['title']}")
        st.caption(f"{match['match_date']} | {match['course_name']} | {match['hole_count']}홀 | 참가자 {len(match['players'])}명")

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

        score_df = records_to_df(match["score_df"])
        edited_df = st.data_editor(score_df, use_container_width=True, num_rows="fixed", key=f"editor_{match_id}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 스코어 저장", use_container_width=True):
                st.session_state.matches[match_id]["score_df"] = df_to_records(edited_df)
                persist_all()

                result_df = compute_score_result(edited_df, match["hole_count"])
                hole_cols = [f"{i}홀" for i in range(1, match["hole_count"] + 1)]

                score_rows = []
                for _, row in result_df.iterrows():
                    score_rows.append({
                        "player": row["선수명"],
                        "scores": [int(row[col]) for col in hole_cols],
                        "total": int(row["합계"]),
                        "rank": int(row["순위"])
                    })

                post_to_gsheet({
                    "type": "SCORE",
                    "game_id": match_id,
                    "game_name": match["title"],
                    "match_date": match["match_date"],
                    "course_name": match["course_name"],
                    "hole_count": match["hole_count"],
                    "score_rows": score_rows,
                    "memo": ""
                })

                st.success("스코어가 저장되었습니다.")

        with c2:
            if st.button("📊 결과 보기", use_container_width=True):
                st.session_state.matches[match_id]["score_df"] = df_to_records(edited_df)
                persist_all()

                result_df = compute_score_result(edited_df, match["hole_count"])
                hole_cols = [f"{i}홀" for i in range(1, match["hole_count"] + 1)]

                score_rows = []
                for _, row in result_df.iterrows():
                    score_rows.append({
                        "player": row["선수명"],
                        "scores": [int(row[col]) for col in hole_cols],
                        "total": int(row["합계"]),
                        "rank": int(row["순위"])
                    })

                post_to_gsheet({
                    "type": "SCORE",
                    "game_id": match_id,
                    "game_name": match["title"],
                    "match_date": match["match_date"],
                    "course_name": match["course_name"],
                    "hole_count": match["hole_count"],
                    "score_rows": score_rows,
                    "memo": "결과보기 진입 시 저장"
                })

                st.session_state.menu = f"RESULT_{match_id}"
                st.rerun()

# =========================================================
# 14. RESULT
# =========================================================
elif st.session_state.menu.startswith("RESULT_"):
    match_id = st.session_state.menu.replace("RESULT_", "")
    match = st.session_state.matches.get(match_id)
    if not match:
        st.error("결과 정보를 찾을 수 없습니다.")
    else:
        st.title(f"📊 경기 결과 - {match['title']}")
        st.caption(f"{match['match_date']} | {match['course_name']} | {match['hole_count']}홀 | 주최자: {match['organizer']}")
        score_df = records_to_df(match["score_df"])
        result_df = compute_score_result(score_df, match["hole_count"])

        top3 = result_df.head(3)
        cols = st.columns(3)
        labels = ["🥇 1위", "🥈 2위", "🥉 3위"]
        for idx, col in enumerate(cols):
            with col:
                if idx < len(top3):
                    st.markdown(
                        f"<div class='kpi-card'><h4>{labels[idx]}</h4><h2>{top3.iloc[idx]['선수명']}</h2><p>{top3.iloc[idx]['합계']}타</p></div>",
                        unsafe_allow_html=True
                    )

        st.subheader("전체 결과")
        st.dataframe(result_df, use_container_width=True, hide_index=True)

        share_text = build_share_text(match, result_df)
        st.subheader("카톡 공유용 텍스트")
        st.text_area("복사해서 사용하세요", value=share_text, height=220)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✏️ 다시 스코어 수정", use_container_width=True):
                st.session_state.menu = f"SCORE_{match_id}"
                st.rerun()
        with c2:
            if st.button("🏠 HOME", use_container_width=True):
                st.session_state.menu = "HOME"
                st.rerun()

# =========================================================
# 15. 구장 지도
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
        folium.Marker([c["lat"], c["lon"]], popup=popup_html, tooltip=c["name"]).add_to(fmap)
    st_folium(fmap, width=1200, height=500)
    st.dataframe(pd.DataFrame(filtered), use_container_width=True, hide_index=True)

# =========================================================
# 16. 유튜브
# =========================================================
elif st.session_state.menu == "YOUTUBE":
    st.title("🎥 파크골프 유튜브")
    st.caption("현재는 링크형 연결입니다. 추후 YouTube API 기반 썸네일/최신영상 자동화 가능")
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
# 17. 관리자 KPI
# =========================================================
elif st.session_state.menu == "ADMIN_KPI":
    st.title("📈 관리자 KPI 대시보드")
    kpi = get_match_kpis()
    player_stats = get_player_stats()
    course_stats = get_course_stats()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("전체 경기 수", kpi["total_matches"])
    with c2:
        st.metric("누적 참가자 수", kpi["total_players"])
    with c3:
        st.metric("스코어 저장 경기", kpi["score_saved_matches"])
    with c4:
        st.metric("누적 회원 수", len(st.session_state.users))

    st.write("")
    a, b = st.columns(2)
    with a:
        st.subheader("홀수별 경기 비중")
        hole_df = pd.DataFrame({
            "홀수": ["9홀", "18홀"],
            "경기수": [kpi["nine_hole_matches"], kpi["eighteen_hole_matches"]]
        })
        st.bar_chart(hole_df.set_index("홀수"))

    with b:
        st.subheader("인기 구장 현황")
        if course_stats.empty:
            st.caption("아직 통계가 없습니다.")
        else:
            st.dataframe(course_stats, use_container_width=True, hide_index=True)

    st.subheader("회원 현황")
    user_rows = []
    for u in st.session_state.users.values():
        user_rows.append({
            "이름": u["name"],
            "전화": u["phone"],
            "가입일": u.get("joined_at", ""),
            "최근로그인": u.get("last_login", ""),
            "로그인횟수": u.get("login_count", 0),
        })
    if user_rows:
        st.dataframe(pd.DataFrame(user_rows), use_container_width=True, hide_index=True)
    else:
        st.caption("회원 데이터가 없습니다.")

    st.subheader("선수 누적 성적 TOP 10")
    if player_stats.empty:
        st.caption("아직 스코어 데이터가 없습니다.")
    else:
        st.dataframe(player_stats.head(10), use_container_width=True, hide_index=True)

# =========================================================
# 18. 누적 랭킹
# =========================================================
elif st.session_state.menu == "RANKING":
    st.title("🏅 누적 랭킹")
    player_stats = get_player_stats()
    if player_stats.empty:
        st.info("누적 랭킹을 계산할 스코어 데이터가 없습니다.")
    else:
        sort_option = st.selectbox("정렬 기준", ["경기수", "평균타수", "최고성적"])
        ascending = True if sort_option in ["평균타수", "최고성적"] else False
        ranking_df = player_stats.sort_values(by=[sort_option], ascending=ascending).reset_index(drop=True)
        ranking_df.index = ranking_df.index + 1
        ranking_df = ranking_df.reset_index().rename(columns={"index": "랭킹"})
        st.dataframe(ranking_df, use_container_width=True, hide_index=True)

# =========================================================
# 19. fallback
# =========================================================
else:
    st.session_state.menu = "HOME"
    st.rerun()