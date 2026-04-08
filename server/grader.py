import re

from server.models import Action, ActionType, InsurerResponse, State


def _normalize(text: str) -> str:
    """Replace hyphens/underscores with spaces, lowercase, collapse whitespace."""
    return re.sub(r"\s+", " ", text.lower().replace("-", " ").replace("_", " ")).strip()


def _words_within_proximity(words: list[str], arg_words: list[str], window: int = 5) -> bool:
    """Check if all words appear within a window of each other in arg_words."""
    if not words:
        return False
    # Find all positions of the first word
    positions = [i for i, w in enumerate(arg_words) if w == words[0]]
    for pos in positions:
        # Check if all remaining words appear within the window
        window_start = max(0, pos - window)
        window_end = min(len(arg_words), pos + window + 1)
        window_slice = arg_words[window_start:window_end]
        if all(w in window_slice for w in words):
            return True
    return False


def _concept_match(argument: str, concepts: list[dict]) -> float:
    argument_lower = argument.lower()
    argument_normalized = _normalize(argument)
    argument_words = argument_normalized.split()

    total_weight = sum(c["weight"] for c in concepts)
    if total_weight == 0:
        return 0.0

    score = 0.0
    for concept in concepts:
        hits = 0.0
        for term in concept["terms"]:
            # Layer 0: Exact substring match (original behavior)
            if term in argument_lower:
                hits += 1.0
                continue

            # Layer 1: Normalized match (hyphens/underscores -> spaces)
            term_normalized = _normalize(term)
            if term_normalized != term and term_normalized in argument_normalized:
                hits += 1.0
                continue

            # Layer 2: Word proximity match (2+ word terms only)
            term_words = term_normalized.split()
            if len(term_words) >= 2 and _words_within_proximity(term_words, argument_words):
                hits += 0.7

        if hits > 0:
            concept_score = min(hits / 2, 1.0)
            score += concept_score * concept["weight"]

    return min(score / total_weight, 1.0)


def _action_effectiveness(action: Action, profile: dict, state: State) -> float:
    base = 0.0
    relevance = _concept_match(action.argument, profile["concepts"])

    match action.action_type:
        case ActionType.CITE_POLICY:
            base = 0.4 * profile["policy_sensitivity"]
            base += 0.6 * relevance * profile["policy_sensitivity"]

        case ActionType.PROVIDE_EVIDENCE:
            base = 0.35 * profile["evidence_sensitivity"]
            base += 0.55 * relevance * profile["evidence_sensitivity"]

        case ActionType.ESCALATE:
            escalation_multiplier = min(state.step / 2, 1.0)
            base = 0.4 * profile["escalation_sensitivity"] * escalation_multiplier
            base += 0.35 * relevance * profile["escalation_sensitivity"]

        case ActionType.REQUEST_SUPERVISOR:
            if state.step < 2:
                base = 0.15
            else:
                base = 0.3 * profile["escalation_sensitivity"]
                base += 0.2 * relevance

        case ActionType.ACCEPT_PARTIAL:
            base = 0.0

        case ActionType.REJECT_OFFER:
            if state.current_offer > 0:
                base = 0.2
            else:
                base = 0.05

        case ActionType.REQUEST_ITEMIZED_BILL:
            base = 0.3 * profile["evidence_sensitivity"]
            base += 0.4 * relevance * profile["evidence_sensitivity"]
            if state.step == 0:
                base *= 1.3

        case ActionType.FILE_FORMAL_APPEAL:
            appeal_multiplier = min(state.step / 3, 1.0)
            base = 0.45 * profile["escalation_sensitivity"] * appeal_multiplier
            base += 0.4 * relevance * profile["policy_sensitivity"]

        case ActionType.CITE_PRECEDENT:
            base = 0.35 * profile["policy_sensitivity"]
            base += 0.5 * relevance * profile["policy_sensitivity"]

        case ActionType.THREATEN_REGULATORY_COMPLAINT:
            escalation_multiplier = min(state.step / 3, 1.0)
            base = 0.5 * profile["escalation_sensitivity"] * escalation_multiplier
            base += 0.3 * relevance * profile["escalation_sensitivity"]
            if state.step < 2:
                base *= 0.4

        case ActionType.PROVIDE_MEDICAL_RECORDS:
            base = 0.4 * profile["evidence_sensitivity"]
            base += 0.5 * relevance * profile["evidence_sensitivity"]

        case ActionType.REQUEST_PEER_REVIEW:
            if state.step < 2:
                base = 0.15
            else:
                base = 0.35 * profile["evidence_sensitivity"]
                base += 0.3 * relevance * profile["policy_sensitivity"]

    stubbornness_penalty = profile["stubbornness"] * 0.12
    effectiveness = max(base - stubbornness_penalty, 0.0)

    repeated_actions = sum(
        1 for h in state.history if h.get("action_type") == action.action_type.value
    )
    if repeated_actions > 0:
        effectiveness *= max(0.5, 1.0 - 0.15 * repeated_actions)

    # Strategy sequencing bonus: reward logical progression through phases.
    # Phase 1 (early): cite_policy, provide_evidence, request_itemized_bill, provide_medical_records
    # Phase 2 (mid):   escalate, request_supervisor, cite_precedent, request_peer_review
    # Phase 3 (late):  file_formal_appeal, threaten_regulatory_complaint
    _PHASE = {
        "cite_policy": 1, "provide_evidence": 1,
        "request_itemized_bill": 1, "provide_medical_records": 1,
        "escalate": 2, "request_supervisor": 2,
        "cite_precedent": 2, "request_peer_review": 2,
        "file_formal_appeal": 3, "threaten_regulatory_complaint": 3,
    }
    current_phase = _PHASE.get(action.action_type.value, 0)
    if current_phase > 0 and state.history:
        prior_phases = [
            _PHASE.get(h.get("action_type", ""), 0) for h in state.history
        ]
        prior_phases = [p for p in prior_phases if p > 0]
        if prior_phases:
            max_prior = max(prior_phases)
            has_phase_1 = any(p == 1 for p in prior_phases)
            # Bonus: current phase >= max prior (not jumping ahead) AND
            # phase 1 groundwork was laid before escalating
            if current_phase >= max_prior and (current_phase == 1 or has_phase_1):
                effectiveness *= 1.15

    # Argument detail bonus/penalty based on length.
    arg_len = len(action.argument.strip())
    if arg_len < 20:
        effectiveness *= 0.9
    elif arg_len >= 300:
        effectiveness *= 1.2
    elif arg_len >= 200:
        effectiveness *= 1.15
    elif arg_len >= 100:
        effectiveness *= 1.1

    return min(effectiveness, 1.0)


