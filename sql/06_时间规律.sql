-- ============================================================
-- 06_时间规律.sql · F 组：什么时候最该触达
-- 说明：dt 为北京时间；strftime('%H') 取小时，'%w' 取星期（0=周日）
-- ============================================================

-- Q6.1 一天中哪个小时最活跃（按行为类型分别看）
SELECT strftime('%H', dt) AS 小时,
       behavior           AS 行为,
       COUNT(*)           AS 次数
FROM user_behavior
WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
GROUP BY 小时, 行为
ORDER BY 小时, 行为;

-- Q6.1 补充：各小时的购买强度（购买数 / 浏览数）
SELECT strftime('%H', dt) AS 小时,
       SUM(CASE WHEN behavior = 'pv'  THEN 1 ELSE 0 END) AS pv,
       SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) AS buy,
       ROUND(SUM(CASE WHEN behavior = 'buy' THEN 1 ELSE 0 END) * 1.0
             / SUM(CASE WHEN behavior = 'pv' THEN 1 ELSE 0 END), 4) AS 购买强度
FROM user_behavior
WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
GROUP BY 小时
ORDER BY 小时;

-- Q6.2 一周中哪天最活跃（用日均，避免周六周日各出现 2 天造成不公平）
SELECT CASE WHEN strftime('%w', dt) = '0' THEN '7'
            ELSE strftime('%w', dt) END AS 星期序号,
       COUNT(*)                          AS 总量,
       COUNT(DISTINCT date(dt))          AS 天数,
       ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT date(dt)), 0) AS 日均
FROM user_behavior
WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
GROUP BY 星期序号
ORDER BY CAST(星期序号 AS INTEGER);

-- Q6.3 小时 × 星期 交叉表（交给 Python 画热力图）
SELECT CASE WHEN strftime('%w', dt) = '0' THEN '7'
            ELSE strftime('%w', dt) END AS 星期序号,
       strftime('%H', dt) AS 小时,
       COUNT(*)           AS 次数
FROM user_behavior
WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
GROUP BY 星期序号, 小时
ORDER BY CAST(星期序号 AS INTEGER), 小时;
