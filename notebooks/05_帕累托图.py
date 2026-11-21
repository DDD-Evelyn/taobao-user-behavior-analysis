"""
05_帕累托图.py —— 商品 vs 品类的帕累托曲线（自己做）
运行： python notebooks/05_帕累托图.py
输出： report/fig05_帕累托.png

模板里「品类」这条线已经写好，可以单独跑通。
你的任务：照抄它，补出「商品」那条线。一共 3 个 TODO。
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
OUT = ROOT / "report" / "fig05_帕累托.png"
W = "date(dt) BETWEEN '2017-11-25' AND '2017-12-03'"

con = sqlite3.connect(DB)

# ---------- 品类曲线（已写好，先跑通这一条） ----------
sql_cat = f"""
SELECT category_id, COUNT(*) AS buys
FROM user_behavior
WHERE behavior = 'buy' AND {W}
GROUP BY category_id
ORDER BY buys DESC
"""
cat = pd.read_sql(sql_cat, con).reset_index(drop=True)
cat["cum_share"] = cat["buys"].cumsum() / cat["buys"].sum()   # 累计占比
cat["unit_pct"] = (cat.index + 1) / len(cat)                  # 前百分之几的单位

# ---------- 商品曲线（TODO 1 & 2：你来做） ----------
# TODO 1：把上面的 sql_cat 复制一份，把 category_id 改成 item_id，
#         查询结果存到 item 这个变量里（记得 reset_index）
sql_item = f"""
SELECT item_id, COUNT(*) AS buys
FROM user_behavior
WHERE behavior = 'buy' AND {W}
GROUP BY item_id
ORDER BY buys DESC
"""
item = pd.read_sql(sql_item, con).reset_index(drop=True)
# TODO 2：照抄上面两行，给 item 也算出 cum_share 和 unit_pct
item["cum_share"] = item["buys"].cumsum() / item["buys"].sum()   # 累计占比
item["unit_pct"] = (item.index + 1) / len(item)                  # 前百分之几的单位

# 打印 80% 拐点（品类）
def pct_for_80(df):
    hit = df[df["cum_share"] >= 0.8]
    return hit["unit_pct"].iloc[0] if len(hit) else None

print(f"品类：{len(cat):,} 个，80% 购买需要 {pct_for_80(cat):.2%} 的品类")
print(f"商品：{len(item):,} 个，80% 购买需要 {pct_for_80(item):.2%} 的商品")
# ---------- 画图 ----------
fig, ax = plt.subplots(figsize=(9.5, 5.5), dpi=160)

ax.plot(cat["unit_pct"], cat["cum_share"], label="品类", color="#c0392b", linewidth=2)

# TODO 3：再画一条 item 的线（照抄上面那行，换变量名和颜色）
ax.plot(item["unit_pct"], item["cum_share"], label="商品", color="#2980b9", linewidth=2)

ax.axhline(0.8, color="#7f8c8d", linestyle="--", linewidth=1)
ax.text(0.62, 0.81, "80% 购买", color="#7f8c8d", fontsize=9)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1.02)
ax.set_xlabel("累计单位占比（按购买次数从高到低排序）")
ax.set_ylabel("累计购买占比")
ax.set_title("帕累托曲线：品类 vs 商品", fontsize=13)
ax.grid(alpha=0.3, linestyle="--")
ax.legend(loc="lower right")

# 标出品类 80% 拐点
x80 = pct_for_80(cat)
if x80 is not None:
    ax.scatter([x80], [0.8], color="#c0392b", zorder=5)
    ax.annotate(f"品类：{x80:.1%}", xy=(x80, 0.8), xytext=(x80 + 0.08, 0.66),
                fontsize=9, color="#c0392b",
                arrowprops=dict(arrowstyle="->", color="#c0392b"))
# 标出商品 80% 拐点
x80_item = pct_for_80(item)
if x80_item is not None:
    ax.scatter([x80_item], [0.8], color="#2980b9", zorder=5)
    ax.annotate(f"商品：{x80_item:.1%}", xy=(x80_item, 0.8),
                xytext=(x80_item - 0.12, 0.62),
                fontsize=9, color="#2980b9",
                arrowprops=dict(arrowstyle="->", color="#2980b9"))
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("已保存:", OUT)
