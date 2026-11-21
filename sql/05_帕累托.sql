-- ============================================================
-- 05_帕累托.sql · E 组：谁在贡献主要价值
-- 方法：按购买次数降序 → 累计求和 → 累计占比
-- 关键：窗口函数必须显式写 ROWS 帧
--       默认 RANGE 帧遇到并列值会整组一起加，导致累计瞬间跳满
-- 注意：行级 5% 抽样会系统性低估集中度，商品级结论应以全量为准
-- ============================================================

-- Q5.1 商品维度：累计购买占比 + 累计单位占比
SELECT item_id,
       buys,
       SUM(buys) OVER (ORDER BY buys DESC
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_buys,
       ROUND(100.0 * SUM(buys) OVER (ORDER BY buys DESC
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(buys) OVER (), 2) AS cum_pct,
       ROUND(100.0 * ROW_NUMBER() OVER (ORDER BY buys DESC)
             / COUNT(*) OVER (), 2) AS item_pct
FROM (
    SELECT item_id, COUNT(*) AS buys
    FROM user_behavior
    WHERE behavior = 'buy'
      AND date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY item_id
) AS item_buys
ORDER BY buys DESC;

-- Q5.1 80% 拐点：第一个累计占比 >= 80% 的位置
SELECT MIN(item_pct) AS 达到80pct的商品占比
FROM (
    SELECT ROUND(100.0 * SUM(buys) OVER (ORDER BY buys DESC
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                 / SUM(buys) OVER (), 2) AS cum_pct,
           ROUND(100.0 * ROW_NUMBER() OVER (ORDER BY buys DESC)
                 / COUNT(*) OVER (), 2) AS item_pct
    FROM (
        SELECT item_id, COUNT(*) AS buys
        FROM user_behavior
        WHERE behavior = 'buy'
          AND date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
        GROUP BY item_id
    ) AS item_buys
)
WHERE cum_pct >= 80;

-- Q5.2 品类维度：同上，只换字段
SELECT category_id,
       buys,
       SUM(buys) OVER (ORDER BY buys DESC
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_buys,
       ROUND(100.0 * SUM(buys) OVER (ORDER BY buys DESC
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(buys) OVER (), 2) AS cum_pct,
       ROUND(100.0 * ROW_NUMBER() OVER (ORDER BY buys DESC)
             / COUNT(*) OVER (), 2) AS item_pct
FROM (
    SELECT category_id, COUNT(*) AS buys
    FROM user_behavior
    WHERE behavior = 'buy'
      AND date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY category_id
) AS category_buys
ORDER BY buys DESC;

-- Q5.2 品类 80% 拐点
SELECT MIN(item_pct) AS 达到80pct的品类占比
FROM (
    SELECT ROUND(100.0 * SUM(buys) OVER (ORDER BY buys DESC
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                 / SUM(buys) OVER (), 2) AS cum_pct,
           ROUND(100.0 * ROW_NUMBER() OVER (ORDER BY buys DESC)
                 / COUNT(*) OVER (), 2) AS item_pct
    FROM (
        SELECT category_id, COUNT(*) AS buys
        FROM user_behavior
        WHERE behavior = 'buy'
          AND date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
        GROUP BY category_id
    ) AS category_buys
)
WHERE cum_pct >= 80;