def compute_step_reward(action: Action, profile: dict, state: State) -> tuple[float, float]:
    effectiveness = _action_effectiveness(action, profile, state)
    recovery_increment = effectiveness * state.max_recoverable * 0.3
    new_offer = min(state.current_offer + recovery_increment, state.max_recoverable)
    actual_increment = new_offer - state.current_offer
    step_reward = actual_increment / state.max_recoverable if state.max_recoverable > 0 else 0.0
    return step_reward, new_offer


def _extract_argument_topic(argument: str) -> str:
    """Pull a short phrase from the agent's argument to reference in the response."""
    arg = argument.strip()
    # Take the first sentence or clause, trimmed to something quotable.
    # Split on sentence boundary (". " + uppercase), but only if the result is long enough.
    import re
    m = re.search(r"\. [A-Z]", arg)
    if m and m.start() >= 30:
        arg = arg[:m.start()]
    else:
        for sep in ["; ", ", and ", ", but "]:
            idx = arg.find(sep)
            if idx >= 30:
                arg = arg[:idx]
                break
    # Cap length for readability
    if len(arg) > 120:
        arg = arg[:117].rsplit(" ", 1)[0] + "..."
    return arg.rstrip(".,;:!? ")


def _matched_concept_names(argument: str, concepts: list[dict]) -> list[str]:
    """Return names of concepts the argument actually hit."""
    lower = argument.lower()
    return [
        c["name"].replace("_", " ")
        for c in concepts
        if any(t in lower for t in c["terms"])
    ]


