import streamlit as st
import streamlit.components.v1 as components
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
from urllib.parse import quote

# =========================================================
# 1. 기본 설정
# =========================================================
st.set_page_config(
    page_title="PARKDA 파크골프 통합관제플랫폼",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. 환경 설정
# =========================================================
DEPLOY_URL = "https://script.google.com/macros/s/AKfycbyp_boO_2lakqlDT64cxFlmh_wtXcazzoXSjK2MMwUTrSryLzZWaAk7ozSz8sMGlXCG/exec"

# 관리자 지정: 본인 번호로 바꾸세요
ADMIN_PHONES = {
    "01071287551",   # 예시
    # "010xxxxxxxx"
}

# 카카오맵 JavaScript 키가 있으면 넣으세요. 없으면 자동으로 Folium 사용
KAKAO_JS_KEY = ""

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

YOUTUBE_VIDEOS = {
    "레슨영상": [
        {
            "title": "[파크골프 레슨] 초보와 고수는 티샷 시 생각부터 다릅니다!",
            "url": "https://www.youtube.com/watch?v=-Y4Ln3FtmP8"
        },
        {
            "title": "[파크골프 레슨] 정타 치고 싶으신가요? 이 동작 이젠 그만!",
            "url": "https://www.youtube.com/watch?v=nSDoAKzk2VA"
        },
        {
            "title": "[파크골프 레슨] 헤드를 던지는 순간 비거리와 정타가 달라집니다",
            "url": "https://www.youtube.com/watch?v=alt1FwmJ3DM"
        },
        {
            "title": "[파크골프 레슨] 가장 중요한 건 기본기입니다",
            "url": "https://www.youtube.com/watch?v=BVAldLrRLak"
        },
        {
            "title": "[파크골프 레슨] 9가지 실전 꿀팁 공개",
            "url": "https://www.youtube.com/watch?v=swi24qWuA7Q"
        }
    ],
    "대회영상": [
        {
            "title": "2025 제3회 문화체육관광부장관기 전국파크골프대회",
            "url": "https://www.youtube.com/watch?v=BAGR4EIBlXI"
        },
        {
            "title": "[Full] 2025 수성그린 전국 파크골프 선수권대회",
            "url": "https://www.youtube.com/watch?v=DfVqZn7GkQ4"
        },
        {
            "title": "짜릿한 승부! 전국 파크골프 대회 현장",
            "url": "https://www.youtube.com/watch?v=YXYUb7hv8L0"
        },
        {
            "title": "2026 시즌 첫 전국파크골프 대회 개막",
            "url": "https://www.youtube.com/watch?v=RCPcjPsqPRs"
        },
        {
            "title": "[Full] 2026 설특집 마실 스크린파크골프 대회",
            "url": "https://www.youtube.com/watch?v=pWPxCQbRfeQ"
        }
    ],
    "구장소개": [
        {
            "title": "장성 황룡강파크골프장 A구장 소개",
            "url": "https://www.youtube.com/watch?v=0hwSbJpFkLU"
        },
        {
            "title": "파크골프와 숙박 식사까지 가능한 구장 소개",
            "url": "https://www.youtube.com/watch?v=1Hv0Kscaq-I"
        },
        {
            "title": "영암파크골프장 소개 영상",
            "url": "https://www.youtube.com/watch?v=o-F7bNdCjWc"
        },
        {
            "title": "양평 파크골프장 구장 소개 및 라운드 후기",
            "url": "https://www.youtube.com/watch?v=qKZCCoRZlF0"
        },
        {
            "title": "진주 평거 파크골프장 구장 소개 및 라운드 영상",
            "url": "https://www.youtube.com/watch?v=2xvfq7thi2k"
        }
    ]
}

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
        "history": [],
        "matches": load_json(MATCHES_FILE, {}),
        "users": load_json(USERS_FILE, {}),
        "current_match_id": None,
        "api_logs": [],
        "score_ui": {}
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
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

[data-testid="stSidebar"] {
    border-right: 1px solid #e5e7eb;
}

.title-main {
    font-size: 2.1rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.2;
}

.sub-main {
    color: #475569;
    font-size: 1rem;
    margin-top: 0.3rem;
}

.kpi-card {
    padding: 18px;
    border-radius: 18px;
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
    min-height: 120px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.12);
}

