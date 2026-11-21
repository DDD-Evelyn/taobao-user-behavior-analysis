"""
经营看板（Streamlit 版）
运行：
    cd ~/Desktop/实习项目/项目一_电商用户行为分析与经营看板
    streamlit run dashboard/app.py
然后在浏览器打开的页面里截图。
"""
from pathlib import Path

import pandas as pd
import altair as alt
import streamlit as st

DATA = Path(__file__).resolve().parent / "data"

st.set_page_config(page_title="电商用户行为经营看板", layout="wide")

# ---------------- 标题 ----------------
st.title("电商用户行为分析与经营看板")
st.caption("数据：淘宝用户行为数据集｜2017-11-25 ~ 12-03（9 天）｜5% 抽样，约 500 万条行为")

# ---------------- KPI 卡片 ----------------
kpi = pd.read_csv(DATA / "08_KPI.csv", encoding="utf-8-sig")
show = kpi[kpi["指标"].isin(["总行为数", "用户数", "购买用户数", "未购买率", "浏览→购买转化率"])]
cols = st.columns(len(show))
for col, (_, row) in zip(cols, show.iterrows()):
    col.metric(row["指标"], row["数值"], help=row["说明"])

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 每日趋势", "🔻 漏斗与路径", "🔁 留存", "👥 RFM 分层", "📊 帕累托与时段"]
)