def _action_type_response(action: Action, state: State, step_reward: float,
                          new_offer: float, topic: str, matched: list[str]) -> str:
    """Build an action-type-specific response that references the argument."""
    matched_str = ", ".join(matched[:2]) if matched else "the points raised"

    match action.action_type:
        case ActionType.CITE_POLICY:
            if step_reward > 0.1:
                return (
                    f"We have reviewed your policy citation regarding \"{topic}\" and "
                    f"acknowledge that the language around {matched_str} supports a "
                    f"revised reading. We are prepared to adjust our position to ${new_offer:,.2f}."
                )
            elif step_reward > 0.03:
                return (
                    f"We have reviewed the policy sections you referenced regarding \"{topic}.\" "
                    f"While our interpretation of the relevant provisions differs from yours, "
                    f"we recognize some ambiguity around {matched_str} and can offer ${new_offer:,.2f}."
                )
            else:
                return (
                    f"We have reviewed your citation regarding \"{topic}\" but do not find "
                    f"that it applies to the circumstances of this denial. The policy language "
                    f"is clear on this matter."
                )

        case ActionType.PROVIDE_EVIDENCE:
            if step_reward > 0.1:
                return (
                    f"The documentation you provided regarding \"{topic}\" is compelling. "
                    f"The evidence around {matched_str} warrants a revised assessment. "
                    f"We can offer ${new_offer:,.2f}."
                )
            elif step_reward > 0.03:
                return (
                    f"We have received and reviewed the evidence regarding \"{topic}.\" "
                    f"Some of the documentation around {matched_str} has merit, though it does "
                    f"not fully address our concerns. Our revised offer is ${new_offer:,.2f}."
                )
            else:
                return (
                    f"We have reviewed the evidence you submitted regarding \"{topic}\" "
                    f"but find it insufficient to alter our determination. Additional "
                    f"documentation may be needed."
                )

        case ActionType.ESCALATE:
            if step_reward > 0.1:
                return (
                    f"Given the seriousness of your escalation regarding \"{topic}\" and "
                    f"the issues raised around {matched_str}, we are elevating this case "
                    f"for expedited review. Our revised offer is ${new_offer:,.2f}."
                )
            elif step_reward > 0.03:
                return (
                    f"We have noted your intent to escalate this matter regarding \"{topic}.\" "
                    f"While we stand by our review process, we have reconsidered the aspects "
                    f"related to {matched_str}. We can offer ${new_offer:,.2f}."
                )
            else:
                return (
                    f"We acknowledge your desire to escalate regarding \"{topic},\" however "
                    f"escalation alone does not change the factual basis of our determination. "
                    f"We encourage you to provide additional supporting documentation."
                )

        case ActionType.REQUEST_SUPERVISOR:
            if state.step < 2:
                return (
                    f"We understand your request for supervisory review regarding \"{topic},\" "
                    f"but this case has not yet completed the standard review process. "
                    f"Please continue to provide your arguments so we can fully evaluate the claim."
                )
            else:
                base = (
                    f"Your request for supervisory review regarding \"{topic}\" has been noted. "
                    f"A senior claims reviewer will be assigned to examine the issues around "
                    f"{matched_str}."
                )
                if new_offer > 0:
                    base += f" The current offer stands at ${new_offer:,.2f} pending their review."
                return base

        case ActionType.ACCEPT_PARTIAL:
            # Handled separately before this function is called
            return f"We're glad we could reach an agreement. We will process a payment of ${new_offer:,.2f}."

        case ActionType.REJECT_OFFER:
            if state.current_offer > 0:
                return (
                    f"We have noted your rejection of our current offer and your position "
                    f"regarding \"{topic}.\" We are willing to continue discussions, but our "
                    f"assessment of {matched_str} has not changed. The offer remains at ${new_offer:,.2f}."
                )
            else:
                return (
                    f"We note your objection regarding \"{topic},\" however no offer has been "
                    f"made at this time. Please provide specific policy references or evidence "
                    f"to support your position."
                )

        case ActionType.REQUEST_ITEMIZED_BILL:
            if step_reward > 0.03:
                return (
                    f"Per your request regarding \"{topic},\" we are providing an itemized "
                    f"breakdown of the charges under review. Upon re-examination of the "
                    f"line items related to {matched_str}, we have identified adjustments. "
                    f"Our revised offer is ${new_offer:,.2f}."
                )
            else:
                return (
                    f"We will provide the itemized breakdown you requested regarding \"{topic}.\" "
                    f"However, a line-item review does not change our determination on the "
                    f"underlying coverage question."
                )

        case ActionType.FILE_FORMAL_APPEAL:
            if state.step < 2:
                return (
                    f"Your formal appeal regarding \"{topic}\" has been logged. However, we "
                    f"note that the standard review process has not yet been exhausted. "
                    f"The appeals department will review your case in due course."
                )
            elif step_reward > 0.1:
                return (
                    f"Your formal appeal regarding \"{topic}\" has been received and assigned "
                    f"to our appeals department. After preliminary review of your arguments "
                    f"around {matched_str}, we are prepared to offer ${new_offer:,.2f} while "
                    f"the full appeal is processed."
                )
            else:
                return (
                    f"Your formal appeal regarding \"{topic}\" has been logged and will be "
                    f"reviewed by our appeals department. The issues you raised around "
                    f"{matched_str} will be examined. Current offer: ${new_offer:,.2f}."
                )

        case ActionType.CITE_PRECEDENT:
            if step_reward > 0.1:
                return (
                    f"The precedent you cited regarding \"{topic}\" is relevant to this case. "
                    f"In light of the established rulings around {matched_str}, we are "
                    f"revising our position. Our updated offer is ${new_offer:,.2f}."
                )
            elif step_reward > 0.03:
                return (
                    f"We have reviewed the precedent you referenced regarding \"{topic}.\" "
                    f"While the applicability to {matched_str} in this specific case is "
                    f"debatable, we acknowledge the argument has some weight. Offer: ${new_offer:,.2f}."
                )
            else:
                return (
                    f"We have reviewed the precedent you cited regarding \"{topic}\" but find "
                    f"it distinguishable from the facts of this claim. The circumstances "
                    f"around {matched_str} differ materially from the cited case."
                )

        case ActionType.THREATEN_REGULATORY_COMPLAINT:
            if state.step < 2:
                return (
                    f"We note your mention of regulatory action regarding \"{topic}.\" "
                    f"Regulatory threats at this early stage of review are premature. "
                    f"We encourage you to work through the standard dispute process first."
                )
            elif step_reward > 0.1:
                return (
                    f"We take your concerns regarding \"{topic}\" and potential regulatory "
                    f"involvement very seriously. After re-examining the issues around "
                    f"{matched_str}, we want to resolve this matter promptly. "
                    f"Our revised offer is ${new_offer:,.2f}."
                )
            else:
                return (
                    f"We are confident in our claims handling regarding \"{topic}\" and "
                    f"welcome any regulatory review. That said, we remain open to resolving "
                    f"this through the standard process. Current offer: ${new_offer:,.2f}."
                )

        case ActionType.PROVIDE_MEDICAL_RECORDS:
            if step_reward > 0.1:
                return (
                    f"The medical records you submitted regarding \"{topic}\" provide "
                    f"significant clinical support. The documentation around {matched_str} "
                    f"justifies a revised assessment. Our updated offer is ${new_offer:,.2f}."
                )
            elif step_reward > 0.03:
                return (
                    f"We have reviewed the medical records pertaining to \"{topic}.\" "
                    f"The clinical documentation around {matched_str} addresses some of "
                    f"our concerns. Revised offer: ${new_offer:,.2f}."
                )
            else:
                return (
                    f"We have added the medical records regarding \"{topic}\" to the case "
                    f"file. However, the clinical documentation does not sufficiently "
                    f"address the basis for our denial."
                )

        case ActionType.REQUEST_PEER_REVIEW:
            if state.step < 2:
                return (
                    f"Your request for peer review regarding \"{topic}\" is noted, but the "
                    f"case has not yet completed the standard clinical review process. "
                    f"Please provide your supporting arguments first."
                )
            else:
                return (
                    f"An independent medical reviewer will be consulted regarding \"{topic}\" "
                    f"and the clinical questions around {matched_str}. "
                    + (f"Pending their review, our current offer is ${new_offer:,.2f}."
                       if new_offer > 0
                       else "We will update you once the peer review is complete.")
                )

    # Fallback (should not be reached)
    return f"We have reviewed your submission. Current offer: ${new_offer:,.2f}."