.feature-card {
    padding: 18px;
    border-radius: 18px;
    background: white;
    border: 1px solid #e2e8f0;
    box-shadow: 0 8px 24px rgba(15,23,42,0.06);
    height: 100%;
}

.feature-card h4 {
    color: #0f172a;
    margin-bottom: 8px;
}

.feature-card p {
    color: #475569;
    font-size: 0.95rem;
    min-height: 64px;
}

.match-card {
    padding: 16px;
    border-radius: 16px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 14px rgba(15,23,42,0.05);
    margin-bottom: 12px;
    color: #0f172a !important;
}

.match-card b,
.match-card div,
.match-card span,
.match-card p {
    color: #0f172a !important;
}

.section-card {
    padding: 18px;
    border-radius: 18px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 14px rgba(15,23,42,0.05);
}

.small-muted {
    color: #64748b;
    font-size: 13px;
}

.yt-card {
    padding: 12px;
    border-radius: 16px;
    background: #fff;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 14px rgba(15,23,42,0.05);
    margin-bottom: 12px;
    color: #0f172a;
}

.yt-title {
    font-size: 14px;
    font-weight: 700;
    color: #0f172a;
    min-height: 40px;
    margin-top: 8px;
}

.copy-box {
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    background: #fff;
    padding: 12px;
}

.topnav-wrap {
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:12px;
    flex-wrap: wrap;
    margin-bottom: 14px;
}

.score-hole-card {
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 10px;
    background: #fff;
    text-align: center;
}

.score-value {
    font-size: 1.3rem;
    font-weight: 800;
    color: #0f172a;
}

.par-badge {
    display:inline-block;
    padding: 4px 8px;
    border-radius: 999px;
    background: #ecfeff;
    color: #155e75;
    font-size: 12px;
    font-weight: 700;
}

.notice-box {
    padding: 14px;
    border-radius: 14px;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1e3a8a;
}

.admin-badge {
    display:inline-block;
    padding:4px 10px;
    border-radius:999px;
    background:#dcfce7;
    color:#166534;
    font-size:12px;
    font-weight:700;
}

@media (max-width: 768px) {
    .title-main {
        font-size: 1.6rem;
    }
    .feature-card p {
        min-height: unset;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 7. 공용 유틸
# =========================================================
def persist_all():
    save_json(MATCHES_FILE, st.session_state.matches)
    save_json(USERS_FILE, st.session_state.users)


def is_admin():
    return st.session_state.phone in ADMIN_PHONES


def add_api_log(action, status, detail):
    st.session_state.api_logs.insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "status": status,
        "detail": detail[:500] if isinstance(detail, str) else str(detail)[:500]
    })
    st.session_state.api_logs = st.session_state.api_logs[:20]


def post_to_gsheet(payload: dict):
    try:
        res = requests.post(
            DEPLOY_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=15
        )
        add_api_log(payload.get("type", "UNKNOWN"), f"HTTP {res.status_code}", res.text)
        return res.status_code, res.text
    except Exception as e:
        add_api_log(payload.get("type", "UNKNOWN"), "ERROR", str(e))
        return None, str(e)


def go(page: str):
    current = st.session_state.menu
    if current != page:
        st.session_state.history.append(current)
        st.session_state.menu = page


def go_back():
    if st.session_state.history:
        st.session_state.menu = st.session_state.history.pop()
    else:
        st.session_state.menu = "HOME"


def render_topbar(title: str, subtitle: str = ""):
    left, right = st.columns([5, 2])
    with left:
        st.markdown(f"<div class='title-main'>{title}</div>", unsafe_allow_html=True)
        if subtitle:
            st.markdown(f"<div class='sub-main'>{subtitle}</div>", unsafe_allow_html=True)
    with right:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅ 이전", use_container_width=True, key=f"back_{title}"):
                go_back()
                st.rerun()
        with c2:
            if st.button("🏠 홈", use_container_width=True, key=f"home_{title}"):
                st.session_state.menu = "HOME"
                st.rerun()


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


def build_par_score_df(players: list, par_list: list) -> pd.DataFrame:
    hole_labels = [f"{i}홀" for i in range(1, len(par_list) + 1)]
    rows = []
    for player in players:
        row = {"선수명": player}
        for idx, h in enumerate(hole_labels):
            row[h] = par_list[idx]
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


