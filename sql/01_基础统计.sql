-- ============================================================
-- 01_基础统计.sql · A 组：把大盘描述清楚
-- 口径：
--   PV  = 浏览次数（同一用户多次浏览计多次）
--   UV  = 当日有 pv 行为的去重用户数
--   DAU = 当日有任意行为的去重用户数（DAU >= UV）
-- 注意：SQLite 整数除法会截断，比值一律 * 1.0
-- ============================================================

-- Q1.1 每日 PV / UV；Q1.3 人均访问次数（PV / UV）
SELECT date(dt)                                              AS 日期,
       COUNT(*)                                              AS pv,
       COUNT(DISTINCT user_id)                               AS uv,
       ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT user_id), 2)    AS 人均访问次数
FROM user_behavior
WHERE behavior = 'pv'
  AND date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
GROUP BY date(dt)
ORDER BY 日期;

-- Q1.2 DAU：当日有任意行为（pv/cart/fav/buy 任一）的去重用户数
-- 注：不加 behavior 条件；同一用户当天多条行为只计 1
SELECT date(dt)                  AS 日期,
       COUNT(DISTINCT user_id)   AS dau
FROM user_behavior
WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
GROUP BY date(dt)
ORDER BY 日期;

-- Q1.2 对照：DAU 与 UV 的差额 = 当天只加购/收藏/购买、没有浏览的用户
SELECT d.日期,
       d.dau,
       u.uv,
       d.dau - u.uv AS 差额
FROM (
    SELECT date(dt) AS 日期, COUNT(DISTINCT user_id) AS dau
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY date(dt)
) d
JOIN (
    SELECT date(dt) AS 日期, COUNT(DISTINCT user_id) AS uv
    FROM user_behavior
    WHERE behavior = 'pv'
      AND date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY date(dt)
) u ON d.日期 = u.日期
ORDER BY d.日期;
