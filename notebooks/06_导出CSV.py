"""
06_导出CSV.py —— 把分析结果导出成 Tableau 能直接用的 CSV
运行： python notebooks/06_导出CSV.py
输出： dashboard/data/*.csv
"""
from pathlib import Path
import sqlite3

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "taobao.db"
OUT = ROOT / "dashboard" / "data"
OUT.mkdir(parents=True, exist_ok=True)
W = "date(dt) BETWEEN '2017-11-25' AND '2017-12-03'"

con = sqlite3.connect(DB)


def save(df: pd.DataFrame, name: str):
    df.to_csv(OUT / name, index=False, encoding="utf-8-sig")
    print(f"  {name:<26} {len(df):>10,} 行")


# ============ 1. 每日 PV / UV / DAU ============
daily = pd.read_sql(f"""
SELECT date(dt) AS 日期,
       SUM(CASE WHEN behavior='pv' THEN 1 ELSE 0 END)            AS PV,
       COUNT(DISTINCT CASE WHEN behavior='pv' THEN user_id END)  AS UV,
       COUNT(DISTINCT user_id)                                   AS DAU
FROM user_behavior
WHERE {W}
GROUP BY date(dt) ORDER BY 日期
""", con)
save(daily, "01_每日趋势.csv")

# ============ 2. 漏斗（每个用户压成一行） ============
pu = pd.read_sql(f"""
SELECT user_id,
       MAX(CASE WHEN behavior='pv'            THEN 1 ELSE 0 END) AS pv,
       MAX(CASE WHEN behavior='cart'          THEN 1 ELSE 0 END) AS cart,
       MAX(CASE WHEN behavior='fav'           THEN 1 ELSE 0 END) AS fav,
       MAX(CASE WHEN behavior='buy'           THEN 1 ELSE 0 END) AS buy,
       MAX(CASE WHEN behavior IN ('cart','fav') THEN 1 ELSE 0 END) AS intent
FROM user_behavior
WHERE {W}
GROUP BY user_id
""", con)

browse = int(pu["pv"].sum())
intent = int(((pu["pv"] == 1) & (pu["intent"] == 1)).sum())
buy_funnel = int(((pu["pv"] == 1) & (pu["intent"] == 1) & (pu["buy"] == 1)).sum())
buyers = int(pu["buy"].sum())

funnel = pd.DataFrame({
    "层级": ["浏览", "意向(加购或收藏)", "购买"],
    "顺序": [1, 2, 3],
    "人数": [browse, intent, buy_funnel],
})
funnel["相对第一层转化率"] = (funnel["人数"] / browse).round(6)
funnel["相对上一层转化率"] = funnel["人数"].div(funnel["人数"].shift(1)).fillna(1).round(6)
save(funnel, "02_漏斗.csv")

# ============ 3. 购买路径构成 ============
paths = pd.DataFrame({
    "路径": ["标准漏斗(浏览→意向→购买)", "浏览后直接购买", "无浏览、有意向、购买", "无浏览、直接购买"],
    "人数": [
        buy_funnel,
        int(((pu["pv"] == 1) & (pu["intent"] == 0) & (pu["buy"] == 1)).sum()),
        int(((pu["pv"] == 0) & (pu["intent"] == 1) & (pu["buy"] == 1)).sum()),
        int(((pu["pv"] == 0) & (pu["intent"] == 0) & (pu["buy"] == 1)).sum()),
    ],
})
paths["占比"] = (paths["人数"] / buyers).round(6)
save(paths, "03_购买路径.csv")

# ============ 4. 留存 ============
def retention(days: int) -> pd.DataFrame:
    return pd.read_sql(f"""
    WITH pu2 AS (SELECT user_id, MIN(date(dt)) AS first_day
                 FROM user_behavior WHERE {W} GROUP BY user_id),
         act AS (SELECT DISTINCT user_id, date(dt) AS d
                 FROM user_behavior WHERE {W})
    SELECT p.first_day AS 首次日期, COUNT(*) AS 新增,
           SUM(CASE WHEN a.d IS NOT NULL THEN 1 ELSE 0 END) AS 留存人数,
           1.0 * SUM(CASE WHEN a.d IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) AS 留存率
    FROM pu2 p
    LEFT JOIN act a ON a.user_id = p.user_id AND a.d = date(p.first_day, '+{days} day')
    GROUP BY p.first_day ORDER BY p.first_day
    """, con)

