# Python 画图速查卡（分析师够用版）

> **不用背。** 做图时打开这张卡，复制、改数字、跑。90% 的分析图就这几招。

---

## 0. 每次开头都一样的 4 行

```python
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")          # 不弹窗，直接存文件
```

中文字体（Mac）：

```python
plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti TC", "STHeiti"]
plt.rcParams["axes.unicode_minus"] = False
```

---

## 1. 读数据：SQL → 表格

```python
con = sqlite3.connect("taobao.db")
df = pd.read_sql("SELECT ... FROM ...", con)
con.close()
```

`df` 就是一张 Excel 表，列名就是你 SQL 里的别名。

---

## 2. 看数据

```python
df.head()          # 前 5 行
df.shape           # (行数, 列数)
df["列名"].describe()   # 均值/分位/最大最小
```

---

## 3. 分组统计（= SQL 的 GROUP BY）

```python
df.groupby("列A").size()                    # 每个 A 有多少行
df.groupby("列A")["列B"].sum()              # 每个 A 的 B 之和
df.groupby(["列A","列B"]).size().reset_index(name="人数")
```

---

## 4. 条件打标签（= SQL 的 CASE WHEN）

```python
import numpy as np
df["等级"] = np.where(df["分数"] >= 60, "及格", "不及格")
```

多个条件用 `np.select`：

```python
df["档"] = np.select(
    [df["分数"] >= 90, df["分数"] >= 60],
    ["高", "中"],
    default="低",
)
```

---

## 5. 画图：三种最常用

**折线（看趋势）**

```python
fig, ax = plt.subplots(figsize=(10, 5), dpi=160)
ax.plot(df["日期"], df["数值"], marker="o", label="图例名")
```

**竖柱（比大小）**

```python
ax.bar(df["类别"], df["数值"], color="#2980b9")
```

**横条（类别名字长时用这个）**

```python
ax.barh(df["类别"], df["数值"])
```

---

## 6. 图上加字

```python
ax.set_title("标题", fontsize=14)
ax.set_xlabel("X 轴"); ax.set_ylabel("Y 轴")
ax.legend()
ax.grid(alpha=0.3, linestyle="--")

# 在每个柱子顶上写数值
for x, y in zip(df["类别"], df["数值"]):
    ax.text(x, y, f"{y:,}", ha="center", va="bottom")

# 带箭头的标注
ax.annotate("这里很重要", xy=(x点, y点), xytext=(文字x, 文字y),
            arrowprops=dict(arrowstyle="->"))
```

---

## 7. 保存

```python
fig.savefig("report/图名.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
```

---

## 8. 导出 CSV 给 Tableau

```python
df.to_csv("report/数据_趋势.csv", index=False, encoding="utf-8-sig")
```

（`utf-8-sig` 是为了 Excel / Tableau 打开中文不乱码。）

---

## 常见报错对照

| 报错 | 原因 | 解决 |
|---|---|---|
| `ModuleNotFoundError` | 这个 Python 没装包 | `pip install 包名` |
| 图里中文是方块 | 没设字体 | 复制第 0 节字体那两行 |
| `KeyError: '列名'` | 列名拼错 / SQL 别名不同 | `print(df.columns)` 看真实列名 |
| `ValueError: x and y must have same length` | 两个列表长度不一样 | `print(len(x), len(y))` |
| `no such table` | 数据库路径不对 | 确认 `taobao.db` 和脚本的相对位置 |
| 图是空的 | 数据筛选后为空 | 先 `print(df.shape)` 看有没有数据 |

---

## 心法

1. **不要从空白写。** 拿一个能跑的模板，改列名、改标题、改颜色。
2. **一次只改一处，跑一次。** 改完立刻运行，错了容易定位。
3. **报错先看最后一行。** 那一行通常直接告诉你哪里错了。
4. **你只需要"看懂 + 改对 + 讲清"**，不需要默写代码。分析师日常也是复制粘贴改。
