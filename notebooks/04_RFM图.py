"""
04_RFM图.py —— RFM 八群人数 + 一次性/复购对比
运行： python notebooks/04_RFM图.py
输出： report/fig04_RFM.png
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
OUT = ROOT / "report" / "fig04_RFM.png"
W = "date(dt) BETWEEN '2017-11-25' AND '2017-12-03'"

# ---------- 1. SQL 只取每个买家的 R / F / M ----------
con = sqlite3.connect(DB)
sql = f"""
SELECT user_id,
       CAST(julianday('2017-12-03')
            - julianday(MAX(CASE WHEN behavior='buy' THEN date(dt) END)) AS INTEGER) AS R,
       SUM(CASE WHEN behavior='buy' THEN 1 ELSE 0 END) AS F,
       COUNT(*) AS M
FROM user_behavior
WHERE {W}
GROUP BY user_id
HAVING SUM(CASE WHEN behavior='buy' THEN 1 ELSE 0 END) > 0
"""
rfm = pd.read_sql(sql, con)
con.close()
print(f"RFM 用户数 {len(rfm):,}")

# ---------- 2. pandas 里做分层（阈值同 D 组） ----------
med_m = rfm["M"].median()
print(f"M 中位数 = {med_m}")

rfm["R层"] = np.where(rfm["R"] <= 3, "R近", "R远")
rfm["F层"] = np.where(rfm["F"] >= 2, "F复购", "F一次性")
rfm["M层"] = np.where(rfm["M"] >= med_m, "M高", "M低")

grp = (rfm.groupby(["R层", "F层", "M层"])
          .size().reset_index(name="人数"))
grp["占比"] = grp["人数"] / len(rfm)
grp["群"] = grp["R层"] + "-" + grp["F层"] + "-" + grp["M层"]
print(grp.sort_values("人数", ascending=False).to_string(index=False))

# ---------- 3. 画图 ----------
fig, axes = plt.subplots(1, 2, figsize=(13.5, 5), dpi=160,
                         gridspec_kw={"width_ratios": [1.55, 1]})

# 左：8 群横向条形，按人数从大到小（自下而上画，所以先升序）
ax = axes[0]
g = grp.sort_values("人数")
colors = ["#c0392b" if f == "F复购" else "#aab7c4" for f in g["F层"]]
bars = ax.barh(g["群"], g["人数"], color=colors, height=0.65)
for b, v, p in zip(bars, g["人数"], g["占比"]):
    ax.text(v + len(rfm) * 0.005, b.get_y() + b.get_height() / 2,
            f"{v:,} ({p:.1%})", va="center", fontsize=9)
ax.set_xlim(0, max(g["人数"]) * 1.28)
ax.set_xlabel("人数")
ax.set_title("RFM 八群（红＝复购，灰＝一次性）", fontsize=12)
ax.grid(axis="x", alpha=0.3, linestyle="--")
# 圈出核心群
core = grp[grp["群"] == "R近-F复购-M高"]
if len(core):
    cy = list(g["群"]).index("R近-F复购-M高")
    ax.scatter([core["人数"].iloc[0] * 1.02], [cy], marker="*", s=220,
               color="#f1c40f", edgecolor="#7b241c", zorder=5)
    ax.annotate("真·核心用户", xy=(core["人数"].iloc[0], cy),
                xytext=(core["人数"].iloc[0] + len(rfm) * 0.10, cy - 0.2),
                fontsize=9, color="#7b241c",
                arrowprops=dict(arrowstyle="->", color="#7b241c"))

# 右：一次性 vs 复购
ax = axes[1]
fc = rfm.groupby("F层").size()
vals = [fc.get("F一次性", 0), fc.get("F复购", 0)]
labels = ["一次性\n(F=1)", "复购\n(F≥2)"]
bars = ax.bar(labels, vals, color=["#aab7c4", "#c0392b"], width=0.55)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + len(rfm)*0.005,
            f"{v:,}\n{v/len(rfm):.1%}", ha="center", fontsize=10)
ax.set_ylim(0, max(vals) * 1.18)
ax.set_ylabel("人数")
ax.set_title("一次性 vs 复购", fontsize=12)
ax.grid(axis="y", alpha=0.3, linestyle="--")

fig.suptitle("RFM 分层：90.2% 的买家只买过一次", fontsize=14, y=1.02)
plt.tight_layout()
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("已保存:", OUT)
