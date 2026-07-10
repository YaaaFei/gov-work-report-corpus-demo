import re
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="2024–2026 政府工作报告小型语料库",
    page_icon="📚",
    layout="wide"
)

DATA_DIR_CANDIDATES = [
    Path("data"),
    Path("../output/04_cleaned_flexible_corpus"),
    Path("output/04_cleaned_flexible_corpus"),
]

def read_csv_safely(path: Path) -> pd.DataFrame:
    for enc in ["utf-8-sig", "utf-8", "gb18030"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)

def read_uploaded_csv(uploaded_file) -> pd.DataFrame:
    for enc in ["utf-8-sig", "utf-8", "gb18030"]:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding=enc)
        except UnicodeDecodeError:
            continue
    uploaded_file.seek(0)
    return pd.read_csv(uploaded_file)

def find_default_csv_files() -> list[Path]:
    patterns = ["*_auto_usable_parallel.csv", "*_cleaned_parallel.csv", "*.csv"]

    for data_dir in DATA_DIR_CANDIDATES:
        if not data_dir.exists():
            continue

        for pattern in patterns:
            files = sorted(data_dir.glob(pattern))
            if files:
                return files

    return []

@st.cache_data
def load_default_data() -> pd.DataFrame:
    files = find_default_csv_files()

    if not files:
        return pd.DataFrame()

    dfs = []

    for path in files:
        df = read_csv_safely(path)
        df["source_file"] = path.name

        if "报告年份" not in df.columns:
            match = re.search(r"(20\d{2})", path.name)
            if match:
                df["报告年份"] = match.group(1)

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)

def choose_text_columns(df: pd.DataFrame) -> list[str]:
    preferred = [
        "中文", "英文",
        "中文句子", "英文句子",
        "原始中文", "原始英文",
        "sentence", "sentence_or_group",
        "text", "source_text", "target_text",
    ]

    cols = [c for c in preferred if c in df.columns]

    if cols:
        return cols

    object_cols = [
        c for c in df.columns
        if df[c].dtype == "object" or str(df[c].dtype).startswith("string")
    ]

    return object_cols[:3]

def make_kwic(text: str, query: str, width: int = 35, use_regex: bool = False) -> str:
    text = "" if pd.isna(text) else str(text)

    if not query:
        return text[:120]

    try:
        match = re.search(query, text) if use_regex else re.search(re.escape(query), text)
    except re.error:
        return text[:120]

    if not match:
        return text[:120]

    start, end = match.span()
    left = text[max(0, start - width):start]
    keyword = text[start:end]
    right = text[end:end + width]

    return f"...{left}【{keyword}】{right}..."

st.title("2024–2026 政府工作报告小型语料库")
st.caption("教学演示版：支持年度筛选、关键词检索、简易 KWIC 上下文展示和结果下载。")

st.info(
    "说明：本页面为课程教学演示项目，语料来源于公开发布的 2024–2026 年政府工作报告文本；"
    "本页面不是官方发布平台。"
)

with st.sidebar:
    st.header("数据来源")
    uploaded_files = st.file_uploader(
        "也可以上传 CSV 文件",
        type=["csv"],
        accept_multiple_files=True
    )

if uploaded_files:
    dfs = []

    for uploaded in uploaded_files:
        df = read_uploaded_csv(uploaded)
        df["source_file"] = uploaded.name

        if "报告年份" not in df.columns:
            match = re.search(r"(20\d{2})", uploaded.name)
            if match:
                df["报告年份"] = match.group(1)

        dfs.append(df)

    corpus_df = pd.concat(dfs, ignore_index=True)
else:
    corpus_df = load_default_data()

if corpus_df.empty:
    st.warning(
        "没有找到语料 CSV。请把 04_2024_auto_usable_parallel.csv 等文件放入 data/ 文件夹，"
        "或在左侧上传 CSV。"
    )
    st.stop()

text_columns = choose_text_columns(corpus_df)

if not text_columns:
    st.error("没有识别到可检索文本列。请检查 CSV 是否包含“中文”或“英文”等文本列。")
    st.stop()

if "报告年份" in corpus_df.columns:
    corpus_df["报告年份"] = corpus_df["报告年份"].astype(str)
    year_options = sorted(corpus_df["报告年份"].dropna().unique().tolist())
else:
    year_options = []

st.subheader("语料概览")

col1, col2, col3 = st.columns(3)
col1.metric("文本行数", f"{len(corpus_df):,}")
col2.metric("可检索字段", " / ".join(text_columns))
col3.metric("年份范围", "、".join(year_options) if year_options else "未识别")

with st.expander("查看字段"):
    st.write(list(corpus_df.columns))

st.divider()

st.subheader("检索")

search_col1, search_col2, search_col3 = st.columns([2, 1.2, 1.2])

with search_col1:
    query = st.text_input("输入关键词", value="发展")

with search_col2:
    selected_text_col = st.selectbox("检索字段", text_columns, index=0)

with search_col3:
    use_regex = st.checkbox("使用正则表达式", value=False)

if year_options:
    selected_years = st.multiselect(
        "筛选年份",
        year_options,
        default=year_options
    )
else:
    selected_years = []

filtered_df = corpus_df.copy()

if selected_years and "报告年份" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["报告年份"].astype(str).isin(selected_years)]

if query:
    if use_regex:
        try:
            mask = filtered_df[selected_text_col].astype(str).str.contains(
                query,
                regex=True,
                na=False
            )
        except re.error as e:
            st.error(f"正则表达式错误：{e}")
            st.stop()
    else:
        mask = filtered_df[selected_text_col].astype(str).str.contains(
            re.escape(query),
            regex=True,
            na=False
        )

    result_df = filtered_df[mask].copy()
else:
    result_df = filtered_df.copy()

st.write(f"检索结果：{len(result_df):,} 条")

if not result_df.empty:
    result_df["KWIC"] = result_df[selected_text_col].apply(
        lambda x: make_kwic(x, query, width=35, use_regex=use_regex)
    )

    display_cols = [
        c for c in ["报告年份", "source_file", "年度文件内行号", "全局对齐序号", "段内对齐序号"]
        if c in result_df.columns
    ]

    display_cols += ["KWIC"]

    if selected_text_col not in display_cols:
        display_cols.append(selected_text_col)

    st.dataframe(
        result_df[display_cols].reset_index(drop=True),
        use_container_width=True,
        height=460
    )

    csv_bytes = result_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

    st.download_button(
        label="下载检索结果 CSV",
        data=csv_bytes,
        file_name="corpus_search_results.csv",
        mime="text/csv"
    )

st.divider()

st.subheader("按年份统计命中数")

if query and "报告年份" in result_df.columns and not result_df.empty:
    count_df = (
        result_df
        .groupby("报告年份")
        .size()
        .reset_index(name="命中数")
        .sort_values("报告年份")
    )

    st.bar_chart(count_df, x="报告年份", y="命中数")
else:
    st.info("输入关键词并检索后，可查看按年份统计的命中数。")

st.divider()

st.caption(
    "教学定位：这是面向课堂演示的小型语料库检索页面。"
    "正式大型语料库上线可考虑 CQPweb、NoSketch Engine、Sketch Engine 等系统。"
)
