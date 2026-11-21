-- ============================================================
-- 07_数据质量.sql · G 组：异常用户与沉默用户
-- 注意：行级 5% 抽样会把重度用户的行为数压缩到约 1/20，
--       样本无法可靠检测异常用户；真实异常需回全量数据确认。
-- ============================================================

-- Q7.1 每个用户每天的行为次数（用户×日）
SELECT user_id, date(dt) AS 日期, COUNT(*) AS 次数
FROM user_behavior
WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
GROUP BY user_id, date(dt)
ORDER BY 次数 DESC
LIMIT 20;

-- Q7.1 最大值
SELECT MAX(n) AS 单日最大行为数
FROM (
    SELECT user_id, date(dt), COUNT(*) AS n
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id, date(dt)
);

-- Q7.1 99 分位：先查有多少个"用户×日"，再用 OFFSET 取 99% 位置
SELECT COUNT(*) AS 用户日组合数
FROM (
    SELECT user_id, date(dt), COUNT(*) AS n
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id, date(dt)
);

SELECT n AS p99
FROM (
    SELECT user_id, date(dt), COUNT(*) AS n
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id, date(dt)
)
ORDER BY n
LIMIT 1 OFFSET 2723284;   -- = 2,750,792 × 99%，换数据后需按实际组合数调整

-- Q7.1 阈值剔除的敏感性：单日 ≥ N 次的用户×日数量
-- 业务阈值取 200 次/天（149 次"人可能做到"、526 次"不像人"之间）
SELECT 200 AS 阈值, COUNT(*) AS 用户日数
FROM (
    SELECT user_id, date(dt), COUNT(*) AS n
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id, date(dt)
    HAVING n >= 200
);

-- Q7.2 从未购买的用户数（分母、分子都限定在 9 天窗口内）
SELECT COUNT(DISTINCT user_id) AS 总用户数,
       COUNT(DISTINCT CASE WHEN behavior = 'buy' THEN user_id END) AS 购买用户数,
       COUNT(DISTINCT user_id)
         - COUNT(DISTINCT CASE WHEN behavior = 'buy' THEN user_id END) AS 未购买用户数,
       ROUND((COUNT(DISTINCT user_id)
              - COUNT(DISTINCT CASE WHEN behavior = 'buy' THEN user_id END)) * 1.0
             / COUNT(DISTINCT user_id), 4) AS 未购买率
FROM user_behavior
WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03';
