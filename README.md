---
title: Insurance Claim Dispute Resolution
emoji: "🏥"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# Insurance Claim Dispute Resolution

Every year, millions of insurance claims get denied. Some denials are legitimate. A lot of them aren't. They rely on policyholders not knowing their rights, not reading the fine print, or just giving up because fighting an insurance company is exhausting.

This environment simulates that fight. An AI agent takes the role of a policyholder (or their advocate) and argues with a simulated insurer over multiple rounds to recover denied claim amounts. The insurer pushes back, stonewalls, makes lowball offers, and hides behind policy language -- just like the real thing.

The point isn't to train agents to be lawyers. It's to test whether language models can do the kind of structured, adversarial reasoning that insurance disputes actually require: reading a policy, finding the weak point in a denial, knowing when to cite law vs. when to provide evidence vs. when to escalate, and doing it all in the right order.

## Why This Matters

The insurance claim denial problem is not small. Roughly 17% of in-network claims are denied in the US, and the appeal rate is under 1%. Most people don't appeal because the process is designed to be exhausting. You need to understand your policy, know the relevant regulations, write structured arguments, and keep pushing through multiple rounds of pushback from adjusters who do this for a living.

This is exactly the kind of problem where AI agents could make a real difference. Not by replacing lawyers, but by doing the grunt work of identifying denial errors, citing the right policy sections, and drafting appeal arguments that a human can review and send. The people who get hurt worst by wrongful denials are the ones who can least afford to fight them.

But building agents that can actually do this well is harder than it looks. The agent needs to understand domain-specific terminology -- not just "the ACA prohibits pre-existing condition exclusions" but the specific statutory section (42 USC 300gg-3) that makes the argument stick. It needs to know that threatening a regulatory complaint on step 1 makes you look unserious, but the same threat on step 6 after building a documented case carries real weight. It needs to adapt its strategy based on how the insurer responds, not just blast through a fixed script.

This environment tests all of that. Easy scenarios can be solved with basic policy knowledge. Expert scenarios require the kind of specific legal citations, medical terminology, and regulatory references that separate a good advocate from a great one.

## The Scenarios

Twelve scenarios across four difficulty tiers, covering six types of insurance. Each one is based on patterns from real disputes.

### Easy -- Clear-cut errors where the insurer is obviously wrong

| ID | Type | Denied | What happened |
|----|------|--------|---------------|
| `easy_billing_error` | Health | $3,000 | ER visit denied because the claim was submitted under the wrong billing code. The policy clearly covers emergency visits. Point at the code error, cite the policy, done. |
| `easy_dental_cleaning` | Dental | $285 | Routine cleaning denied because the insurer miscounted -- they logged a canceled appointment as a completed visit. Records show only one cleaning in the past year. |
| `easy_auto_glass` | Auto | $850 | Windshield replacement denied as "cosmetic damage." It's a cracked windshield from road debris. Comprehensive coverage explicitly covers glass, and state law requires intact windshields. |

### Medium -- Ambiguous policy language or procedural obstacles

| ID | Type | Denied | What happened |
|----|------|--------|---------------|
| `medium_partial_denial` | Health | $8,500 | Knee surgery approved, but the robotic-assisted technique denied as "experimental." Policy covers arthroscopy but is silent on robotic tools. Is the robot a separate procedure or just a tool? |
| `medium_travel_emergency` | Travel | $12,400 | Emergency appendectomy in Costa Rica denied because the hospital was "out of network." There is no network in Costa Rica. The patient was being wheeled into surgery -- pre-authorization wasn't really an option. |
| `medium_homeowners_pipe` | Homeowners | $15,800 | Basement water damage from a burst pipe denied as "flood damage." Floods and burst pipes are completely different perils. The policy covers one and not the other, and the insurer picked the wrong one. |

### Hard -- Stubborn insurers, multi-step legal arguments required

| ID | Type | Denied | What happened |
|----|------|--------|---------------|
| `hard_full_denial` | Health | $67,000 | Twelve-day hospitalization for a lupus flare denied as a "pre-existing condition." The patient has been continuously covered for 14 months. The ACA has prohibited pre-existing condition exclusions since 2014. The insurer is also challenging the length of stay. |
| `hard_disability_mental` | Disability | $57,600 | Long-term disability claim for severe depression denied. The insurer says the claimant doesn't meet the definition of "total disability" and is misapplying the 24-month mental health cap to an 8-month claim. Three physicians have documented the functional limitations. |
| `hard_dental_implant` | Dental | $4,200 | Dental implant denied as cosmetic. The tooth was lost to infection, and the implant prevents bone loss and bite problems. Two providers recommend it as standard of care. The insurer's alternative (a partial denture) would cause long-term damage. |