def build_group_share_text(match: dict) -> str:
    lines = [
        "⛳ [PARKDA 조편성 결과]",
        f"경기명: {match['title']}",
        f"일시: {match['match_date']}",
        f"구장: {match['course_name']}",
        f"홀수: {match['hole_count']}홀",
        ""
    ]
    for g in match["groups"]:
        lines.append(f"{g['group_no']}조 ({g['start_hole']}홀 출발): {', '.join(g['players'])}")
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


def get_player_stats(course_filter=None):
    all_rows = []
    for match in st.session_state.matches.values():
        if course_filter and match["course_name"] != course_filter:
            continue
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
        return pd.DataFrame(columns=["선수명", "구장", "경기수", "평균타수", "최고성적", "최근경기"])

    base = pd.DataFrame(all_rows)
    grouped = base.groupby(["선수명", "구장"], as_index=False).agg(
        경기수=("합계", "count"),
        평균타수=("합계", "mean"),
        최고성적=("순위", "min")
    )
    grouped["평균타수"] = grouped["평균타수"].round(1)
    recent = base.sort_values(by=["일자"], ascending=False).drop_duplicates(subset=["선수명", "구장"])
    grouped = grouped.merge(recent[["선수명", "구장", "경기명"]], on=["선수명", "구장"], how="left")
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