d1 = retention(1)
d1 = d1[d1["首次日期"] < "2017-12-03"].copy()
d1["类型"] = "次日留存"
d7 = retention(7)
d7 = d7[d7["首次日期"] <= "2017-11-26"].copy()
d7["类型"] = "7日留存"
save(pd.concat([d1, d7], ignore_index=True), "04_留存.csv")

# ============ 5. RFM 八群 ============
rfm = pd.read_sql(f"""
SELECT user_id,
       CAST(julianday('2017-12-03')
            - julianday(MAX(CASE WHEN behavior='buy' THEN date(dt) END)) AS INTEGER) AS R,
       SUM(CASE WHEN behavior='buy' THEN 1 ELSE 0 END) AS F,
       COUNT(*) AS M
FROM user_behavior
WHERE {W}
GROUP BY user_id
HAVING SUM(CASE WHEN behavior='buy' THEN 1 ELSE 0 END) > 0
""", con)
med_m = rfm["M"].median()
rfm["R层"] = np.where(rfm["R"] <= 3, "R近", "R远")
rfm["F层"] = np.where(rfm["F"] >= 2, "F复购", "F一次性")
rfm["M层"] = np.where(rfm["M"] >= med_m, "M高", "M低")
rfm["群"] = rfm["R层"] + "-" + rfm["F层"] + "-" + rfm["M层"]
g = rfm.groupby(["群", "R层", "F层", "M层"]).size().reset_index(name="人数")
g["占比"] = (g["人数"] / len(rfm)).round(6)
save(g.sort_values("人数", ascending=False), "05_RFM八群.csv")

# ============ 6. 帕累托（商品 + 品类合并） ============
def pareto(col: str, label: str) -> pd.DataFrame:
    d = pd.read_sql(f"""
        SELECT {col} AS 单位, COUNT(*) AS buys
        FROM user_behavior
        WHERE behavior='buy' AND {W}
        GROUP BY {col}
        ORDER BY buys DESC
    """, con).reset_index(drop=True)
    out = pd.DataFrame({
        "维度": label,
        "排名": d.index + 1,
        "单位占比": (d.index + 1) / len(d),
        "累计购买占比": d["buys"].cumsum() / d["buys"].sum(),
    })
    return out

pareto_all = pd.concat([pareto("item_id", "商品"), pareto("category_id", "品类")], ignore_index=True)
save(pareto_all, "06_帕累托.csv")

# ============ 7. 小时 × 星期 ============
hw = pd.read_sql(f"""
SELECT CASE WHEN strftime('%w',dt)='0' THEN '7' ELSE strftime('%w',dt) END AS 星期序号,
       CAST(strftime('%H',dt) AS INTEGER) AS 小时,
       COUNT(*) AS 行为数
FROM user_behavior WHERE {W}
GROUP BY 星期序号, 小时
""", con)
days_per = {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1, "6": 2, "7": 2}
hw["星期"] = hw["星期序号"].map(dict(zip("1234567", ["周一", "周二", "周三", "周四", "周五", "周六", "周日"])))
hw["日均"] = (hw["行为数"] / hw["星期序号"].map(days_per)).round(1)
hw["星期序号"] = hw["星期序号"].astype(int)
save(hw[["星期序号", "星期", "小时", "行为数", "日均"]], "07_小时星期.csv")

# ============ 8. KPI 汇总 ============
total_rows = int(pd.read_sql(f"SELECT COUNT(*) n FROM user_behavior WHERE {W}", con)["n"].iloc[0])
kpi = pd.DataFrame({
    "指标": ["总行为数", "用户数", "购买用户数", "未购买率", "浏览→购买转化率", "核心用户(复购且近期)", "一次性买家占比"],
    "数值": [
        f"{total_rows:,}", f"{len(pu):,}", f"{buyers:,}",
        f"{1 - buyers/len(pu):.2%}", f"{buy_funnel/browse:.2%}",
        f"{int(((rfm['R']<=3)&(rfm['F']>=2)&(rfm['M']>=med_m)).sum()):,}",
        f"{(rfm['F']==1).mean():.2%}",
    ],
    "说明": ["9天窗口内", "有任意行为", "有购买行为", "从未购买", "严格漏斗口径", "R近·复购·M高", "F=1"],
})
save(kpi, "08_KPI.csv")

con.close()
print(f"\n全部导出到: {OUT}")