### Expert -- Complex multi-vector disputes, very stubborn insurers

| ID | Type | Denied | What happened |
|----|------|--------|---------------|
| `expert_auto_diminished_value` | Auto | $6,800 | After a not-at-fault collision, the car was repaired but lost $6,800 in resale value due to its accident history. The insurer says diminished value is "speculative." State law disagrees, and dealer appraisals confirm the loss. |
| `expert_homeowners_mold` | Homeowners | $23,500 | Mold discovered 6 weeks after a covered water heater burst. Water damage was already paid, but mold remediation denied under the mold exclusion. The mold only exists because of the covered event. Ensuing loss doctrine should apply. |
| `expert_health_balance_billing` | Health | $27,000 | Emergency heart surgery at an in-network hospital, but the assigned surgeon was out-of-network. Surprise balance bill of $27,000. State and federal surprise billing laws should prevent this, but the insurer is misreading the statute. |

## Action Space

The agent picks one of twelve action types per step, along with a free-text argument:

| Action | What it does | When to use it |
|--------|-------------|----------------|
| `cite_policy` | Reference specific policy sections | When the policy language supports your case |
| `provide_evidence` | Submit documentation or records | When you have concrete proof |
| `escalate` | General escalation (supervisors, complaints) | Mid-to-late game when progress stalls |
| `request_supervisor` | Ask for a senior reviewer | After initial arguments have been made |
| `accept_partial` | Accept the current offer, end episode | When the offer is good enough |
| `reject_offer` | Reject a lowball offer | When you can do better |
| `request_itemized_bill` | Ask for a detailed charge breakdown | Early game, especially for billing disputes |
| `file_formal_appeal` | Submit a formal appeal | After building your case with evidence |
| `cite_precedent` | Reference case law or prior rulings | When legal precedent supports your position |
| `threaten_regulatory_complaint` | Threaten to involve regulators | Late game nuclear option, penalized if used too early |
| `provide_medical_records` | Submit medical documentation | When clinical evidence is the key argument |
| `request_peer_review` | Ask for independent medical review | When the insurer's medical judgment is questionable |

Timing matters. Requesting a supervisor on step 1 is weak. Threatening a regulatory complaint before you've built your case backfires. The environment rewards agents that sequence their actions strategically.

## Observation Space

After each action, the agent receives:

- **Insurer response** -- a text message reacting to the argument, with contextual flavor based on the action taken
- **Current offer** -- how much the insurer is willing to pay right now
- **Max recoverable** -- the ceiling for this scenario
- **Steps remaining** -- how many turns are left (max 8 per episode)
- **Step reward** -- how much progress this action made
- **Cumulative reward** -- total progress so far

The insurer's response text gives qualitative signal about how the argument landed. A good agent should read these responses to calibrate its next move.

## Reward Design

The reward function isn't a black box. Transparency matters here -- if you're building an agent to argue insurance claims, you need to understand what the environment actually rewards and why.

**Per-step reward** = effectiveness * max_recoverable * 0.3, normalized. Each action's effectiveness is built up from several factors that mirror what actually works in real insurance disputes:

1. **Action-profile match** -- each insurer has different sensitivities. Some respond to policy citations, others to evidence, others to escalation threats. The profile weights (policy_sensitivity, evidence_sensitivity, escalation_sensitivity) determine what works. This reflects reality: some adjusters care about being technically correct, others respond to pressure, others need clinical documentation. There's no universal winning move.

2. **Argument relevance** -- the free-text argument is matched against scenario-specific concepts (groups of related terms with synonyms). Easy scenarios accept general terms ("emergency", "billing code"). Expert scenarios require precise domain terminology ("42 USC 300gg-3", "IICRC S520 standard", "Mabry formula"). This is the sharpest difficulty lever in the environment. A general LLM can talk about insurance concepts, but producing the exact statutory citation or medical term that moves a stubborn adjuster requires genuine domain knowledge.

3. **Timing** -- some actions have multipliers based on the current step. Escalation is weak early and strong late. Requesting an itemized bill is strongest on step 0. Filing a formal appeal scales with how much case you've built. This isn't arbitrary -- it mirrors the real process. You don't threaten to call the insurance commissioner before you've even cited the policy. And requesting an itemized bill after 6 rounds of arguing is too late.