def get_video_id(url: str):
    m = re.search(r"v=([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def youtube_thumbnail(url: str):
    vid = get_video_id(url)
    if not vid:
        return None
    return f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"


def copy_widget(text: str, key: str, height=180):
    escaped = json.dumps(text, ensure_ascii=False)
    html = f"""
    <div style="margin-top:6px;">
      <textarea id="copy_area_{key}" style="width:100%;height:{height}px;border:1px solid #d1d5db;border-radius:12px;padding:10px;font-size:14px;">{text}</textarea>
      <button onclick='navigator.clipboard.writeText({escaped});this.innerText="복사완료";'
        style="margin-top:8px;padding:10px 14px;border:none;border-radius:10px;background:#0f172a;color:white;cursor:pointer;font-weight:700;">
        전체복사
      </button>
    </div>
    """
    components.html(html, height=height + 70)


def render_feature_teaser():
    st.markdown("<div class='title-main'>⛳ PARKDA 파크골프 통합관제플랫폼</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-main'>로그인하면 경기 생성, 조편성, 스코어 기록, 구장 지도, 유튜브 학습, 구장별 누적 랭킹까지 바로 사용할 수 있습니다.</div>",
        unsafe_allow_html=True
    )
    st.write("")

    cols = st.columns(3)
    features = [
        ("📝 경기 생성", "참가자만 넣으면 9홀/18홀 경기 생성과 자동 조편성을 바로 만들 수 있습니다."),
        ("👥 조편성 공유", "생성된 조편성을 전체복사해서 카카오톡, 밴드, 단체방에 바로 전파할 수 있습니다."),
        ("📋 스코어 기록", "PAR 기준 + / - 방식으로 1홀부터 9홀까지 빠르게 입력할 수 있습니다."),
        ("🏅 구장별 랭킹", "구장마다 기준이 다르기 때문에 구장별로 누적 랭킹을 확인할 수 있습니다."),
        ("📍 전국 구장 지도", "구장 위치, 연락처, 이용료를 확인하고 카카오맵 또는 지도 기반으로 탐색할 수 있습니다."),
        ("🎥 유튜브 학습", "레슨영상, 대회영상, 구장소개를 카테고리별로 보고 바로 들어갈 수 있습니다.")
    ]
    for i, (title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class='feature-card'>
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button(f"{title} 사용하기", key=f"teaser_{i}", use_container_width=True):
                st.warning("로그인 후 사용할 수 있습니다. 왼쪽 사이드바에서 로그인해주세요.")

    st.write("")
    st.markdown(
        "<div class='notice-box'>로그인 전에는 기능 소개만 볼 수 있고, 실제 저장·조편성·스코어 입력은 로그인 후 가능합니다.</div>",
        unsafe_allow_html=True
    )


def render_map(courses):
    if KAKAO_JS_KEY:
        markers = json.dumps(courses, ensure_ascii=False)
        html = f"""
        <div id="map" style="width:100%;height:520px;border-radius:16px;"></div>
        <script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}"></script>
        <script>
          const data = {markers};
          const center = new kakao.maps.LatLng(data[0]?.lat || 36.5, data[0]?.lon || 127.8);
          const mapContainer = document.getElementById('map');
          const mapOption = {{ center: center, level: 8 }};
          const map = new kakao.maps.Map(mapContainer, mapOption);

          data.forEach(function(item) {{
            const position = new kakao.maps.LatLng(item.lat, item.lon);
            const marker = new kakao.maps.Marker({{ position: position }});
            marker.setMap(map);

            const infowindow = new kakao.maps.InfoWindow({{
              content: `
                <div style="padding:10px;min-width:220px;font-size:13px;line-height:1.5;">
                  <b>${{item.name}}</b><br/>
                  지역: ${{item.region}}<br/>
                  주소: ${{item.address}}<br/>
                  홀수: ${{item.holes}}홀<br/>
                  이용료: ${{item.fee}}<br/>
                  전화: ${{item.phone}}
                </div>
              `
            }});

            kakao.maps.event.addListener(marker, 'click', function() {{
              infowindow.open(map, marker);
            }});
          }});
        </script>
        """
        components.html(html, height=540)
    else:
        if courses:
            center_lat = sum(c["lat"] for c in courses) / len(courses)
            center_lon = sum(c["lon"] for c in courses) / len(courses)
        else:
            center_lat, center_lon = 36.5, 127.8

        fmap = folium.Map(location=[center_lat, center_lon], zoom_start=7)
        for c in courses:
            popup_html = f"""
            <b>{c['name']}</b><br>
            지역: {c['region']}<br>
            주소: {c['address']}<br>
            홀수: {c['holes']}홀<br>
            이용료: {c['fee']}<br>
            전화: {c['phone']}
            """
            folium.Marker([c["lat"], c["lon"]], popup=popup_html, tooltip=c["name"]).add_to(fmap)
        st_folium(fmap, width="100%", height=520)

        st.info("카카오맵 JavaScript 키가 없어 현재는 기본 지도로 표시됩니다. 키를 넣으면 카카오맵으로 바꿀 수 있습니다.")


def ensure_score_ui(match_id, match):
    ui_key = f"score_{match_id}"
    if ui_key not in st.session_state.score_ui:
        score_df = records_to_df(match["score_df"])
        if score_df.empty:
            score_df = build_par_score_df(match["players"], match["par_list"])
        score_map = {}
        for _, row in score_df.iterrows():
            player = row["선수명"]
            score_map[player] = {}
            for i in range(1, match["hole_count"] + 1):
                score_map[player][f"{i}홀"] = int(row[f"{i}홀"])
        st.session_state.score_ui[ui_key] = score_map
    return st.session_state.score_ui[ui_key]


def score_ui_to_df(match_id, match):
    ui_key = f"score_{match_id}"
    score_map = st.session_state.score_ui.get(ui_key, {})
    rows = []
    for player in match["players"]:
        row = {"선수명": player}
        for i in range(1, match["hole_count"] + 1):
            row[f"{i}홀"] = int(score_map.get(player, {}).get(f"{i}홀", match["par_list"][i-1]))
        rows.append(row)
    return pd.DataFrame(rows)

# =========================================================
# 8. 사이드바
# =========================================================
with st.sidebar:
    st.markdown("## ⛳ PARKDA")
    st.caption("파크골프 통합관제플랫폼")

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
        badge = "<span class='admin-badge'>관리자</span>" if is_admin() else ""
        st.markdown(f"**{st.session_state.user_name}님** {badge}", unsafe_allow_html=True)
        st.caption(f"연락처: {st.session_state.phone}")

        if st.button("로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_name = ""
            st.session_state.phone = ""
            st.session_state.menu = "HOME"
            st.session_state.history = []
            st.rerun()

        st.divider()
        if st.button("🏠 HOME", use_container_width=True):
            st.session_state.menu = "HOME"
            st.rerun()
        if st.button("📝 경기 생성", use_container_width=True):
            go("CREATE_MATCH")
            st.rerun()
        if st.button("📋 경기 목록", use_container_width=True):
            go("MATCH_LIST")
            st.rerun()
        if st.button("📍 전국 구장 지도", use_container_width=True):
            go("COURSE_MAP")
            st.rerun()
        if st.button("🎥 유튜브", use_container_width=True):
            go("YOUTUBE")
            st.rerun()
        if st.button("🏅 구장별 랭킹", use_container_width=True):
            go("RANKING")
            st.rerun()

        if is_admin():
            if st.button("📈 관리자 KPI", use_container_width=True):
                go("ADMIN_KPI")
                st.rerun()

        st.divider()
        st.markdown("### 시트 연동 상태")
        if st.session_state.api_logs:
            latest = st.session_state.api_logs[0]
            st.write(f"최근 요청: `{latest['action']}`")
            st.write(f"상태: `{latest['status']}`")
        else:
            st.caption("아직 시트 전송 기록이 없습니다.")

        with st.expander("최근 전송 로그 보기"):
            if st.session_state.api_logs:
                for log in st.session_state.api_logs:
                    st.write(f"[{log['time']}] {log['action']} / {log['status']}")
                    st.caption(log["detail"])
            else:
                st.caption("기록 없음")

# =========================================================
# 9. 로그인 전 첫 화면
# =========================================================
if not st.session_state.logged_in:
    render_feature_teaser()
    st.stop()

# =========================================================
# 10. HOME
# =========================================================
if st.session_state.menu == "HOME":
    render_topbar("⛳ PARKDA 통합관제 대시보드", "경기 운영 · 조편성 · 스코어 · 지도 · 유튜브 · 구장별 랭킹")
    kpi = get_match_kpis()

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
    quick_cols = st.columns(4)
    with quick_cols[0]:
        if st.button("📝 경기 생성", use_container_width=True):
            go("CREATE_MATCH")
            st.rerun()
    with quick_cols[1]:
        if st.button("📋 경기 목록", use_container_width=True):
            go("MATCH_LIST")
            st.rerun()
    with quick_cols[2]:
        if st.button("📍 전국 구장 지도", use_container_width=True):
            go("COURSE_MAP")
            st.rerun()
    with quick_cols[3]:
        if st.button("🏅 구장별 랭킹", use_container_width=True):
            go("RANKING")
            st.rerun()

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
        st.subheader("바로 할 수 있는 기능")
        st.markdown("""
        <div class='section-card'>
            <p>• 경기 생성 후 자동 조편성</p>
            <p>• 조편성 전체복사 후 카톡/밴드 공유</p>
            <p>• PAR 기준 + / - 스코어 입력</p>
            <p>• 구장별 누적 랭킹 조회</p>
            <p>• 카테고리별 유튜브 학습</p>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# 11. 경기 생성
# =========================================================
elif st.session_state.menu == "CREATE_MATCH":
    render_topbar("📝 경기 생성", "경기 생성이 완료되면 조편성 결과를 바로 전체복사할 수 있습니다.")

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
            st.error("참가자는 최소 2명 이상 입력해주세요.")
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
            score_df = build_par_score_df(players, PAR_9_DEFAULT if hole_count == 9 else PAR_18_DEFAULT)

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

            # score_ui도 초기화
            ui_key = f"score_{match_id}"
            st.session_state.score_ui[ui_key] = {
                player: {f"{i}홀": (PAR_9_DEFAULT if hole_count == 9 else PAR_18_DEFAULT)[i-1] for i in range(1, hole_count+1)}
                for player in players
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
        match = st.session_state.matches[current_id]
        st.subheader("생성된 조편성")
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

        share_text = build_group_share_text(match)
        st.subheader("조편성 전체복사")
        copy_widget(share_text, key=f"group_copy_{current_id}", height=200)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📋 경기목록으로", use_container_width=True):
                go("MATCH_LIST")
                st.rerun()
        with c2:
            if st.button("📝 이 경기 스코어 입력", use_container_width=True):
                go(f"SCORE_{current_id}")
                st.rerun()

# =========================================================
# 12. 경기 목록
# =========================================================
elif st.session_state.menu == "MATCH_LIST":
    render_topbar("📋 경기 목록", "경기 검색, 스코어 입력, 결과 확인, 조편성 공유")
    if not st.session_state.matches:
        st.info("생성된 경기가 없습니다.")
    else:
        search = st.text_input("경기명/구장명 검색", placeholder="예: 김해")
        all_matches = list(st.session_state.matches.values())[::-1]
        if search.strip():
            all_matches = [m for m in all_matches if search.strip() in m["title"] or search.strip() in m["course_name"]]

        for match in all_matches:
            mid = match["id"]
            st.markdown(
                f"""
                <div class='match-card'>
                    <b>{match['title']}</b><br>
                    경기일: {match['match_date']} / 구장: {match['course_name']} / 홀수: {match['hole_count']}홀 / 참가자: {len(match['players'])}명
                </div>
                """,
                unsafe_allow_html=True
            )
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button(f"✏ 스코어 입력", key=f"score_{mid}", use_container_width=True):
                    st.session_state.current_match_id = mid
                    go(f"SCORE_{mid}")
                    st.rerun()
            with c2:
                if st.button(f"📊 결과 보기", key=f"result_{mid}", use_container_width=True):
                    st.session_state.current_match_id = mid
                    go(f"RESULT_{mid}")
                    st.rerun()
            with c3:
                if st.button(f"📋 조편성 복사", key=f"copy_{mid}", use_container_width=True):
                    st.session_state.current_match_id = mid
                    st.session_state.menu = f"COPY_{mid}"
                    st.rerun()

# =========================================================
# 13. 조편성 복사 전용
# =========================================================
elif st.session_state.menu.startswith("COPY_"):
    match_id = st.session_state.menu.replace("COPY_", "")
    match = st.session_state.matches.get(match_id)
    if not match:
        st.error("경기 정보를 찾을 수 없습니다.")
    else:
        render_topbar("📋 조편성 공유", f"{match['title']} / {match['course_name']}")
        share_text = build_group_share_text(match)
        copy_widget(share_text, key=f"group_copy_page_{match_id}", height=220)

# =========================================================
# 14. SCORE
# =========================================================
elif st.session_state.menu.startswith("SCORE_"):
    match_id = st.session_state.menu.replace("SCORE_", "")
    match = st.session_state.matches.get(match_id)
    if not match:
        st.error("경기 정보를 찾을 수 없습니다.")
    else:
        render_topbar(
            f"📋 스코어 입력 - {match['title']}",
            f"{match['match_date']} | {match['course_name']} | {match['hole_count']}홀 | 참가자 {len(match['players'])}명"
        )

        score_map = ensure_score_ui(match_id, match)
        player_tabs = st.tabs(match["players"])

        for idx, player in enumerate(match["players"]):
            with player_tabs[idx]:
                st.markdown(f"### {player}")
                hole_cols = st.columns(3 if match["hole_count"] == 9 else 4)
                for i in range(1, match["hole_count"] + 1):
                    col = hole_cols[(i - 1) % len(hole_cols)]
                    with col:
                        hole_key = f"{i}홀"
                        current_score = int(score_map[player][hole_key])
                        par_value = match["par_list"][i - 1]

                        st.markdown(
                            f"""
                            <div class='score-hole-card'>
                                <div><b>{i}홀</b></div>
                                <div class='par-badge'>PAR {par_value}</div>
                                <div class='score-value'>{current_score}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        m1, m2 = st.columns(2)
                        with m1:
                            if st.button("－", key=f"minus_{match_id}_{player}_{i}", use_container_width=True):
                                score_map[player][hole_key] = max(1, current_score - 1)
                                st.rerun()
                        with m2:
                            if st.button("＋", key=f"plus_{match_id}_{player}_{i}", use_container_width=True):
                                score_map[player][hole_key] = current_score + 1
                                st.rerun()

        st.write("")
        preview_df = score_ui_to_df(match_id, match)
        result_preview = compute_score_result(preview_df, match["hole_count"])
        st.subheader("현재 점수 미리보기")
        st.dataframe(result_preview, use_container_width=True, hide_index=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 스코어 저장", use_container_width=True):
                final_df = score_ui_to_df(match_id, match)
                st.session_state.matches[match_id]["score_df"] = df_to_records(final_df)
                persist_all()

                result_df = compute_score_result(final_df, match["hole_count"])
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
            if st.button("📊 저장 후 결과 보기", use_container_width=True):
                final_df = score_ui_to_df(match_id, match)
                st.session_state.matches[match_id]["score_df"] = df_to_records(final_df)
                persist_all()

                result_df = compute_score_result(final_df, match["hole_count"])
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

                go(f"RESULT_{match_id}")
                st.rerun()

# =========================================================
# 15. RESULT
# =========================================================
elif st.session_state.menu.startswith("RESULT_"):
    match_id = st.session_state.menu.replace("RESULT_", "")
    match = st.session_state.matches.get(match_id)
    if not match:
        st.error("결과 정보를 찾을 수 없습니다.")
    else:
        render_topbar(
            f"📊 경기 결과 - {match['title']}",
            f"{match['match_date']} | {match['course_name']} | {match['hole_count']}홀 | 주최자: {match['organizer']}"
        )

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
        st.subheader("결과 공유")
        copy_widget(share_text, key=f"result_copy_{match_id}", height=220)

# =========================================================
# 16. 구장 지도
# =========================================================
elif st.session_state.menu == "COURSE_MAP":
    render_topbar("📍 전국 구장 지도", "지역별 구장 탐색 / 카카오맵 가능 시 카카오맵 우선")
    region_filter = st.selectbox("지역 선택", ["전체"] + sorted(list(set(c["region"] for c in COURSES))))
    filtered = COURSES if region_filter == "전체" else [c for c in COURSES if c["region"] == region_filter]
    render_map(filtered)
    st.dataframe(pd.DataFrame(filtered), use_container_width=True, hide_index=True)

# =========================================================
# 17. 유튜브
# =========================================================
elif st.session_state.menu == "YOUTUBE":
    render_topbar("🎥 파크골프 유튜브", "레슨영상 / 대회영상 / 구장소개를 카테고리별로 확인")
    categories = list(YOUTUBE_VIDEOS.keys())
    cat = st.radio("카테고리 선택", categories, horizontal=True)

    videos = YOUTUBE_VIDEOS.get(cat, [])
    cols = st.columns(2)
    for i, item in enumerate(videos):
        with cols[i % 2]:
            thumb = youtube_thumbnail(item["url"])
            st.markdown("<div class='yt-card'>", unsafe_allow_html=True)
            if thumb:
                st.image(thumb, use_container_width=True)
            st.markdown(f"<div class='yt-title'>{item['title']}</div>", unsafe_allow_html=True)
            st.link_button("영상 보러가기", item["url"], use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 18. 관리자 KPI
# =========================================================
elif st.session_state.menu == "ADMIN_KPI":
    if not is_admin():
        st.error("관리자만 접근할 수 있습니다.")
        if st.button("홈으로"):
            st.session_state.menu = "HOME"
            st.rerun()
    else:
        render_topbar("📈 관리자 KPI 대시보드", "관리자는 전화번호 기준으로 지정됩니다. 주최자와 관리자는 별개입니다.")
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

        st.subheader("시트 연동 로그")
        if st.session_state.api_logs:
            st.dataframe(pd.DataFrame(st.session_state.api_logs), use_container_width=True, hide_index=True)
        else:
            st.caption("아직 시트 전송 로그가 없습니다.")

        st.subheader("누적 성적 TOP 10")
        if player_stats.empty:
            st.caption("아직 스코어 데이터가 없습니다.")
        else:
            st.dataframe(player_stats.head(10), use_container_width=True, hide_index=True)

# =========================================================
# 19. 구장별 누적 랭킹
# =========================================================
elif st.session_state.menu == "RANKING":
    render_topbar("🏅 구장별 누적 랭킹", "전체가 아니라 구장별 기준으로 랭킹을 봅니다.")
    course_names = sorted(list(set([m["course_name"] for m in st.session_state.matches.values()])))
    if not course_names:
        st.info("랭킹을 계산할 경기 데이터가 없습니다.")
    else:
        selected_course = st.selectbox("구장 선택", course_names)
        player_stats = get_player_stats(course_filter=selected_course)

        if player_stats.empty:
            st.info("선택한 구장의 스코어 데이터가 없습니다.")
        else:
            sort_option = st.selectbox("정렬 기준", ["경기수", "평균타수", "최고성적"])
            ascending = True if sort_option in ["평균타수", "최고성적"] else False
            ranking_df = player_stats[player_stats["구장"] == selected_course].sort_values(
                by=[sort_option],
                ascending=ascending
            ).reset_index(drop=True)
            ranking_df.index = ranking_df.index + 1
            ranking_df = ranking_df.reset_index().rename(columns={"index": "랭킹"})
            st.dataframe(ranking_df, use_container_width=True, hide_index=True)

            share_lines = [f"🏅 [{selected_course}] 누적 랭킹"]
            for _, row in ranking_df.head(10).iterrows():
                share_lines.append(
                    f"{row['랭킹']}위 {row['선수명']} / 경기 {row['경기수']}회 / 평균 {row['평균타수']}타 / 최고성적 {row['최고성적']}위"
                )
            copy_widget("\n".join(share_lines), key=f"rank_copy_{selected_course}", height=220)

# =========================================================
# 20. fallback
# =========================================================
else:
    st.session_state.menu = "HOME"
    st.rerun()