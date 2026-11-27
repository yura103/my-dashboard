import streamlit as st  # 웹 화면을 만드는 라이브러리
import pandas as pd  # 표 형태 데이터를 다루는 라이브러리

# 페이지 기본 설정: 화면을 넓게 쓰기 (반드시 맨 처음에 호출)
st.set_page_config(page_title="매출 현황", layout="wide")


DATA_FILE = "sales_sample.csv"  # 읽어 올 데이터 파일 이름
REQUIRED_COLUMNS = ["date", "region", "category", "sales", "quantity"]  # 꼭 있어야 하는 열


# 데이터 불러오기 함수
# @st.cache_data: 처음 한 번만 파일을 읽고, 그 뒤에는 저장해 둔 결과를 재사용
# (읽다가 오류가 나면 저장하지 않으므로, 파일을 고친 뒤 새로고침하면 다시 읽음)
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    return df


# 제목과 캡션 (문제가 생겨도 제목은 보이도록 데이터 확인보다 먼저 그림)
st.title("영업팀 매출 현황")
st.caption("데이터 기준: 2026년 1~10월")

# ---------------- 데이터 읽기 + 문제 확인 ----------------
# try ~ except: 오류가 나도 화면이 깨지지 않게 '잡아서' 안내 문구로 바꿔 보여주기
try:
    df = load_data().copy()  # .copy(): 캐시에 저장된 원본은 건드리지 않고 복사본으로 작업
except FileNotFoundError:  # 1) 파일이 없을 때
    st.warning(
        f"데이터 파일 '{DATA_FILE}'을(를) 찾을 수 없습니다. "
        f"app.py와 같은 폴더에 파일이 있는지, 파일 이름이 정확한지 확인한 뒤 "
        f"그 폴더에서 streamlit run app.py로 다시 실행해 주세요."
    )
    st.stop()  # 여기서 실행 멈춤
except Exception:  # 파일은 있지만 비어 있거나 형식이 깨져서 못 읽을 때
    st.warning(
        f"데이터 파일 '{DATA_FILE}'을(를) 읽지 못했습니다. "
        f"파일이 비어 있지 않은지, UTF-8 형식의 CSV로 저장되어 있는지 확인해 주세요."
    )
    st.stop()

# 2) 필요한 열이 모두 있는지 확인
missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]  # 없는 열만 모으기
if missing:  # 없는 열이 하나라도 있으면
    st.warning(
        f"데이터 파일에 꼭 필요한 열이 없습니다: {', '.join(missing)}. "
        f"CSV 파일 첫 줄의 열 이름을 확인하고 위 열을 추가하거나 이름을 고쳐 주세요."
    )
    st.stop()

# 값 형식 맞추기: 잘못된 값은 오류 대신 빈 값(NaN)으로 바꿈 (errors="coerce")
df["date"] = pd.to_datetime(df["date"], errors="coerce")  # date 열을 날짜 형식으로
df["sales"] = pd.to_numeric(df["sales"], errors="coerce")  # sales 열을 숫자로
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")  # quantity 열을 숫자로

# 빈 값이 있는 행은 계산에 쓸 수 없으므로 빼기
row_count_before = len(df)
df = df.dropna(subset=REQUIRED_COLUMNS)
dropped = row_count_before - len(df)  # 빠진 행 개수
df["region"] = df["region"].astype(str)  # 지역·카테고리는 글자로 통일
df["category"] = df["category"].astype(str)

if df.empty:  # 쓸 수 있는 행이 하나도 남지 않았을 때
    st.warning(
        "데이터 파일에 올바른 값이 들어 있는 행이 없습니다. "
        "date는 2026-01-01 같은 날짜, sales와 quantity는 숫자로 들어 있는지 확인해 주세요."
    )
    st.stop()

if dropped > 0:  # 일부 행만 빠졌다면 작게 알려 주기
    st.caption(f"값이 비어 있거나 잘못된 {dropped:,}행은 제외했습니다. 원본 파일의 해당 행을 확인해 주세요.")

# ---------------- 왼쪽 사이드바: 조건(필터) ----------------
st.sidebar.header("조건 선택")

# 1) 지역: 여러 개 선택 가능, 처음에는 모든 지역이 선택된 상태
region_list = sorted(df["region"].unique())  # 데이터에 있는 지역 이름을 겹치지 않게 뽑아 가나다순 정렬
selected_regions = st.sidebar.multiselect("지역", region_list, default=region_list)

# 2) 카테고리: 드롭다운에서 하나 선택, 맨 앞에 '전체' 추가
category_list = ["전체"] + sorted(df["category"].unique())
selected_category = st.sidebar.selectbox("카테고리", category_list)

