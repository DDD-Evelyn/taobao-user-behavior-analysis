"""
数据导入脚本 —— 把淘宝用户行为数据集抽样后导入 SQLite
=====================================================
用途：原始文件约 1 亿行 / 3.4GB，直接分析会卡死。本脚本按比例随机抽样，
      转换时间戳，写入 SQLite 数据库并建索引，供 SQL 分析使用。

使用：
    1. 把下载的 UserBehavior.csv 放在本脚本同一目录
    2. 命令行运行：python 数据导入脚本.py
    3. 完成后会生成 taobao.db，里面有一张 user_behavior 表

依赖：pandas （安装：pip install pandas）
"""
import os
import sqlite3

import pandas as pd

# ---------------- 配置 ----------------
SRC = "UserBehavior.csv"      # 原始数据文件（原文件没有表头）
DB = "taobao.db"              # 输出的数据库文件
TABLE = "user_behavior"
SAMPLE_RATE = 0.05            # 抽样比例：0.05 约等于 500 万行，够用了
CHUNK_ROWS = 2_000_000        # 每次读入的行数（控制内存，不要改太大）
SEED = 42                     # 随机种子，保证结果可复现

COLS = ["user_id", "item_id", "category_id", "behavior", "timestamp"]


def main():
    if not os.path.exists(SRC):
        raise SystemExit(
            f"\n[错误] 找不到数据文件：{SRC}\n"
            f"请先从天池下载数据集，解压后把 UserBehavior.csv 放到：\n"
            f"  {os.getcwd()}\n"
            f"下载地址：https://tianchi.aliyun.com/dataset/649\n"
        )

    # ---------- 1. 分块读取 + 随机抽样 ----------
    print("1/4  分块读取并抽样中（1 亿行，大约需要 2-5 分钟）...")
    parts = []
    total_rows = 0
    for i, chunk in enumerate(
        pd.read_csv(SRC, header=None, names=COLS, chunksize=CHUNK_ROWS)
    ):
        total_rows += len(chunk)
        parts.append(chunk.sample(frac=SAMPLE_RATE, random_state=SEED))
        print(f"      已读取 {total_rows:,} 行 ...", end="\r")
    df = pd.concat(parts, ignore_index=True)
    print(f"\n      原始 {total_rows:,} 行  →  抽样后 {len(df):,} 行")

    # ---------- 2. 转换时间戳 ----------
    # timestamp 是从 1970-01-01 起的秒数（UTC）。原始数据的行为时间对应北京时间，
    # 所以必须先按 UTC 解析，再转到东八区，最后去掉时区信息，
    # 否则所有日期会整体偏移 8 小时（最早一天会错误地显示成 2017-11-24）。
    print("2/4  转换时间戳（按北京时间）...")
    df["dt"] = (
        pd.to_datetime(df["timestamp"], unit="s", utc=True)
        .dt.tz_convert("Asia/Shanghai")
        .dt.tz_localize(None)
    )

    # ---------- 3. 写入 SQLite ----------
    print("3/4  写入 SQLite 数据库 ...")
    conn = sqlite3.connect(DB)
    df.to_sql(TABLE, conn, if_exists="replace", index=False)

    # ---------- 4. 建索引（大幅加速后续查询） ----------
    print("4/4  建立索引 ...")
    cur = conn.cursor()
    for col in ["user_id", "item_id", "category_id", "behavior", "dt"]:
        cur.execute(f'CREATE INDEX IF NOT EXISTS idx_{TABLE}_{col} ON {TABLE}({col})')
    conn.commit()

    # ---------------- 自检 ----------------
    print("\n" + "=" * 52)
    print("自检结果（请确认下列数字是否合理）")
    print("=" * 52)

    summary = pd.read_sql(
        f"SELECT COUNT(*) AS 总行数, "
        f"COUNT(DISTINCT user_id) AS 用户数, "
        f"COUNT(DISTINCT item_id) AS 商品数, "
        f"COUNT(DISTINCT date(dt)) AS 天数, "
        f"MIN(dt) AS 最早时间, MAX(dt) AS 最晚时间 "
        f"FROM {TABLE}",
        conn,
    )
    print(summary.to_string(index=False))
    print("\n（正常情况下：天数应为 9，最早时间应为 2017-11-25。若不是，请检查时区处理。）")

    print("\n各行为类型分布：")
    print(
        pd.read_sql(
            f"SELECT behavior AS 行为, COUNT(*) AS 条数 "
            f"FROM {TABLE} GROUP BY behavior ORDER BY 条数 DESC",
            conn,
        ).to_string(index=False)
    )

    conn.close()
    print("\n" + "=" * 52)
    print(f"完成！数据库：{DB}   表名：{TABLE}")
    print("下一步：安装 DB Browser for SQLite，打开 taobao.db 开始写 SQL。")
    print("=" * 52)


if __name__ == "__main__":
    main()
