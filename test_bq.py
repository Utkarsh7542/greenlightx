from google.cloud import bigquery

client = bigquery.Client(project="modern-door-499015-u8")

query = """
SELECT
    state,
    COUNT(*) as campaign_count,
    ROUND(AVG(goal), 0) as avg_goal,
    ROUND(AVG(backers), 0) as avg_backers
FROM `modern-door-499015-u8.kickstarter.campaigns`
WHERE LOWER(main_category) = LOWER('Comics')
AND goal BETWEEN 2500 AND 125000
AND state IN ('successful', 'failed')
GROUP BY state
"""

results = client.query(query).result()
for row in results:
    print(dict(row))