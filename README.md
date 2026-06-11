# GreenlightX
### Kickstarter Campaign Diagnostic Agent

Paste your draft campaign. Get an evidence-backed rewrite before you launch.

Built for the Google Cloud Rapid Agent Hackathon — Fivetran Track, June 2026.

## What it does
GreenlightX benchmarks your draft Kickstarter campaign against 300,000+ 
real funded and failed campaigns, diagnoses where your plan is weak, 
and rewrites it with specific evidence-backed fixes.

## Stack
- Gemini (Google Cloud Vertex AI)
- Google ADK
- Fivetran Connector SDK (custom Kickstarter connector)
- Fivetran MCP Server
- Google BigQuery
- Google Cloud Run
- Python / Flask

## Partner Integration (Fivetran)
Fivetran moves the Kickstarter dataset into BigQuery via a custom 
Connector SDK connector. The Fivetran MCP Server is integrated so 
the agent can trigger and check data syncs during execution.

## Live Demo
https://greenlightx-841673981611.us-central1.run.app

## License
MIT