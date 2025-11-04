from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from .dependencies import get_usage_service
from .schemas import (
    MonthlyUsageQuery,
    MonthlyUsageResponse,
    UsageMetric,
)
from .services.retell_client import RetellAPIError
from .services.usage_service import UsageService

app = FastAPI(title="Retell Usage API", version="1.1.0")


INDEX_HTML = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Retell Monthly Usage</title>
  <style>
    :root {
      color-scheme: light dark;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background-color: #f5f5f5;
    }
    body {
      margin: 0;
      padding: 2rem;
      display: flex;
      justify-content: center;
    }
    main {
      width: min(720px, 100%);
      background: white;
      border-radius: 12px;
      box-shadow: 0 20px 60px rgba(15, 23, 42, 0.12);
      padding: 2.5rem;
    }
    h1 {
      margin-top: 0;
      font-size: 2rem;
    }
    form {
      display: grid;
      gap: 1rem;
      margin-bottom: 2rem;
    }
    label {
      font-weight: 600;
      display: grid;
      gap: 0.4rem;
    }
    input[type="month"],
    input[type="text"],
    input[type="password"] {
      padding: 0.7rem 0.9rem;
      border: 1px solid rgba(148, 163, 184, 0.7);
      border-radius: 8px;
      font-size: 1rem;
    }
    button {
      padding: 0.75rem 1.2rem;
      font-size: 1rem;
      border-radius: 999px;
      border: none;
      background: #2563eb;
      color: white;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s ease;
    }
    button:hover {
      background: #1d4ed8;
    }
    .result-card {
      background: rgba(37, 99, 235, 0.08);
      border-radius: 12px;
      padding: 1.5rem;
      display: grid;
      gap: 0.8rem;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th, td {
      text-align: left;
      padding: 0.5rem 0.25rem;
      border-bottom: 1px solid rgba(148, 163, 184, 0.4);
    }
    pre {
      background: #0f172a;
      color: #e2e8f0;
      padding: 1rem;
      border-radius: 8px;
      overflow-x: auto;
    }
    #status {
      font-weight: 600;
      min-height: 1.5rem;
    }
    @media (max-width: 600px) {
      body {
        padding: 1rem;
      }
      main {
        padding: 1.5rem;
      }
    }
  </style>