def _apply_personality(message: str, personality: str, step_reward: float, is_final: bool) -> str:
    """Transform the base response message to match the insurer's personality."""
    if personality == "bureaucratic":
        # Hides behind process, forms, reference numbers, and procedure
        prefixes_strong = [
            "Per internal review protocol RV-7, ",
            "Following standard claims procedure section 4.2, ",
            "As documented in our review workflow, ",
        ]
        prefixes_weak = [
            "In accordance with established claims processing guidelines, ",
            "Per our standard adjudication protocol, ",
            "As required by our internal review procedures, ",
        ]
        import hashlib
        idx = int(hashlib.md5(message[:20].encode()).hexdigest(), 16) % 3
        prefix = prefixes_strong[idx] if step_reward > 0.05 else prefixes_weak[idx]
        message = prefix + message[0].lower() + message[1:]
        if is_final:
            message += " Please retain this correspondence for your records. Reference number will follow."

    elif personality == "aggressive":
        # Confrontational, challenges the claimant's credibility, uses strong language
        if step_reward > 0.1:
            message = message.replace("We are prepared to adjust", "Against our better judgment, we will adjust")
            message = message.replace("we agree to", "we are compelled to")
            message = message.replace("is compelling", "raises points we cannot entirely dismiss")
            message = message.replace("We can offer", "We will grudgingly offer")
            message = "Let us be direct. " + message
        elif step_reward > 0.03:
            message = message.replace("we acknowledge", "we reluctantly concede")
            message = message.replace("has merit", "has limited merit at best")
            message = message.replace("some weight", "marginal weight")
            message = message.replace("we have reconsidered", "we have been forced to reconsider")
            message = message.replace("We can offer", "We are offering")
            message = "We remain unconvinced by most of your argument. " + message
        else:
            challenges = [
                " We strongly suggest you reconsider pursuing this line of argument.",
                " Frankly, this does not advance your case.",
                " We fail to see how this changes the fundamental basis for our denial.",
            ]
            import hashlib
            idx = int(hashlib.md5(message[:20].encode()).hexdigest(), 16) % 3
            message += challenges[idx]

    elif personality == "passive_aggressive":
        # Superficially polite but dismissive, backhanded acknowledgments
        if step_reward > 0.1:
            message = "We appreciate your thoroughness. " + message
        elif step_reward > 0.03:
            hedges = [
                "We certainly understand your frustration, and we want you to know we take every claim seriously. ",
                "We appreciate you taking the time to put this together. ",
                "We do value your persistence on this matter. ",
            ]
            import hashlib
            idx = int(hashlib.md5(message[:20].encode()).hexdigest(), 16) % 3
            message = hedges[idx] + message
        else:
            dismissals = [
                " We understand this may not be the answer you were hoping for, but we do encourage you to review our denial letter carefully.",
                " We wish we could be of more help, but unfortunately the policy is quite clear on this point.",
                " We know this process can be confusing, and we are always here to help you understand our decision.",
            ]
            import hashlib
            idx = int(hashlib.md5(message[:20].encode()).hexdigest(), 16) % 3
            message += dismissals[idx]

    elif personality == "reasonable":
        # Professional, willing to engage, explains reasoning even when denying
        if step_reward > 0.1:
            message = message.replace("We are prepared to adjust", "This is a fair point, and we are adjusting")
            message = message.replace("warrants a revised assessment", "clearly warrants a revised assessment")
        elif step_reward > 0.03:
            message = "We want to work with you to resolve this fairly. " + message
        else:
            message += " We encourage you to provide additional details, as we genuinely want to ensure this claim is adjudicated correctly."

    return message


