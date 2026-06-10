from fivetran_connector_sdk import Connector, Operations as op
import pandas as pd
import os

def schema(configuration):
    return [
        {
            "table": "campaigns",
            "primary_key": ["id"],
            "columns": {
                "id": "STRING",
                "name": "STRING",
                "category": "STRING",
                "main_category": "STRING",
                "goal": "FLOAT",
                "pledged": "FLOAT",
                "backers_count": "INT",
                "blurb": "STRING",
                "duration_days": "INT",
                "state": "STRING",
                "launched": "STRING",
                "country": "STRING"
            }
        }
    ]

def update(configuration, state):
    csv_path = os.path.join(os.path.dirname(__file__), "..", "ks-projects-201801.csv")
    df = pd.read_csv(csv_path, encoding="latin-1")
    
    # Clean up
    df = df.dropna(subset=["ID", "state", "goal"])
    df = df[df["state"].isin(["successful", "failed"])]
    
    # Calculate duration
    df["launched"] = pd.to_datetime(df["launched"], errors="coerce")
    df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")
    df["duration_days"] = (df["deadline"] - df["launched"]).dt.days.fillna(30).astype(int)
    
    count = 0
    for _, row in df.iterrows():
        yield op.upsert("campaigns", {
            "id": str(row["ID"]),
            "name": str(row["name"])[:500] if pd.notna(row["name"]) else "",
            "category": str(row["category"]) if pd.notna(row["category"]) else "",
            "main_category": str(row["main_category"]) if pd.notna(row["main_category"]) else "",
            "goal": float(row["goal"]),
            "pledged": float(row["usd pledged"]) if pd.notna(row["usd pledged"]) else 0.0,
            "backers_count": int(row["backers"]) if pd.notna(row["backers"]) else 0,
            "blurb": "",
            "duration_days": int(row["duration_days"]),
            "state": str(row["state"]),
            "launched": str(row["launched"]),
            "country": str(row["country"]) if pd.notna(row["country"]) else ""
        })
        count += 1
        if count % 10000 == 0:
            print(f"Processed {count} rows...")

    yield op.checkpoint(state={})

connector = Connector(update=update, schema=schema)

if __name__ == "__main__":
    connector.debug()