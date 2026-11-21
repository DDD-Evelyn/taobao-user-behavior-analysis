-- ============================================================
-- 00_热身.sql · 0 组：摸清数据边界
-- 项目：电商用户行为分析与经营看板
-- 数据：taobao.db / user_behavior（5% 抽样，5,007,540 行）
-- 说明：dt 为已转换为北京时间的日期时间文本
-- ============================================================

-- Q0.1 表规模：行数 / 用户数 / 商品数 / 品类数
SELECT COUNT(*)                    AS 总行数,
       COUNT(DISTINCT user_id)     AS 用户数,
       COUNT(DISTINCT item_id)     AS 商品数,
       COUNT(DISTINCT category_id) AS 品类数
FROM user_behavior;

-- Q0.2 行为类型分布（pv 应占约九成，buy 最少）
SELECT behavior, COUNT(*) AS 条数
FROM user_behavior
GROUP BY behavior
ORDER BY 条数 DESC;

-- Q0.3 日期覆盖：预期 9 天；若出现 1920/2028 等，说明存在越界时间戳
SELECT date(dt) AS 日期, COUNT(*) AS 条数
FROM user_behavior
GROUP BY date(dt)
ORDER BY 日期;

-- Q0.3 补充：只看 9 天主窗口（分析统一使用这个范围）
SELECT date(dt) AS 日期, COUNT(*) AS 条数
FROM user_behavior
WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
GROUP BY date(dt)
ORDER BY 日期;
