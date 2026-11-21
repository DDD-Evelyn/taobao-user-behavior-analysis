"""
01_趋势图.py —— 每日 PV / UV / DAU 趋势
运行方式（在项目文件夹下）：
    python notebooks/01_趋势图.py
输出：
    report/fig01_每日趋势.png
"""
from pathlib import Path
import sqlite3

import pandas as pd
import matplotlib
matplotlib.use("Agg")          # 不弹窗，直接存成图片文件
import matplotlib.pyplot as plt

# ---------- 1. 中文字体（Mac） ----------
# 不设这个，图里的中文会变成方块
plt.rcParams["font.sans-serif"] = [
    "PingFang SC", "Heiti TC", "STHeiti", "PingFang HK", "Arial Unicode MS",
]
plt.rcParams["axes.unicode_minus"] = False

# ---------- 2. 路径 ----------
ROOT = Path(__file__).resolve().parent.parent   # 从 notebooks/ 回到项目根目录
DB = ROOT / "taobao.db"
OUT = ROOT / "report" / "fig01_每日趋势.png"
OUT.parent.mkdir(exist_ok=True)

# ---------- 3. 读数据 ----------
# pandas.read_sql 会把查询结果直接变成一张表（DataFrame）
con = sqlite3.connect(DB)
sql = """
SELECT date(dt) AS 日期,
       SUM(CASE WHEN behavior='pv' THEN 1 ELSE 0 END)            AS PV,
       COUNT(DISTINCT CASE WHEN behavior='pv' THEN user_id END)  AS UV,
       COUNT(DISTINCT user_id)                                   AS DAU
FROM user_behavior
WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
GROUP BY date(dt)
ORDER BY 日期
"""
df = pd.read_sql(sql, con)
con.close()

df["日期"] = pd.to_datetime(df["日期"])   # 转成日期类型，x 轴才会按时间排
print(df.to_string(index=False))

# ---------- 4. 画图 ----------
fig, ax = plt.subplots(figsize=(10, 5), dpi=160)

ax.plot(df["日期"], df["PV"],  marker="o", label="PV（浏览次数）", color="#c0392b")
ax.plot(df["日期"], df["DAU"], marker="s", label="DAU（活跃用户）", color="#2c3e50")
ax.plot(df["日期"], df["UV"],  marker="^", label="UV（浏览用户）", color="#2980b9")

# 标出 12-02 / 12-03 这两天异常
ax.axvspan(pd.Timestamp("2017-12-02"), pd.Timestamp("2017-12-03") + pd.Timedelta(hours=12),
           color="orange", alpha=0.10, label="12-02/03 流量异常")

ax.set_title("每日 PV / UV / DAU（2017-11-25 ~ 12-03）", fontsize=14, pad=12)
ax.set_ylabel("数量")
ax.grid(alpha=0.3, linestyle="--")
ax.legend(loc="lower right", fontsize=9)
ax.tick_params(axis="x", rotation=30)
fig.autofmt_xdate()

# ---------- 5. 保存 ----------
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("已保存:", OUT)
