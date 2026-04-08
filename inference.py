import json
import os
import sys

import requests
from openai import OpenAI

ENV_URL = os.getenv("ENV_URL", "https://anishkishore-insurance-claim-env.hf.space")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

VALID_ACTIONS = [
    "cite_policy", "provide_evidence", "escalate",
    "request_supervisor", "accept_partial", "reject_offer",
    "request_itemized_bill", "file_formal_appeal", "cite_precedent",
    "threaten_regulatory_complaint", "provide_medical_records", "request_peer_review",
]

SYSTEM_PROMPT = """You are an expert insurance claim dispute agent. Your goal is to recover as much money as possible for the claimant by arguing with the insurance company.

You must respond with a JSON object containing:
- "action_type": one of {actions}
- "argument": your detailed argument supporting this action

Strategy guidance:
- Start by citing relevant policy sections and identifying errors in the denial.
- Provide medical or documentary evidence to support the claim.
- Escalate or request a supervisor if initial arguments are rebuffed.
- NEVER accept a partial offer unless you have used at least 6 different arguments and the offer exceeds 80% of the max recoverable amount. Always keep fighting.
- Reject inadequate offers and continue arguing with new angles.
- Vary your approach across steps — repeating the same action is less effective.
- Use all available steps. Each new argument can recover more money.

Respond ONLY with the JSON object, no other text."""

VALID_ACTIONS_STR = ", ".join(VALID_ACTIONS)


def build_user_prompt(state: dict, observation: dict | None) -> str:
    parts = []
    if observation is None:
        parts.append("CLAIM DISPUTE SCENARIO:")
        parts.append(state["description"])
        parts.append(f"\nClaim amount: ${state['claim_amount']:,.2f}")
        parts.append(f"Denied amount: ${state['denied_amount']:,.2f}")
        parts.append(f"Maximum recoverable: ${state['max_recoverable']:,.2f}")
        parts.append(f"Steps available: {state['max_steps']}")
        parts.append("\nChoose your first action to begin the dispute.")
    else:
        parts.append("INSURER RESPONSE:")
        parts.append(observation["insurer_response"]["message"])
        parts.append(f"\nCurrent offer: ${observation['current_offer']:,.2f}")
        parts.append(f"Maximum recoverable: ${observation['max_recoverable']:,.2f}")
        parts.append(f"Steps remaining: {observation['steps_remaining']}")
        parts.append(f"Your cumulative reward so far: {observation['cumulative_reward']:.3f}")
        parts.append("\nChoose your next action.")
    return "\n".join(parts)


def parse_action(response_text: str) -> dict:
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    parsed = json.loads(text)
    action_type = parsed.get("action_type", "")
    if action_type not in VALID_ACTIONS:
        action_type = "cite_policy"
    return {
        "action_type": action_type,
        "argument": parsed.get("argument", "I dispute this denial."),
    }


BENCHMARK_NAME = "insurance-claim-dispute-resolution"


def run_episode(task_id: str):
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    try:
        reset_resp = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id}, timeout=30)
        reset_resp.raise_for_status()
        state = reset_resp.json()
    except requests.ConnectionError:
        print(f"[ERROR] Cannot connect to environment at {ENV_URL}. Is the server running?", file=sys.stderr)
        raise
    except requests.HTTPError as e:
        print(f"[ERROR] Reset failed for task {task_id}: {e.response.status_code} {e.response.text}", file=sys.stderr)
        raise
    except requests.Timeout:
        print(f"[ERROR] Timeout connecting to {ENV_URL}/reset", file=sys.stderr)
        raise

    print(f"[START] task={task_id} env={BENCHMARK_NAME} model={MODEL_NAME}")
    sys.stdout.flush()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(actions=VALID_ACTIONS_STR)},
        {"role": "user", "content": build_user_prompt(state, None)},
    ]

    observation = None
    done = False
    step = 0
    rewards = []

    while not done:
        error = None
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.7,
                max_tokens=512,
            )
            assistant_text = completion.choices[0].message.content
            messages.append({"role": "assistant", "content": assistant_text})
        except Exception as e:
            error = f"LLM call failed: {e}"
            print(f"[ERROR] {error}", file=sys.stderr)
            assistant_text = None

        if assistant_text is not None:
            try:
                action = parse_action(assistant_text)
            except (json.JSONDecodeError, KeyError):
                action = {"action_type": "cite_policy", "argument": "I dispute this claim denial."}

            try:
                step_resp = requests.post(
                    f"{ENV_URL}/step",
                    json={"action": action},
                    timeout=30,
                )
                step_resp.raise_for_status()
                observation = step_resp.json()
            except requests.ConnectionError:
                error = f"Lost connection to environment at {ENV_URL}/step"
                print(f"[ERROR] {error}", file=sys.stderr)
                observation = None
            except requests.HTTPError as e:
                error = f"Step failed: {e.response.status_code} {e.response.text}"
                print(f"[ERROR] {error}", file=sys.stderr)
                observation = None
            except requests.Timeout:
                error = f"Timeout on {ENV_URL}/step"
                print(f"[ERROR] {error}", file=sys.stderr)
                observation = None
        else:
            action = {"action_type": "cite_policy", "argument": "I dispute this claim denial."}

        step += 1

        if observation is not None:
            done = observation["done"]
            step_reward = observation["reward"]
            rewards.append(step_reward)
        else:
            done = True
            step_reward = 0.0
            rewards.append(step_reward)

        error_str = error if error else "null"
        done_str = "true" if done else "false"
        print(f"[STEP] step={step} action={action['action_type']} reward={step_reward:.2f} done={done_str} error={error_str}")
        sys.stdout.flush()

        if not done and observation is not None:
            messages.append({"role": "user", "content": build_user_prompt(state, observation)})

    try:
        score_resp = requests.get(f"{ENV_URL}/score", timeout=30)
        score_resp.raise_for_status()
        final = score_resp.json()["score"]
    except Exception as e:
        print(f"[ERROR] Failed to fetch score: {e}", file=sys.stderr)
        final = 0.0

    success = final > 0.0
    success_str = "true" if success else "false"
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={success_str} steps={step} score={final:.2f} rewards={rewards_str}")
    sys.stdout.flush()

    return final


def main():
    try:
        task_ids_resp = requests.get(f"{ENV_URL}/tasks", timeout=30)
        task_ids_resp.raise_for_status()
        task_ids = task_ids_resp.json()
    except requests.ConnectionError:
        print(f"[ERROR] Cannot connect to environment at {ENV_URL}. Is the server running?", file=sys.stderr)
        sys.exit(1)
    except requests.HTTPError as e:
        print(f"[ERROR] Failed to fetch tasks: {e.response.status_code} {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except requests.Timeout:
        print(f"[ERROR] Timeout connecting to {ENV_URL}/tasks", file=sys.stderr)
        sys.exit(1)

    for task_id in task_ids:
        run_episode(task_id)


if __name__ == "__main__":
    main()
