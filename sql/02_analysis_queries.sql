-- 1. Monthly creator ecosystem scorecard
SELECT
    performance_month,
    COUNT(DISTINCT CASE WHEN uploads > 0 THEN creator_id END) AS active_creators,
    SUM(uploads) AS total_uploads,
    SUM(views) AS total_views,
    ROUND(SUM(watch_hours), 1) AS total_watch_hours,
    SUM(new_subscribers) AS new_subscribers
FROM monthly_performance
GROUP BY performance_month
ORDER BY performance_month;

-- 2. Full-year performance by region
SELECT
    c.region,
    COUNT(DISTINCT c.creator_id) AS creators,
    COUNT(DISTINCT CASE WHEN p.uploads > 0 THEN p.creator_id END) AS active_creators,
    SUM(p.uploads) AS uploads,
    SUM(p.views) AS views,
    ROUND(SUM(p.watch_hours), 1) AS watch_hours,
    SUM(p.new_subscribers) AS new_subscribers
FROM creators AS c
JOIN monthly_performance AS p
    ON c.creator_id = p.creator_id
GROUP BY c.region
ORDER BY views DESC;

-- 3. Creator performance by partner tier
SELECT
    c.partner_tier,
    COUNT(DISTINCT c.creator_id) AS creators,
    ROUND(AVG(p.uploads), 2) AS avg_monthly_uploads,
    ROUND(AVG(p.views), 0) AS avg_monthly_views,
    ROUND(AVG(p.watch_hours), 1) AS avg_monthly_watch_hours,
    ROUND(AVG(p.new_subscribers), 1) AS avg_monthly_new_subscribers
FROM creators AS c
JOIN monthly_performance AS p
    ON c.creator_id = p.creator_id
GROUP BY c.partner_tier
ORDER BY avg_monthly_views DESC;

-- 4. Support operations by case type
SELECT
    case_type,
    COUNT(*) AS cases,
    ROUND(AVG(resolution_hours), 1) AS avg_resolution_hours,
    ROUND(AVG(first_contact_resolved) * 100, 1) AS first_contact_resolution_pct,
    ROUND(AVG(satisfaction_score), 2) AS avg_satisfaction
FROM support_cases
WHERE case_status = 'Closed'
GROUP BY case_type
ORDER BY cases DESC;

-- 5. Creator-level view growth and support demand
WITH performance AS (
    SELECT
        creator_id,
        AVG(CASE WHEN performance_month BETWEEN '2025-01' AND '2025-06' THEN views END) AS first_half_views,
        AVG(CASE WHEN performance_month BETWEEN '2025-07' AND '2025-12' THEN views END) AS second_half_views,
        SUM(CASE WHEN uploads > 0 THEN 1 ELSE 0 END) AS active_months
    FROM monthly_performance
    GROUP BY creator_id
),
support AS (
    SELECT
        creator_id,
        COUNT(*) AS support_cases,
        AVG(resolution_hours) AS avg_resolution_hours
    FROM support_cases
    GROUP BY creator_id
)
SELECT
    c.creator_id,
    c.region,
    c.category,
    c.partner_tier,
    p.active_months,
    ROUND((p.second_half_views - p.first_half_views) * 100.0 /
        NULLIF(p.first_half_views, 0), 1) AS view_growth_pct,
    COALESCE(s.support_cases, 0) AS support_cases,
    ROUND(s.avg_resolution_hours, 1) AS avg_resolution_hours
FROM creators AS c
JOIN performance AS p
    ON c.creator_id = p.creator_id
LEFT JOIN support AS s
    ON c.creator_id = s.creator_id
ORDER BY view_growth_pct DESC;

-- 6. Year-end active retention by partner tier
WITH january AS (
    SELECT creator_id
    FROM monthly_performance
    WHERE performance_month = '2025-01' AND uploads > 0
),
december AS (
    SELECT creator_id
    FROM monthly_performance
    WHERE performance_month = '2025-12' AND uploads > 0
)
SELECT
    c.partner_tier,
    COUNT(DISTINCT j.creator_id) AS january_active_creators,
    COUNT(DISTINCT d.creator_id) AS retained_in_december,
    ROUND(COUNT(DISTINCT d.creator_id) * 100.0 /
        NULLIF(COUNT(DISTINCT j.creator_id), 0), 1) AS year_end_retention_pct
FROM january AS j
JOIN creators AS c
    ON j.creator_id = c.creator_id
LEFT JOIN december AS d
    ON j.creator_id = d.creator_id
GROUP BY c.partner_tier
ORDER BY year_end_retention_pct DESC;
