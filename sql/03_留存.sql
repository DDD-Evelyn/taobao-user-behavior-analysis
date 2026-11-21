-- ============================================================
-- 03_留存.sql · C 组：用户还回来吗
-- 口径：
--   次日留存率 = 当日新增用户中，次自然日（+1 day）有任意行为的比例
--   新增用户   = 数据窗口内"首次出现"的用户（不是真实注册）
-- 注意：
--   1) 11-25 的"新增"混入老用户（首日污染）
--   2) 12-03 的次日为 12-04，数据不可观测，须剔除
--   3) 7 日留存只有 11-25、11-26 两批可算
-- ============================================================

-- Q3.2 每日新增用户（每个用户取首次出现日期，再按该日期计数）
SELECT first_day        AS 首次日期,
       COUNT(*)         AS 新增用户
FROM (
    SELECT user_id, MIN(date(dt)) AS first_day
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id
)
GROUP BY first_day
ORDER BY first_day;

-- Q3.3 次日留存率（按首次日期分批）
WITH pu AS (
    SELECT user_id, MIN(date(dt)) AS first_day
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id
),
act AS (
    SELECT DISTINCT user_id, date(dt) AS d
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
)
SELECT p.first_day AS 首次日期,
       COUNT(*)    AS 新增,
       SUM(CASE WHEN a.d IS NOT NULL THEN 1 ELSE 0 END) AS 次日留存人数,
       ROUND(SUM(CASE WHEN a.d IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS 次日留存率
FROM pu p
LEFT JOIN act a
       ON a.user_id = p.user_id
      AND a.d = date(p.first_day, '+1 day')
GROUP BY p.first_day
HAVING p.first_day < '2017-12-03'      -- 12-03 的次日不可观测，剔除
ORDER BY p.first_day;

-- Q3.4 7 日留存率（只保留"首次日期 + 7 天"仍在窗口内的批次）
WITH pu AS (
    SELECT user_id, MIN(date(dt)) AS first_day
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id
),
act AS (
    SELECT DISTINCT user_id, date(dt) AS d
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
)
SELECT p.first_day AS 首次日期,
       COUNT(*)    AS 新增,
       SUM(CASE WHEN a.d IS NOT NULL THEN 1 ELSE 0 END) AS 七日留存人数,
       ROUND(SUM(CASE WHEN a.d IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS 七日留存率
FROM pu p
LEFT JOIN act a
       ON a.user_id = p.user_id
      AND a.d = date(p.first_day, '+7 day')
GROUP BY p.first_day
HAVING date(p.first_day, '+7 day') <= '2017-12-03'
ORDER BY p.first_day;
