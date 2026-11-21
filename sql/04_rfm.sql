-- ============================================================
-- 04_rfm.sql · D 组：把用户分层
-- 口径：
--   基准日 = 2017-12-03（数据集最后一天，不是"今天"）
--   只算购买过的用户（未购买者单独归为"未购买用户"）
--   R = 基准日 − 最后购买日（天）
--   F = buy 记录条数（商品件次，不是订单数）
--   M = 总行为次数（数据无金额，用活跃度近似）
-- 注意：
--   本数据 R 只有 0~8 天、F 有 90% 为 1，R/F 区分度弱，报告已说明
-- ============================================================

-- Q4.1 每个购买用户的 R / F / M
SELECT user_id,
       CAST(julianday('2017-12-03')
            - julianday(MAX(CASE WHEN behavior = 'buy' THEN date(dt) END)) AS INTEGER) AS R,
       SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) AS F,
       COUNT(*) AS M
FROM user_behavior
WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
GROUP BY user_id
HAVING SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) > 0;

-- Q4.2 分位数切两档（NTILE 版）
-- 注意：本数据 F=1 占 90%，NTILE 会把大量并列值随机拆到两组，
--       该版本的"F 高/低"不可靠，仅作为对照保留。
WITH rfm AS (
    SELECT user_id,
           CAST(julianday('2017-12-03')
                - julianday(MAX(CASE WHEN behavior = 'buy' THEN date(dt) END)) AS INTEGER) AS R,
           SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) AS F,
           COUNT(*) AS M
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id
    HAVING SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) > 0
),
b AS (
    SELECT user_id, R, F, M,
           NTILE(2) OVER (ORDER BY R ASC)  AS r_bucket,   -- 1 = R 近
           NTILE(2) OVER (ORDER BY F DESC) AS f_bucket,   -- 1 = F 高
           NTILE(2) OVER (ORDER BY M DESC) AS m_bucket    -- 1 = M 高
    FROM rfm
)
SELECT CASE WHEN r_bucket = 1 THEN 'R高' ELSE 'R低' END AS R层,
       CASE WHEN f_bucket = 1 THEN 'F高' ELSE 'F低' END AS F层,
       CASE WHEN m_bucket = 1 THEN 'M高' ELSE 'M低' END AS M层,
       COUNT(*) AS 人数
FROM b
GROUP BY R层, F层, M层
ORDER BY 人数 DESC;

-- Q4.4 用业务经验值重做（推荐版本）
-- R<=3 为近；F>=2 为复购；M 取中位数 6
WITH rfm AS (
    SELECT user_id,
           CAST(julianday('2017-12-03')
                - julianday(MAX(CASE WHEN behavior = 'buy' THEN date(dt) END)) AS INTEGER) AS R,
           SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) AS F,
           COUNT(*) AS M
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id
    HAVING SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) > 0
),
med AS (
    SELECT MIN(M) AS m
    FROM (SELECT M, NTILE(2) OVER (ORDER BY M ASC) AS b FROM rfm)
    WHERE b = 2
)
SELECT CASE WHEN R <= 3 THEN 'R近' ELSE 'R远' END                       AS R层,
       CASE WHEN F >= 2 THEN 'F复购' ELSE 'F一次性' END                 AS F层,
       CASE WHEN M >= (SELECT m FROM med) THEN 'M高' ELSE 'M低' END     AS M层,
       COUNT(*) AS 人数,
       ROUND(COUNT(*) * 1.0 / (SELECT COUNT(*) FROM rfm), 4) AS 占比
FROM rfm
GROUP BY R层, F层, M层
ORDER BY 人数 DESC;