</head>
<body>
  <main>
    <h1>Retell Monthly Usage Explorer</h1>
    <p>Enter a billing month and your Retell API key to fetch voice usage minutes and a detailed breakdown.</p>
    <form id=\"usage-form\">
      <label>
        Month
        <input type=\"month\" name=\"month\" required />
      </label>
      <label>
        Retell API Key
        <input type=\"password\" name=\"api_key\" autocomplete=\"off\" required />
      </label>
      <label>
        Team ID (optional)
        <input type=\"text\" name=\"team_id\" placeholder=\"team_123\" />
      </label>
      <button type=\"submit\">Fetch usage</button>
    </form>
    <div id=\"status\"></div>
    <section id=\"results\"></section>
  </main>
  <script>
    const form = document.getElementById("usage-form");
    const status = document.getElementById("status");
    const results = document.getElementById("results");

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      results.innerHTML = "";
      status.textContent = "Fetching usage from Retell...";
      const formData = new FormData(form);
      const month = formData.get("month");
      const apiKey = formData.get("api_key");
      const teamId = formData.get("team_id");

      try {
        const response = await fetch("/usage/monthly/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            month,
            retell_api_key: apiKey,
            team_id: teamId?.trim() ? teamId.trim() : null,
          }),
        });

        if (!response.ok) {
          const error = await response.json().catch(() => ({ detail: response.statusText }));
          throw new Error(error.detail || "Request failed");
        }

        const payload = await response.json();
        const totalMinutes = payload.metrics.reduce((sum, metric) => sum + (metric.value || 0), 0);
        const totalHours = totalMinutes / 60;

        const metricsRows = payload.metrics
          .map((metric) => `
            <tr>
              <td>${metric.period_start}</td>
              <td>${metric.period_end}</td>
              <td>${metric.value.toLocaleString(undefined, { maximumFractionDigits: 2 })} minutes</td>
              <td>${(metric.value / 60).toLocaleString(undefined, { maximumFractionDigits: 2 })} hours</td>
            </tr>
          `)
          .join("");

        results.innerHTML = `
          <div class="result-card">
            <div>
              <strong>Month:</strong> ${payload.month}
            </div>
            <div>
              <strong>Total usage:</strong> ${totalHours.toLocaleString(undefined, { maximumFractionDigits: 2 })} hours (${totalMinutes.toLocaleString(undefined, { maximumFractionDigits: 0 })} minutes)
            </div>
            <div>
              <table>
                <thead>
                  <tr>
                    <th>Start</th>
                    <th>End</th>
                    <th>Minutes</th>
                    <th>Hours</th>
                  </tr>
                </thead>
                <tbody>
                  ${metricsRows || '<tr><td colspan="4">No usage metrics found for this month.</td></tr>'}
                </tbody>
              </table>
            </div>
            <details>
              <summary>Raw response</summary>
              <pre>${JSON.stringify(payload.source_payload, null, 2)}</pre>
            </details>
          </div>
        `;
        status.textContent = "Usage loaded successfully.";
        form.reset();
      } catch (error) {
        status.textContent = error.message;
      }
    });
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse, tags=["ui"])
async def index() -> HTMLResponse:
    return HTMLResponse(content=INDEX_HTML)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _build_monthly_response(
    *, year: int, month: int, payload: dict[str, object]
) -> MonthlyUsageResponse:
    metrics: list[UsageMetric] = []
    data = payload.get("data", [])  # type: ignore[assignment]
    for item in data:  # type: ignore[assignment]
        period_start = item.get("start_date") or item.get("period_start")
        period_end = item.get("end_date") or item.get("period_end")
        value = item.get("value") or item.get("minutes") or item.get("count")

        if period_start and period_end and value is not None:
            metrics.append(
                UsageMetric(
                    period_start=date.fromisoformat(period_start),
                    period_end=date.fromisoformat(period_end),
                    value=float(value),
                    raw=item,
                )
            )

    month_key = f"{year:04d}-{month:02d}"
    return MonthlyUsageResponse(month=month_key, metrics=metrics, source_payload=payload)


@app.get("/usage/monthly", response_model=MonthlyUsageResponse, tags=["usage"])
async def get_monthly_usage(
    year: int = Query(default=datetime.utcnow().year, ge=2000, le=3000),
    month: int = Query(default=datetime.utcnow().month, ge=1, le=12),
    team_id: Optional[str] = Query(default=None, description="Optional Retell team ID"),
    api_key: Optional[str] = Query(
        default=None, description="Override Retell API key for this request"
    ),
    service: UsageService = Depends(get_usage_service),
) -> MonthlyUsageResponse:
    try:
        payload = await service.get_monthly_usage(
            year=year, month=month, team_id=team_id, api_key_override=api_key
        )
    except RetellAPIError as exc:  # pragma: no cover - depends on external API
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return _build_monthly_response(year=year, month=month, payload=payload)


@app.post(
    "/usage/monthly/query",
    response_model=MonthlyUsageResponse,
    tags=["usage"],
    summary="Fetch monthly usage by posting an API key and month",
)
async def query_monthly_usage(
    request: MonthlyUsageQuery, service: UsageService = Depends(get_usage_service)
) -> MonthlyUsageResponse:
    year_str, month_str = request.month.split("-")
    year = int(year_str)
    month = int(month_str)

    try:
        payload = await service.get_monthly_usage(
            year=year,
            month=month,
            team_id=request.team_id,
            api_key_override=request.retell_api_key,
        )
    except RetellAPIError as exc:  # pragma: no cover - depends on external API
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return _build_monthly_response(year=year, month=month, payload=payload)
