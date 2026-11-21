"""
03_留存图.py —— 次日留存曲线 + 次日/7日对比
运行： python notebooks/03_留存图.py
输出： report/fig03_留存.png
"""
from pathlib import Path
import sqlite3

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = [
    "PingFang SC", "Heiti TC", "STHeiti", "PingFang HK", "Arial Unicode MS",
]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "taobao.db"
OUT = ROOT / "report" / "fig03_留存.png"

W = "date(dt) BETWEEN '2017-11-25' AND '2017-12-03'"

con = sqlite3.connect(DB)

def retention(days: int) -> pd.DataFrame:
    """按首次日期算第 N 日留存。days=1 是次日，days=7 是第 7 日。"""
    sql = f"""
    WITH pu AS (
        SELECT user_id, MIN(date(dt)) AS first_day
        FROM user_behavior
        WHERE {W}
        GROUP BY user_id
    ),
    act AS (
        SELECT DISTINCT user_id, date(dt) AS d
        FROM user_behavior
        WHERE {W}
    )
    SELECT p.first_day AS 首次日期,
           COUNT(*) AS 新增,
           SUM(CASE WHEN a.d IS NOT NULL THEN 1 ELSE 0 END) AS 留存,
           1.0 * SUM(CASE WHEN a.d IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) AS 留存率
    FROM pu p
    LEFT JOIN act a
           ON a.user_id = p.user_id
          AND a.d = date(p.first_day, '+{days} day')
    GROUP BY p.first_day
    ORDER BY p.first_day
    """
    return pd.read_sql(sql, con)

d1 = retention(1)
d7 = retention(7)
con.close()

# 12-03 的"次日"是 12-04，数据里没有 → 不可观测，剔除
d1_valid = d1[d1["首次日期"] < "2017-12-03"].copy()
# 7 日留存只保留"首次日期+7 仍在窗口内"的批次
d7_valid = d7[d7["留存率"].notna() & (d7["首次日期"] <= "2017-11-26")].copy()

print("次日留存（12-03 不可观测，已剔除）:")
print(d1_valid[["首次日期", "新增", "留存", "留存率"]].to_string(index=False))
print("\n7 日留存（只有 11-25/11-26 可算）:")
print(d7_valid[["首次日期", "新增", "留存", "留存率"]].to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), dpi=160,
                         gridspec_kw={"width_ratios": [1.45, 1]})

# ---------- 左：逐日次日留存 ----------
ax = axes[0]
x = np.arange(len(d1_valid))
bars = ax.bar(x, d1_valid["留存率"], color="#2980b9", width=0.6)
for xi, v in zip(x, d1_valid["留存率"]):
    ax.text(xi, v + 0.008, f"{v:.1%}", ha="center", fontsize=9)
# 12-03 不可观测：用浅灰底标记这个"位置"，但不画柱子（避免被误读成 0）
ax.axvspan(len(d1_valid) - 0.4, len(d1_valid) + 0.4, color="#ecf0f1", zorder=0)
ax.text(len(d1_valid), 0.03, "12-03\n不可观测", ha="center", va="bottom",
        fontsize=8.5, color="#7f8c8d")
ax.set_xticks(np.arange(len(d1_valid) + 1))
ax.set_xticklabels(list(d1_valid["首次日期"]) + ["12-03"], rotation=30, fontsize=8.5)
ax.set_ylim(0, 0.55)
ax.set_ylabel("次日留存率")
ax.set_title("逐日次日留存率（分母＝当日新增用户）", fontsize=12)
ax.grid(axis="y", alpha=0.3, linestyle="--")
ax.text(0.02, 0.95, "11-25 偏高：混入老用户（首日污染）", transform=ax.transAxes,
        fontsize=8.5, color="#c0392b", va="top")

# ---------- 右：次日 vs 7 日 ----------
ax = axes[1]
cohorts = ["11-25", "11-26"]
r1 = [d1[d1["首次日期"] == "2017-" + c]["留存率"].iloc[0] for c in cohorts]
r7 = [d7[d7["首次日期"] == "2017-" + c]["留存率"].iloc[0] for c in cohorts]
xx = np.arange(len(cohorts))
w = 0.35
ax.bar(xx - w/2, r1, w, label="次日留存", color="#2980b9")
ax.bar(xx + w/2, r7, w, label="7 日留存", color="#c0392b")
for i in range(len(cohorts)):
    ax.text(xx[i] - w/2, r1[i] + 0.008, f"{r1[i]:.1%}", ha="center", fontsize=9)
    ax.text(xx[i] + w/2, r7[i] + 0.008, f"{r7[i]:.1%}", ha="center", fontsize=9)
ax.set_xticks(xx)
ax.set_xticklabels([f"{c} 批次" for c in cohorts])
ax.set_ylim(0, 0.55)
ax.set_title("次日 vs 7 日留存：7 日反而更高", fontsize=12)
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3, linestyle="--")
ax.text(0.5, -0.22, "原因：两批的第 7 天恰逢 12-02/12-03 周末流量高峰（日历效应），不可与次日直接比较。",
        transform=ax.transAxes, ha="center", fontsize=8.5, color="#555")

fig.suptitle("留存分析：逐日次日留存 + 次日/7 日对比", fontsize=14, y=1.02)
plt.tight_layout()
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("已保存:", OUT)
