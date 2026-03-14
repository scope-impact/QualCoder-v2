-- Firebase Analytics → Participant Profile CSV
-- =============================================
-- Run this query in BigQuery console, then export result as CSV.
-- The output CSV can be imported directly into QualCoder as Case attributes.
--
-- Instructions:
--   1. Replace YOUR_DATASET with your Firebase Analytics dataset (e.g., analytics_123456789)
--   2. Replace YYYYMMDD date range with your study period
--   3. Run in BigQuery console
--   4. Export results as CSV
--   5. Upload CSV to S3 (or import directly into QualCoder)
--
-- Output columns:
--   participant_id  — Firebase user pseudo ID (maps to Case name)
--   sessions        — Total session count (NUMBER)
--   total_events    — Total event count (NUMBER)
--   first_seen      — First event date (DATE)
--   last_seen       — Last event date (DATE)
--   top_event       — Most frequent event name (TEXT)
--   country         — Most common country (TEXT)
--   device_category — Most common device type: mobile/desktop/tablet (TEXT)
--   platform        — Most common platform: ANDROID/IOS/WEB (TEXT)

SELECT
  user_pseudo_id AS participant_id,

  -- Session count (unique ga_session_id values)
  COUNT(DISTINCT
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
  ) AS sessions,

  -- Total events
  COUNT(*) AS total_events,

  -- Date range
  MIN(PARSE_DATE('%Y%m%d', event_date)) AS first_seen,
  MAX(PARSE_DATE('%Y%m%d', event_date)) AS last_seen,

  -- Most frequent event (excluding session lifecycle events)
  APPROX_TOP_COUNT(
    IF(event_name NOT IN ('session_start', 'first_visit', 'first_open', 'user_engagement'),
       event_name, NULL),
    1
  )[SAFE_OFFSET(0)].value AS top_event,

  -- Demographics
  APPROX_TOP_COUNT(geo.country, 1)[SAFE_OFFSET(0)].value AS country,
  APPROX_TOP_COUNT(device.category, 1)[SAFE_OFFSET(0)].value AS device_category,
  APPROX_TOP_COUNT(platform, 1)[SAFE_OFFSET(0)].value AS platform

FROM `YOUR_DATASET.events_*`

WHERE
  _TABLE_SUFFIX BETWEEN '20260101' AND '20260331'
  AND user_pseudo_id IS NOT NULL

GROUP BY user_pseudo_id

-- Filter out users with minimal activity
HAVING sessions >= 1

ORDER BY sessions DESC
