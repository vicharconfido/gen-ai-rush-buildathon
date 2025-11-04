# Retell Monthly Usage API

This project exposes a lightweight FastAPI service that aggregates monthly usage metrics from the Retell API. It acts as a thin
proxy that handles authentication, query parameter validation, and response normalization so downstream systems can consume cons
istent analytics data.

## Features

- ✅ Simple REST endpoint (`GET /usage/monthly`) to fetch usage for a given month
- ✅ JSON POST endpoint (`POST /usage/monthly/query`) that accepts an API key and month in the request body
- ✅ Built-in web interface at `/` where you can paste a Retell API key, pick a month, and visualize total hours
- ✅ Automatic month boundary calculation based on the requested year and month
- ✅ Pluggable configuration via environment variables (`RETELL_API_KEY`, `RETELL_BASE_URL`, `RETELL_TIMEOUT_SECONDS`)
- ✅ Graceful error handling when the upstream Retell API is unavailable or returns unexpected data
- ✅ Docker-friendly dependency list via `requirements.txt`

## Getting Started

1. **Create a virtual environment and install dependencies:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **(Optional) Set default environment variables:**

   ```bash
   export RETELL_API_KEY="your_retell_api_key"
   # Optional overrides
   export RETELL_BASE_URL="https://api.retellai.com/v2"
   export RETELL_TIMEOUT_SECONDS=10
   ```

   Supplying `RETELL_API_KEY` allows the service to call Retell without the client providing a key on each request. If it is not
   set, callers must provide `api_key` on `GET /usage/monthly` or `retell_api_key` in `POST /usage/monthly/query`.

3. **Run the API locally:**

   From the repository root you can launch the server directly with a fully
   qualified module path:

   ```bash
   uvicorn retell_usage_api.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Alternatively, `cd retell_usage_api` and then run `uvicorn app.main:app --reload`.

4. **Use the web explorer:**

   Visit [http://localhost:8000/](http://localhost:8000/) and enter a month plus your Retell API key. The page summarizes total
   usage hours and exposes the full JSON response from Retell.

5. **Call the monthly usage endpoint programmatically:**

   ```bash
   curl "http://localhost:8000/usage/monthly?year=2024&month=5&api_key=retell_live_xxx"
   ```

   Include `team_id=...` if you need to scope the query to a specific Retell team.

   Or send JSON to the POST helper:

   ```bash
   curl -X POST http://localhost:8000/usage/monthly/query \
     -H "Content-Type: application/json" \
     -d '{"month": "2024-05", "retell_api_key": "retell_live_xxx"}'
   ```

6. **Health check:**

   ```bash
   curl http://localhost:8000/health
   ```

## Response Format

The API normalizes the upstream response into the following structure:

```json
{
  "month": "2024-05",
  "metrics": [
    {
      "period_start": "2024-05-01",
      "period_end": "2024-05-31",
      "value": 123.45,
      "raw": { "minutes": 123.45, "start_date": "2024-05-01", "end_date": "2024-05-31" }
    }
  ],
  "source_payload": { "data": [...] }
}
```

`value` is inferred from common Retell metric keys (`value`, `minutes`, or `count`) but the raw payload is preserved for custom
processing needs.

## Testing Notes

The service relies on the live Retell API. To run unit tests without hitting the upstream service, you can mock the `UsageServic
e` or `RetellClient` classes.