# 3) 기간: 슬라이더로 시작일~종료일 선택 (처음에는 데이터 전체 기간)
min_date = df["date"].min().date()  # 가장 이른 날짜 (.date(): 시간 빼고 날짜만)
max_date = df["date"].max().date()  # 가장 늦은 날짜
if min_date < max_date:
    start_date, end_date = st.sidebar.slider(
        "기간",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),  # 값 2개를 주면 '범위' 슬라이더가 됨
        format="YYYY-MM-DD",
    )
else:  # 데이터가 하루치뿐이면 슬라이더를 만들 수 없으므로(시작=끝이면 오류) 날짜만 보여주기
    start_date, end_date = min_date, max_date
    st.sidebar.write(f"기간: {min_date} (하루치 데이터)")

# ---------------- 조건으로 데이터 걸러내기 → filtered ----------------
filtered = df[df["region"].isin(selected_regions)]  # 선택한 지역에 해당하는 행만 남기기
if selected_category != "전체":  # '전체'가 아닐 때만 카테고리로 거르기
    filtered = filtered[filtered["category"] == selected_category]
filtered = filtered[
    (filtered["date"].dt.date >= start_date) & (filtered["date"].dt.date <= end_date)
]  # 시작일 이상 '그리고(&)' 종료일 이하인 행만 남기기

# 필터 아래에 걸러진 건수 표시
st.sidebar.write(f"선택 조건: {len(filtered):,}건 / 전체 {len(df):,}건")

# 3) 조건에 맞는 데이터가 하나도 없으면 안내만 하고 지표·그래프·표는 그리지 않음
if filtered.empty:
    st.info(
        "선택한 조건에 맞는 데이터가 없습니다. "
        "사이드바에서 지역을 더 선택하거나, 카테고리를 '전체'로 바꾸거나, 기간을 늘려 조건을 넓혀 보세요."
    )
    st.stop()  # 여기서 실행 멈춤

# ---------------- 본문 탭 ----------------
tab_summary, tab_detail = st.tabs(["요약", "상세 데이터"])

with tab_summary:
    # 핵심 숫자 3개 계산 (걸러진 데이터 filtered 기준)
    total_sales = filtered["sales"].sum()  # 총 매출: sales 열을 모두 더함
    order_count = len(filtered)  # 주문 건수: 데이터 행(줄) 개수
    avg_order = total_sales / order_count  # 평균 주문액: 총 매출 ÷ 주문 건수

    # 화면을 가로로 3칸 나누기
    col1, col2, col3 = st.columns(3)

    # 각 칸에 숫자 카드(metric) 넣기
    # f"{값:,.0f}원": 천 단위 쉼표(,) + 소수점 없이(.0f) + 뒤에 '원'
    col1.metric("총 매출", f"{total_sales:,.0f}원")
    col2.metric("주문 건수", f"{order_count:,}건")
    col3.metric("평균 주문액", f"{avg_order:,.0f}원")

    # 그래프 2개를 가로로 나란히 놓기
    chart_left, chart_right = st.columns(2)

    with chart_left:
        st.subheader("월별 매출 추이")
        # 날짜를 '2026-01' 같은 월 글자로 바꾼 뒤, 월마다 매출 합계 구하기
        monthly = filtered.groupby(filtered["date"].dt.strftime("%Y-%m"))["sales"].sum().reset_index()
        monthly.columns = ["월", "매출"]  # 그래프 축 이름이 한글로 보이도록 열 이름 변경
        st.line_chart(monthly, x="월", y="매출")  # 선 그래프

    with chart_right:
        st.subheader("지역별 매출")
        # 지역마다 매출 합계 구하기
        by_region = filtered.groupby("region")["sales"].sum().reset_index()
        by_region.columns = ["지역", "매출"]
        # sort="-매출": 매출이 큰 순서(내림차순)로 막대 정렬 (- 는 큰 것부터라는 뜻)
        st.bar_chart(by_region, x="지역", y="매출", sort="-매출")  # 막대 그래프

with tab_detail:
    # 걸러진 데이터를 표로 보여주기
    # width="stretch": 표를 화면 폭에 꽉 맞춤
    # hide_index=True: 맨 왼쪽 행 번호(0, 1, 2...) 숨기기
    # column_config: 열마다 보여주는 방식 정하기
    # date 열은 날짜 형식으로, 'YYYY-MM-DD'(예: 2026-01-01) 모양으로만 표시 → 시간 부분 숨김
    st.dataframe(
        filtered,
        width="stretch",
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("date", format="YYYY-MM-DD"),
        },
    )
