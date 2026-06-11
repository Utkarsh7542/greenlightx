from flask import Flask, request, jsonify, send_from_directory
from google.cloud import bigquery
import vertexai
from vertexai.generative_models import GenerativeModel
import os

app = Flask(__name__, static_folder='static')

vertexai.init(project="modern-door-499015-u8", location="global")
model = GenerativeModel("gemini-3.5-flash")

def query_kickstarter_benchmarks(category, goal):
    client = bigquery.Client(project="modern-door-499015-u8")
    goal_min = float(goal) * 0.1
    goal_max = float(goal) * 5

    benchmark_query = """
    SELECT state, COUNT(*) as count,
        ROUND(AVG(goal), 0) as avg_goal,
        ROUND(AVG(backers), 0) as avg_backers,
        ROUND(AVG(DATE_DIFF(deadline, DATE(launched), DAY)), 0) as avg_duration
    FROM `modern-door-499015-u8.kickstarter.campaigns`
    WHERE LOWER(main_category) = LOWER(@category)
    AND goal BETWEEN @goal_min AND @goal_max
    AND state IN ('successful', 'failed')
    GROUP BY state
    """

    comparables_query = """
    SELECT name, ROUND(goal,0) as goal,
        ROUND(usd_pledged_real,0) as pledged, backers
    FROM `modern-door-499015-u8.kickstarter.campaigns`
    WHERE LOWER(main_category) = LOWER(@category)
    AND state = 'successful'
    AND goal BETWEEN @goal_min AND @goal_max
    ORDER BY backers DESC LIMIT 3
    """

    job_config = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter("category", "STRING", category),
        bigquery.ScalarQueryParameter("goal_min", "FLOAT64", goal_min),
        bigquery.ScalarQueryParameter("goal_max", "FLOAT64", goal_max),
    ])

    benchmarks = {}
    for row in client.query(benchmark_query, job_config=job_config).result():
        benchmarks[row["state"]] = dict(row)

    comparables = []
    for row in client.query(comparables_query, job_config=job_config).result():
        comparables.append(dict(row))

    return benchmarks, comparables

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/diagnose', methods=['POST'])
def diagnose():
    data = request.get_json()
    category = data.get('category', '')
    goal = data.get('goal', 0)
    duration = data.get('duration', 0)
    blurb = data.get('blurb', '')

    try:
        benchmarks, comparables = query_kickstarter_benchmarks(category, goal)

        prompt = f"""You are GreenlightX, a Kickstarter Campaign Diagnostic Agent.

A creator has shared their draft campaign. You have just queried a BigQuery database 
of 300,000+ real Kickstarter campaigns and retrieved this live data:

THEIR DRAFT:
- Category: {category}
- Goal: ${goal}
- Duration: {duration} days
- Blurb: {blurb}

LIVE BIGQUERY DATA FOR '{category}' CAMPAIGNS:
{benchmarks}

REAL COMPARABLE FUNDED CAMPAIGNS:
{comparables}

Now do the following:

1. DIAGNOSE: Identify every gap between their draft and what successful campaigns look like.
   Cite exact numbers from the BigQuery data above.

2. COMPARABLE WINNERS: Name the real funded campaigns from the data above with their goals 
   and backer counts.

3. REWRITE: Give them a new goal, new duration, and rewritten blurb based on the data.

4. SIDE BY SIDE TABLE:
| Metric | Original | Rewritten | Data Citation |
Every change must cite a specific number from the BigQuery results.

Never predict success or failure. Only benchmark against historical data.
Be direct and specific."""

        response = model.generate_content(prompt)
        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)