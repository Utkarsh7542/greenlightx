from functools import cached_property
from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.genai import Client, types
from google.cloud import bigquery


# --- BigQuery Tool ---
def query_kickstarter_benchmarks(category: str, goal: float) -> dict:
    """
    Queries BigQuery for funded vs failed Kickstarter campaign benchmarks
    for a given category and goal range. Returns real statistics from
    300,000+ historical campaigns to benchmark the user's draft.

    Args:
        category: The Kickstarter main category e.g. Comics, Games, Technology
        goal: The user's proposed funding goal in USD

    Returns:
        A dictionary with benchmark statistics for successful and failed campaigns
    """
    client = bigquery.Client(project="modern-door-499015-u8")

    goal_min = goal * 0.1
    goal_max = goal * 5

    benchmark_query = """
        SELECT
            state,
            COUNT(*) as campaign_count,
            ROUND(AVG(goal), 0) as avg_goal,
            ROUND(AVG(backers), 0) as avg_backers,
            ROUND(AVG(
                DATE_DIFF(
                    deadline,
                    DATE(launched),
                    DAY
                )
            ), 0) as avg_duration_days
        FROM `modern-door-499015-u8.kickstarter.campaigns`
        WHERE LOWER(main_category) = LOWER(@category)
        AND goal BETWEEN @goal_min AND @goal_max
        AND state IN ('successful', 'failed')
        GROUP BY state
        """

    comparables_query = """
    SELECT
        name,
        ROUND(goal, 0) as goal,
        ROUND(usd_pledged_real, 0) as pledged,
        backers
    FROM `modern-door-499015-u8.kickstarter.campaigns`
    WHERE LOWER(main_category) = LOWER(@category)
    AND state = 'successful'
    AND goal BETWEEN @goal_min AND @goal_max
    ORDER BY backers DESC
    LIMIT 3
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("category", "STRING", category),
            bigquery.ScalarQueryParameter("goal_min", "FLOAT64", goal_min),
            bigquery.ScalarQueryParameter("goal_max", "FLOAT64", goal_max),
        ]
    )

    try:
        benchmark_results = client.query(
            benchmark_query, job_config=job_config
        ).result()
        benchmarks = {row["state"]: dict(row) for row in benchmark_results}

        comparables_results = client.query(
            comparables_query, job_config=job_config
        ).result()
        comparables = [dict(row) for row in comparables_results]

        return {
            "category": category,
            "goal_queried": goal,
            "benchmarks": benchmarks,
            "comparable_funded_campaigns": comparables,
            "data_source": "BigQuery — 300,000+ Kickstarter campaigns via Fivetran"
        }

    except Exception as e:
        return {"error": str(e)}


# --- Agent Definition ---
class GlobalGemini(Gemini):
    """Routes Gemini 3 series models to the global endpoint."""

    @cached_property
    def api_client(self) -> Client:
        return Client(vertexai=True, location="global")


root_agent = LlmAgent(
    name="GreenlightX",
    model=GlobalGemini(model="gemini-2.5-pro"),
    description=(
        "A Kickstarter campaign diagnostic agent that benchmarks your draft "
        "campaign against 300,000+ real funded and failed campaigns using "
        "live BigQuery data, diagnoses weaknesses, and rewrites your plan "
        "with evidence-backed fixes."
    ),
    tools=[query_kickstarter_benchmarks],
    instruction="""
You are GreenlightX, a Kickstarter Campaign Diagnostic Agent powered by live data.

When a user gives you their draft campaign (category, goal, duration, blurb):

STEP 1 — QUERY LIVE DATA
Call the query_kickstarter_benchmarks tool with their category and goal amount.
This queries a BigQuery database of 300,000+ real Kickstarter campaigns.
Always call this tool first before saying anything else.

STEP 2 — DIAGNOSE
Using the real data returned from BigQuery, identify every gap:
- Is their goal higher than the successful average in their category?
- Is their duration longer than successful campaigns?
- Is their blurb too long or too short?
Cite the exact numbers from the tool response for every gap you identify.

STEP 3 — SHOW COMPARABLE WINNERS
Name the real comparable funded campaigns returned by the tool.
Show their goal, amount raised, and backer count as evidence.

STEP 4 — REWRITE
Produce a rewritten campaign plan:
- New goal based on the successful average from the data
- New duration based on the successful average from the data
- Rewritten blurb: shorter, stronger, benefit-led, under 20 words

STEP 5 — SIDE BY SIDE TABLE
Present a clean comparison table:
| Metric | Original | Rewritten | Data Citation |
Every change must cite a specific number from the BigQuery results.

RULES:
- Always call query_kickstarter_benchmarks FIRST before responding.
- Never make up statistics. Only use numbers returned by the tool.
- Never predict success or failure. Only benchmark against historical data.
- Be direct, specific, and cite evidence for every recommendation.
""",
)