def generate_insurer_response(
    action: Action, profile: dict, state: State, new_offer: float, step_reward: float
) -> InsurerResponse:
    offer_ratio = new_offer / state.max_recoverable if state.max_recoverable > 0 else 0.0
    is_final = state.step + 1 >= state.max_steps or offer_ratio >= 0.95
    personality = profile.get("personality", "bureaucratic")

    if action.action_type == ActionType.ACCEPT_PARTIAL:
        msg = f"We're glad we could reach an agreement. We will process a payment of ${new_offer:,.2f}."
        return InsurerResponse(
            message=_apply_personality(msg, personality, 1.0, True),
            offer_amount=new_offer,
            is_final=True,
        )

    if offer_ratio >= 0.95:
        topic = _extract_argument_topic(action.argument)
        msg = (
            f"After thorough review of your arguments — particularly regarding "
            f"\"{topic}\" — we agree to cover the full disputed amount of "
            f"${new_offer:,.2f}. We apologize for the inconvenience."
        )
        return InsurerResponse(
            message=_apply_personality(msg, personality, 1.0, True),
            offer_amount=new_offer,
            is_final=True,
        )

    topic = _extract_argument_topic(action.argument)
    matched = _matched_concept_names(action.argument, profile["concepts"])
    message = _action_type_response(action, state, step_reward, new_offer, topic, matched)

    if is_final:
        message += " This is our final determination on this matter."

    message = _apply_personality(message, personality, step_reward, is_final)

    return InsurerResponse(message=message, offer_amount=new_offer, is_final=is_final)


def final_score(state: State) -> float:
    if state.max_recoverable <= 0:
        return 0.01
    raw = state.current_offer / state.max_recoverable
    return max(0.01, min(0.99, raw))