4. **Strategy sequencing** -- the environment tracks whether actions follow a logical progression through three phases: evidence-building (cite policy, provide evidence), escalation (request supervisor, cite precedent), and nuclear options (formal appeal, regulatory complaint). Following this natural order earns a 15% effectiveness bonus. Skipping straight to threats without building your case gets no bonus. Real insurance disputes work the same way -- adjusters take you more seriously when your escalation is backed by a documented trail of evidence.

5. **Argument detail** -- short, lazy arguments (<20 characters) get a 10% penalty. Detailed arguments get bonuses: 10% at 100+ characters, 15% at 200+, and 20% at 300+. This rewards agents that actually articulate their reasoning rather than sending "I disagree" and hoping for the best. In real disputes, the quality and specificity of your written argument is often the difference between a denial upheld and a denial overturned.

6. **Repetition penalty** -- using the same action type repeatedly gets diminishing returns (15% penalty per repeat). Real adjusters stop listening when you make the same argument three times.

7. **Stubbornness** -- each insurer profile has a stubbornness factor that applies a flat penalty to all actions. Easy scenarios have low stubbornness (0.1), hard scenarios have high stubbornness (0.7), and expert scenarios are very high (0.85-0.9). This is the blunt difficulty knob -- stubborn insurers just don't move much per step, so you need every other factor working in your favor.

**Final score** = current_offer / max_recoverable (0.0 to 1.0).

An episode ends when the agent hits 8 steps, accepts a partial offer, or recovers 95%+ of the max recoverable amount.

The design philosophy is that scoring well on easy scenarios should be achievable with basic prompt engineering. Scoring well on expert scenarios should require either fine-tuning on insurance domain knowledge or retrieval-augmented generation with access to legal databases. The gap between those two is where the interesting agent architecture decisions live.

## Baseline Scores

These are measured baselines to calibrate expectations. "Always cite_policy" sends a short generic argument with the same action every step. "Heuristic agent" cycles through varied actions with a decent (but non-expert) argument.

| Strategy | Easy | Medium | Hard | Expert |
|----------|------|--------|------|--------|
| Always cite_policy (lazy) | 0.57 | 0.39 | 0.15 | 0.05 |
| Heuristic agent (varied actions) | 0.73 | 0.61 | 0.45 | 0.27 |
| Target (strong LLM with domain knowledge) | 0.90+ | 0.75+ | 0.60+ | 0.40+ |

Per-scenario breakdown (heuristic agent):

| Tier | Scenario | Score |
|------|----------|-------|
| Easy | `easy_billing_error` | 0.99 |
| Easy | `easy_dental_cleaning` | 0.64 |
| Easy | `easy_auto_glass` | 0.55 |
| Medium | `medium_partial_denial` | 0.71 |
| Medium | `medium_travel_emergency` | 0.56 |
| Medium | `medium_homeowners_pipe` | 0.57 |
| Hard | `hard_full_denial` | 0.58 |
| Hard | `hard_disability_mental` | 0.44 |
| Hard | `hard_dental_implant` | 0.34 |
| Expert | `expert_auto_diminished_value` | 0.28 |
| Expert | `expert_homeowners_mold` | 0.23 |
| Expert | `expert_health_balance_billing` | 0.31 |

The difficulty gradient is sharp. Easy scenarios are solvable with generic arguments. Expert scenarios require specific statutory citations, case law references, and domain terminology that general-purpose LLMs rarely produce without retrieval augmentation.

## Setup

### Local development

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

In a separate terminal:

```bash
export HF_TOKEN=your_token
export ENV_URL=http://localhost:8000
python inference.py
```

### Docker

```bash
docker build -t insurance-claim-env .
docker run -p 8000:8000 insurance-claim-env
```

Then run `inference.py` with `ENV_URL=http://localhost:8000`.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tasks` | List available task IDs |
| POST | `/reset` | Start a new episode (`{"task_id": "easy_billing_error"}`) |
| POST | `/step` | Submit an action (`{"action": {"action_type": "cite_policy", "argument": "..."}}`) |
| GET | `/state` | Get current episode state |
| GET | `/score` | Get current score (0.0 to 1.0) |
| GET | `/health` | Health check |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `https://router.huggingface.co/v1` | LLM API endpoint |
| `MODEL_NAME` | `Qwen/Qwen2.5-72B-Instruct` | Model for inference |
| `HF_TOKEN` | -- | HuggingFace API token |
| `ENV_URL` | `http://localhost:8000` | Environment server URL |