# ---------------- 1. 趋势 ----------------
with tab1:
    daily = pd.read_csv(DATA / "01_每日趋势.csv", encoding="utf-8-sig")
    daily["日期"] = pd.to_datetime(daily["日期"])
    long = daily.melt(id_vars="日期", value_vars=["PV", "UV", "DAU"],
                      var_name="指标", value_name="数量")
    chart = (
        alt.Chart(long)
        .mark_line(point=True)
        .encode(
            x=alt.X("日期:T", title="日期"),
            y=alt.Y("数量:Q", title="数量", scale=alt.Scale(zero=False)),
            color=alt.Color("指标:N", title="指标"),
            tooltip=["日期:T", "指标:N", "数量:Q"],
        )
        .properties(height=420)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("12-02 / 12-03 两天 PV、UV、DAU 同时跳升；DAU 始终高于 UV，差额是当天只加购/收藏/购买、没浏览的用户。")

# ---------------- 2. 漏斗与路径 ----------------
with tab2:
    c1, c2 = st.columns([1, 1])
    with c1:
        f = pd.read_csv(DATA / "02_漏斗.csv", encoding="utf-8-sig")
        chart = (
            alt.Chart(f)
            .mark_bar()
            .encode(
                x=alt.X("人数:Q", title="人数"),
                y=alt.Y("层级:N", sort=["浏览", "意向(加购或收藏)", "购买"], title=""),
                color=alt.Color("层级:N", legend=None,
                                scale=alt.Scale(range=["#2c3e50", "#e67e22", "#c0392b"])),
                tooltip=["层级:N", "人数:Q", alt.Tooltip("相对第一层转化率:Q", format=".2%")],
            )
            .properties(height=360, title="三层漏斗（严格嵌套）")
        )
        st.altair_chart(chart, use_container_width=True)
    with c2:
        p = pd.read_csv(DATA / "03_购买路径.csv", encoding="utf-8-sig")
        chart = (
            alt.Chart(p)
            .mark_bar()
            .encode(
                x=alt.X("人数:Q", title="人数"),
                y=alt.Y("路径:N", sort="-x", title=""),
                color=alt.Color("路径:N", legend=None,
                                scale=alt.Scale(range=["#c0392b", "#e67e22", "#f1c40f", "#95a5a6"])),
                tooltip=["路径:N", "人数:Q", alt.Tooltip("占比:Q", format=".1%")],
            )
            .properties(height=360, title="购买路径构成（总买家 90,524）")
        )
        st.altair_chart(chart, use_container_width=True)
    st.caption("关键：标准漏斗只覆盖 34.6% 的购买者，57.0% 是浏览后直接购买。漏斗转化率 ≠ 整体购买转化率。")

# ---------------- 3. 留存 ----------------
with tab3:
    r = pd.read_csv(DATA / "04_留存.csv", encoding="utf-8-sig")
    r["首次日期"] = pd.to_datetime(r["首次日期"])
    chart = (
        alt.Chart(r)
        .mark_line(point=True)
        .encode(
            x=alt.X("首次日期:T", title="首次出现日期"),
            y=alt.Y("留存率:Q", title="留存率", axis=alt.Axis(format="%")),
            color=alt.Color("类型:N", title="口径"),
            tooltip=["首次日期:T", "类型:N", alt.Tooltip("留存率:Q", format=".1%"), "新增:Q"],
        )
        .properties(height=420)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("7 日留存只有 11-25、11-26 两批可算；两批的第 7 天恰逢 12-02/03 周末流量高峰，所以 7 日留存反而高于次日，不可与次日直接比较。")

# ---------------- 4. RFM ----------------
with tab4:
    g = pd.read_csv(DATA / "05_RFM八群.csv", encoding="utf-8-sig")
    chart = (
        alt.Chart(g)
        .mark_bar()
        .encode(
            x=alt.X("人数:Q", title="人数"),
            y=alt.Y("群:N", sort="-x", title=""),
            color=alt.Color("F层:N", title="购买频次",
                            scale=alt.Scale(domain=["F复购", "F一次性"], range=["#c0392b", "#aab7c4"])),
            tooltip=["群:N", "人数:Q", alt.Tooltip("占比:Q", format=".2%")],
        )
        .properties(height=420)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("90.2% 的买家只买过一次；真正的核心用户（R近·复购·M高）只有 4,184 人（4.62%）。")

# ---------------- 5. 帕累托 + 时段 ----------------
with tab5:
    c1, c2 = st.columns([1, 1])
    with c1:
        pareto = pd.read_csv(DATA / "06_帕累托.csv", encoding="utf-8-sig")
        # 7.9 万行太密，抽稀到每个维度约 400 点
        def thin(d, n=400):
            step = max(1, len(d) // n)
            return d.iloc[::step]
        p = pd.concat([thin(d) for _, d in pareto.groupby("维度")])
        chart = (
            alt.Chart(p)
            .mark_line()
            .encode(
                x=alt.X("单位占比:Q", title="累计单位占比", axis=alt.Axis(format="%")),
                y=alt.Y("累计购买占比:Q", title="累计购买占比", axis=alt.Axis(format="%")),
                color=alt.Color("维度:N", title="维度"),
                tooltip=["维度:N", alt.Tooltip("单位占比:Q", format=".1%"),
                         alt.Tooltip("累计购买占比:Q", format=".1%")],
            )
            .properties(height=380, title="帕累托曲线：商品 vs 品类")
        )
        st.altair_chart(chart, use_container_width=True)
        st.caption("品类需 15.8% 的单位到 80% 购买；商品需 73.2%（样本口径）。全量数据分别为 9.7% / 39.3%——行级抽样会低估集中度。")
    with c2:
        hw = pd.read_csv(DATA / "07_小时星期.csv", encoding="utf-8-sig")
        order_w = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        chart = (
            alt.Chart(hw)
            .mark_rect()
            .encode(
                x=alt.X("小时:O", title="小时"),
                y=alt.Y("星期:N", sort=order_w, title=""),
                color=alt.Color("日均:Q", title="日均行为数", scale=alt.Scale(scheme="orangered")),
                tooltip=["星期:N", "小时:O", alt.Tooltip("日均:Q", format=",.0f")],
            )
            .properties(height=380, title="小时 × 星期 活跃度热力图")
        )
        st.altair_chart(chart, use_container_width=True)
        st.caption("工作日集中在 20–22 点；周末深夜和上午相对更活跃。")

# ---------------- 口径与局限 ----------------
with st.expander("📌 口径与数据局限（面试/报告必看）"):
    st.markdown("""
- **抽样**：原始 1 亿行按 5% 行级抽样，得到 5,007,540 行；行级抽样会压低人均行为数、低估商品集中度、隐藏异常用户。
- **时间窗**：仅 9 天（2017-11-25 ~ 12-03）；"新增用户"只能定义为"数据内首次出现"，首日污染严重。
- **脏数据**：2,719 条（0.054%）时间戳越界（最早 1920、最晚 2028），数据库保留、分析时用 `WHERE date(dt) BETWEEN ...` 过滤。
- **无金额/订单号**：RFM 的 M 用总行为次数近似；F 是商品件次，不是订单数。
- **转化率口径**：9.6% 是"9 天内浏览过的用户中购买过的比例"，与行业常见的会话级转化率不可比。
""")
