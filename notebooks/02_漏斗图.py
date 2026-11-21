"""
02_漏斗图.py —— 三层漏斗 + 购买路径构成
运行方式（在项目文件夹下）：
    python notebooks/02_漏斗图.py
输出：
    report/fig02_漏斗与购买路径.png
"""
from pathlib import Path
import sqlite3

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = [
    "PingFang SC", "Heiti TC", "STHeiti", "PingFang HK", "Arial Unicode MS",
]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "taobao.db"
OUT = ROOT / "report" / "fig02_漏斗与购买路径.png"

# ---------- 读数据：先把用户压成一行 ----------
con = sqlite3.connect(DB)
sql = """
WITH per_user AS (
    SELECT user_id,
           MAX(CASE WHEN behavior = 'pv'                 THEN 1 ELSE 0 END) AS has_pv,
           MAX(CASE WHEN behavior IN ('cart','fav')      THEN 1 ELSE 0 END) AS has_intent,
           MAX(CASE WHEN behavior = 'buy'                THEN 1 ELSE 0 END) AS has_buy
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id
)
SELECT
    SUM(has_pv)                                                          AS browse,
    SUM(CASE WHEN has_pv=1 AND has_intent=1 THEN 1 ELSE 0 END)           AS intent,
    SUM(CASE WHEN has_pv=1 AND has_intent=1 AND has_buy=1 THEN 1 ELSE 0 END) AS buy_in_funnel,
    SUM(has_buy)                                                         AS buyers,
    -- 购买路径拆分
    SUM(CASE WHEN has_pv=1 AND has_intent=1 AND has_buy=1 THEN 1 ELSE 0 END) AS p_funnel,
    SUM(CASE WHEN has_pv=1 AND has_intent=0 AND has_buy=1 THEN 1 ELSE 0 END) AS p_direct_buy,
    SUM(CASE WHEN has_pv=0 AND has_intent=1 AND has_buy=1 THEN 1 ELSE 0 END) AS p_no_browse_intent,
    SUM(CASE WHEN has_pv=0 AND has_intent=0 AND has_buy=1 THEN 1 ELSE 0 END) AS p_no_browse_direct
FROM per_user
"""
row = pd.read_sql(sql, con).iloc[0]
con.close()

browse, intent, buy = int(row.browse), int(row.intent), int(row.buy_in_funnel)
buyers = int(row.buyers)
print(f"浏览 {browse:,}  意向 {intent:,}  漏斗内购买 {buy:,}  总买家 {buyers:,}")
print(f"漏斗覆盖率 {buy/buyers:.1%}")

# ---------- 图 1：漏斗 ----------
fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=160,
                         gridspec_kw={"width_ratios": [1, 1.15]})

ax = axes[0]
stages = ["浏览", "意向\n(加购或收藏)", "购买"]
vals = [browse, intent, buy]
colors = ["#2c3e50", "#e67e22", "#c0392b"]
bars = ax.barh(range(len(stages))[::-1], vals, color=colors, height=0.6)
for i, (v, b) in enumerate(zip(vals, bars)):
    ax.text(v + max(vals) * 0.02, b.get_y() + b.get_height() / 2,
            f"{v:,}  ({v/browse:.1%})", va="center", fontsize=10)
ax.set_yticks(range(len(stages))[::-1])
ax.set_yticklabels(stages, fontsize=11)
ax.set_xlim(0, max(vals) * 1.28)
ax.set_title("三层漏斗（严格嵌套）", fontsize=13)
ax.set_xlabel("人数")
ax.grid(axis="x", alpha=0.3, linestyle="--")

# ---------- 图 2：购买路径构成（总买家 = 100%） ----------
ax = axes[1]
parts = [
    ("标准漏斗（浏览→意向→购买）", int(row.p_funnel), "#c0392b"),
    ("浏览后直接购买", int(row.p_direct_buy), "#e67e22"),
    ("无浏览、有意向、购买", int(row.p_no_browse_intent), "#f1c40f"),
    ("无浏览、直接购买", int(row.p_no_browse_direct), "#95a5a6"),
]
left = 0
for label, v, c in parts:
    ax.barh([0], [v], left=left, color=c, height=0.5, label=f"{label}  {v:,} ({v/buyers:.1%})")
    left += v
ax.set_yticks([])
ax.set_xlim(0, buyers)
ax.set_title(f"购买路径构成（总买家 {buyers:,}）", fontsize=13)
ax.set_xlabel("人数")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), fontsize=9, frameon=False)
ax.text(buyers * 0.5, 0.42, f"漏斗只覆盖 {buy/buyers:.1%} 的购买者", ha="center",
        fontsize=11, color="#7b241c", fontweight="bold")

fig.suptitle(f"漏斗转化 + 购买路径：{1-buy/buyers:.1%} 的购买发生在漏斗之外", fontsize=14, y=1.02)
plt.tight_layout()
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("已保存:", OUT)
