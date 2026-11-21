-- ============================================================
-- 02_漏斗.sql · B 组：用户卡在哪一步
-- 方法：先把每个用户压成一行（MAX + CASE WHEN），再对外层 SUM 统计人数
-- 口径：
--   独立计数 = 做过该行为就算
--   嵌套计数 = 上一层和这一层都做过（转化率分子必须含于分母）
-- 重要：加购与收藏是并行的意向行为，不构成"加购→收藏"漏斗
-- ============================================================

-- Q2.1 四层独立计数：浏览 / 加购 / 收藏 / 购买
WITH per_user AS (
    SELECT user_id,
           MAX(CASE WHEN behavior = 'pv'   THEN 1 ELSE 0 END) AS has_pv,
           MAX(CASE WHEN behavior = 'cart' THEN 1 ELSE 0 END) AS has_cart,
           MAX(CASE WHEN behavior = 'fav'  THEN 1 ELSE 0 END) AS has_fav,
           MAX(CASE WHEN behavior = 'buy'  THEN 1 ELSE 0 END) AS has_buy
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id
)
SELECT SUM(has_pv)   AS 浏览人数,
       SUM(has_cart) AS 加购人数,
       SUM(has_fav)  AS 收藏人数,
       SUM(has_buy)  AS 购买人数
FROM per_user;

-- Q2.2 口径 A：相对第一层（分母均为浏览人数）
WITH per_user AS (
    SELECT user_id,
           MAX(CASE WHEN behavior = 'pv'   THEN 1 ELSE 0 END) AS has_pv,
           MAX(CASE WHEN behavior = 'cart' THEN 1 ELSE 0 END) AS has_cart,
           MAX(CASE WHEN behavior = 'fav'  THEN 1 ELSE 0 END) AS has_fav,
           MAX(CASE WHEN behavior = 'buy'  THEN 1 ELSE 0 END) AS has_buy
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id
)
SELECT ROUND(SUM(CASE WHEN has_pv = 1 AND has_cart = 1 THEN 1 ELSE 0 END) * 1.0
             / SUM(has_pv), 4) AS 浏览_加购,
       ROUND(SUM(CASE WHEN has_pv = 1 AND has_fav = 1 THEN 1 ELSE 0 END) * 1.0
             / SUM(has_pv), 4) AS 浏览_收藏,
       ROUND(SUM(CASE WHEN has_pv = 1 AND has_buy = 1 THEN 1 ELSE 0 END) * 1.0
             / SUM(has_pv), 4) AS 浏览_购买
FROM per_user;

-- Q2.2 口径 B：相对上一层
WITH per_user AS (
    SELECT user_id,
           MAX(CASE WHEN behavior = 'cart' THEN 1 ELSE 0 END) AS has_cart,
           MAX(CASE WHEN behavior = 'fav'  THEN 1 ELSE 0 END) AS has_fav,
           MAX(CASE WHEN behavior = 'buy'  THEN 1 ELSE 0 END) AS has_buy
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id
)
SELECT ROUND(SUM(CASE WHEN has_cart = 1 AND has_fav = 1 THEN 1 ELSE 0 END) * 1.0
             / SUM(has_cart), 4) AS 加购_收藏,
       ROUND(SUM(CASE WHEN has_fav = 1 AND has_buy = 1 THEN 1 ELSE 0 END) * 1.0
             / SUM(has_fav), 4)  AS 收藏_购买
FROM per_user;

-- Q2.4 加购与收藏，哪个更接近购买
WITH per_user AS (
    SELECT user_id,
           MAX(CASE WHEN behavior = 'cart' THEN 1 ELSE 0 END) AS has_cart,
           MAX(CASE WHEN behavior = 'fav'  THEN 1 ELSE 0 END) AS has_fav,
           MAX(CASE WHEN behavior = 'buy'  THEN 1 ELSE 0 END) AS has_buy
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id
)
SELECT ROUND(SUM(CASE WHEN has_cart = 1 AND has_buy = 1 THEN 1 ELSE 0 END) * 1.0
             / SUM(has_cart), 4) AS 加购_购买,
       ROUND(SUM(CASE WHEN has_fav = 1 AND has_buy = 1 THEN 1 ELSE 0 END) * 1.0
             / SUM(has_fav), 4)  AS 收藏_购买
FROM per_user;

-- Q2.5 修正漏斗：把「加购或收藏」合并为"意向"层
WITH per_user AS (
    SELECT user_id,
           MAX(CASE WHEN behavior = 'pv'            THEN 1 ELSE 0 END) AS has_pv,
           MAX(CASE WHEN behavior IN ('cart','fav') THEN 1 ELSE 0 END) AS has_intent,
           MAX(CASE WHEN behavior = 'buy'           THEN 1 ELSE 0 END) AS has_buy
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id
)
SELECT SUM(has_pv)                                                       AS 浏览,
       SUM(CASE WHEN has_pv = 1 AND has_intent = 1 THEN 1 ELSE 0 END)    AS 意向,
       SUM(CASE WHEN has_pv = 1 AND has_intent = 1 AND has_buy = 1
                THEN 1 ELSE 0 END)                                       AS 购买,
       ROUND(SUM(CASE WHEN has_pv = 1 AND has_intent = 1 THEN 1 ELSE 0 END) * 1.0
             / SUM(has_pv), 4)                                           AS 浏览_意向,
       ROUND(SUM(CASE WHEN has_pv = 1 AND has_intent = 1 AND has_buy = 1
                      THEN 1 ELSE 0 END) * 1.0
             / SUM(CASE WHEN has_pv = 1 AND has_intent = 1 THEN 1 ELSE 0 END), 4) AS 意向_购买
FROM per_user;

-- Q2.5 补充：购买路径拆分（漏斗只覆盖 34.6% 的购买者）
WITH per_user AS (
    SELECT user_id,
           MAX(CASE WHEN behavior = 'pv'            THEN 1 ELSE 0 END) AS has_pv,
           MAX(CASE WHEN behavior IN ('cart','fav') THEN 1 ELSE 0 END) AS has_intent,
           MAX(CASE WHEN behavior = 'buy'           THEN 1 ELSE 0 END) AS has_buy
    FROM user_behavior
    WHERE date(dt) BETWEEN '2017-11-25' AND '2017-12-03'
    GROUP BY user_id
)
SELECT SUM(CASE WHEN has_pv = 1 AND has_intent = 1 AND has_buy = 1 THEN 1 ELSE 0 END) AS 标准漏斗,
       SUM(CASE WHEN has_pv = 1 AND has_intent = 0 AND has_buy = 1 THEN 1 ELSE 0 END) AS 浏览后直接购买,
       SUM(CASE WHEN has_pv = 0 AND has_intent = 1 AND has_buy = 1 THEN 1 ELSE 0 END) AS 无浏览有意向购买,
       SUM(CASE WHEN has_pv = 0 AND has_intent = 0 AND has_buy = 1 THEN 1 ELSE 0 END) AS 无浏览直接购买
FROM per_user;
