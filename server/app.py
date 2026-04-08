from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from server.models import ResetRequest, StepRequest, State, Observation
from server.environment import ClaimDisputeEnvironment
from server.scenarios import list_task_ids, SCENARIOS

app = FastAPI(title="Insurance Claim Dispute Resolution Environment")
env = ClaimDisputeEnvironment()


@app.get("/", response_class=HTMLResponse)
def root():
    task_rows = ""
    for tid, s in SCENARIOS.items():
        personality = s.get("personality", "bureaucratic")
        task_rows += (
            f"<tr>"
            f"<td><code>{tid}</code></td>"
            f"<td>{s['difficulty'].capitalize()}</td>"
            f"<td>{personality.replace('_', '-').capitalize()}</td>"
            f"<td>${s['denied_amount']:,.0f}</td>"
            f"<td>{s['description'][:120]}...</td>"
            f"</tr>\n"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Insurance Claim Dispute Resolution</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1a1a1a;
    background: #f8f9fa;
    line-height: 1.6;
  }}
  .container {{
    max-width: 960px;
    margin: 0 auto;
    padding: 40px 24px;
  }}
  h1 {{
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;
  }}
  .subtitle {{
    color: #555;
    font-size: 16px;
    margin-bottom: 32px;
  }}
  h2 {{
    font-size: 20px;
    font-weight: 600;
    margin: 32px 0 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid #e0e0e0;
  }}
  p {{
    margin-bottom: 12px;
    color: #333;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 24px;
    font-size: 14px;
  }}
  th, td {{
    text-align: left;
    padding: 10px 12px;
    border-bottom: 1px solid #e0e0e0;
  }}
  th {{
    background: #f0f0f0;
    font-weight: 600;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #444;
  }}
  tr:hover {{
    background: #f5f7fa;
  }}
  code {{
    background: #eef;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 13px;
  }}
  .method {{
    display: inline-block;
    font-size: 12px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 3px;
    color: #fff;
    min-width: 48px;
    text-align: center;
  }}
  .method-get {{ background: #2e7d32; }}
  .method-post {{ background: #1565c0; }}
  .links {{
    margin-top: 32px;
    padding-top: 16px;
    border-top: 1px solid #e0e0e0;
    font-size: 14px;
    color: #555;
  }}
  .links a {{
    color: #1565c0;
    text-decoration: none;
  }}
  .links a:hover {{
    text-decoration: underline;
  }}
</style>
</head>
<body>
<div class="container">
  <h1>Insurance Claim Dispute Resolution</h1>
  <p class="subtitle">
    An OpenEnv-compliant environment for testing AI agents on multi-turn insurance claim negotiations.
  </p>
  <p>
    Agents argue with a simulated insurer over multiple rounds to recover denied claim amounts.
    The insurer pushes back with distinct personalities, and the agent must choose the right
    strategy, timing, and arguments to maximize recovery.
  </p>

  <h2>Scenarios</h2>
  <table>
    <thead>
      <tr>
        <th>Task ID</th>
        <th>Difficulty</th>
        <th>Personality</th>
        <th>Denied</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody>
      {task_rows}
    </tbody>
  </table>

  <h2>API Endpoints</h2>
  <table>
    <thead>
      <tr><th>Method</th><th>Path</th><th>Description</th></tr>
    </thead>
    <tbody>
      <tr>
        <td><span class="method method-get">GET</span></td>
        <td><code>/tasks</code></td>
        <td>List all available task IDs</td>
      </tr>
      <tr>
        <td><span class="method method-post">POST</span></td>
        <td><code>/reset</code></td>
        <td>Start a new episode. Body: <code>{{"task_id": "easy_billing_error"}}</code></td>
      </tr>
      <tr>
        <td><span class="method method-post">POST</span></td>
        <td><code>/step</code></td>
        <td>Submit an action. Body: <code>{{"action": {{"action_type": "cite_policy", "argument": "..."}}}}</code></td>
      </tr>
      <tr>
        <td><span class="method method-get">GET</span></td>
        <td><code>/state</code></td>
        <td>Get the current episode state</td>
      </tr>
      <tr>
        <td><span class="method method-get">GET</span></td>
        <td><code>/score</code></td>
        <td>Get the current score (0.0 to 1.0)</td>
      </tr>
      <tr>
        <td><span class="method method-get">GET</span></td>
        <td><code>/transcript</code></td>
        <td>Full negotiation transcript for the current episode (plain text)</td>
      </tr>
      <tr>
        <td><span class="method method-get">GET</span></td>
        <td><code>/health</code></td>
        <td>Health check</td>
      </tr>
    </tbody>
  </table>

  <div class="links">
    Source: <a href="https://huggingface.co/spaces/AnishKishore/insurance-claim-env">Hugging Face Space</a>
  </div>
</div>
</body>
</html>"""
    return html


@app.get("/tasks")
def get_tasks() -> list[str]:
    return list_task_ids()


@app.post("/reset")
def reset(request: ResetRequest = ResetRequest()) -> State:
    try:
        return env.reset(task_id=request.task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step")
def step(request: StepRequest) -> Observation:
    try:
        return env.step(request.action)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state")
def get_state() -> State:
    try:
        return env.get_state()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/score")
def get_score() -> dict:
    return {"score": env.score()}


@app.get("/transcript", response_class=PlainTextResponse)
def get_transcript():
    try:
        state = env.get_state()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    lines = []
    lines.append(f"TRANSCRIPT: {state.task_id}")
    lines.append(f"Difficulty: {state.difficulty}")
    lines.append(f"Claim: ${state.claim_amount:,.2f} | Denied: ${state.denied_amount:,.2f} | Max recoverable: ${state.max_recoverable:,.2f}")
    lines.append("")
    lines.append("SCENARIO:")
    lines.append(state.description)
    lines.append("")
    lines.append("-" * 80)

    for entry in state.history:
        step = entry["step"]
        action_type = entry["action_type"]
        argument = entry["argument"]
        reward = entry["reward"]
        insurer_msg = entry.get("insurer_message", "")
        offer = entry.get("offer_amount", 0.0)

        lines.append("")
        lines.append(f"[Step {step}] AGENT ({action_type}):")
        lines.append(argument)
        lines.append("")
        lines.append(f"[Step {step}] INSURER (offer: ${offer:,.2f}, reward: {reward:.4f}):")
        lines.append(insurer_msg)
        lines.append("")
        lines.append("-" * 80)

    lines.append("")
    status = "COMPLETED" if state.done else "IN PROGRESS"
    lines.append(f"STATUS: {status}")
    lines.append(f"Current offer: ${state.current_offer:,.2f} / ${state.max_recoverable:,.2f}")
    lines.append(f"Score: {state.current_offer / state.max_recoverable:.4f}" if state.max_recoverable > 0 else "Score: 0.0000")
    lines.append(f"Steps used: {state.step} / {state.max_steps}")

    return "\n".join(lines)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
