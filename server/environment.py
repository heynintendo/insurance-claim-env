from server.models import Action, ActionType, Observation, State
from server.scenarios import get_insurer_profile, get_scenario, list_task_ids
from server.grader import compute_step_reward, final_score, generate_insurer_response


class ClaimDisputeEnvironment:
    def __init__(self):
        self.state: State | None = None
        self.profile: dict | None = None

    def reset(self, task_id: str | None = None) -> State:
        if task_id is None:
            task_id = list_task_ids()[0]
        self.state = get_scenario(task_id)
        self.profile = get_insurer_profile(task_id)
        return self.state

    def step(self, action: Action) -> Observation:
        if self.state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        if self.state.done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        step_reward, new_offer = compute_step_reward(action, self.profile, self.state)

        self.state.current_offer = new_offer
        self.state.cumulative_reward += step_reward
        self.state.step += 1

        done = (
            self.state.step >= self.state.max_steps
            or action.action_type == ActionType.ACCEPT_PARTIAL
            or new_offer >= self.state.max_recoverable * 0.95
        )
        self.state.done = done

        insurer_response = generate_insurer_response(
            action, self.profile, self.state, new_offer, step_reward
        )

        self.state.history.append({
            "step": self.state.step - 1,
            "action_type": action.action_type.value,
            "argument": action.argument,
            "reward": step_reward,
            "insurer_message": insurer_response.message,
            "offer_amount": insurer_response.offer_amount,
        })

        return Observation(
            step=self.state.step,
            insurer_response=insurer_response,
            current_offer=self.state.current_offer,
            max_recoverable=self.state.max_recoverable,
            steps_remaining=self.state.max_steps - self.state.step,
            done=done,
            reward=step_reward,
            cumulative_reward=self.state.cumulative_reward,
        )

    def get_state(self) -> State:
        if self.state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        return self.state

    def score(self) -> float:
        if self.state is None:
            return 0.01
        return final_score(self.state)
