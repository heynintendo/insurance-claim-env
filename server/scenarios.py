from server.models import State

SCENARIOS: dict[str, dict] = {
    # =========================================================================
    # EASY TIER (3 scenarios) — straightforward errors or clear policy violations
    # =========================================================================
    "easy_billing_error": {
        "description": (
            "Patient Jane Smith received an ER visit bill of $4,200. Insurance denied "
            "$3,000 claiming the visit was 'non-emergency'. However, the patient's policy "
            "clearly covers ER visits with a $200 copay, and the visit was for chest pain "
            "requiring immediate evaluation. The denial appears to be a straightforward "
            "billing code error — the claim was submitted under outpatient instead of "
            "emergency. Citing the correct policy section and the billing error should "
            "resolve this quickly."
        ),
        "claim_amount": 4200.0,
        "denied_amount": 3000.0,
        "max_recoverable": 3000.0,
        "difficulty": "easy",
        "personality": "bureaucratic",
        "insurer_profile": {
            "stubbornness": 0.1,
            "policy_sensitivity": 0.9,
            "evidence_sensitivity": 0.6,
            "escalation_sensitivity": 0.4,
            "concepts": [
                {
                    "name": "billing_error",
                    "weight": 1.0,
                    "terms": [
                        "billing code", "billing error", "wrong code", "incorrect code",
                        "miscoded", "coded incorrectly", "submitted as outpatient",
                        "should be emergency", "coding error", "cpt code", "cpt",
                        "procedure code", "claim code", "reclassif", "recod",
                    ],
                },
                {
                    "name": "emergency_coverage",
                    "weight": 0.8,
                    "terms": [
                        "emergency", "er visit", "emergency room", "emergency department",
                        "urgent", "chest pain", "immediate", "life-threatening",
                        "emergent", "acute", "copay", "covered under",
                    ],
                },
                {
                    "name": "policy_reference",
                    "weight": 0.6,
                    "terms": [
                        "policy", "section", "clause", "coverage", "plan",
                        "benefit", "contract", "terms", "provision", "schedule",
                        "covered procedure", "covered service",
                    ],
                },
            ],
        },
    },
    "easy_dental_cleaning": {
        "description": (
            "Patient Tom Rivera had a routine dental cleaning and exam totaling $285. "
            "Insurance denied the $285 claim stating he already used his two covered "
            "cleanings this year. However, his policy covers cleanings every 6 months, "
            "and his last cleaning was 7 months ago — the insurer appears to have "
            "miscounted by including a canceled appointment as a completed visit. The "
            "appointment records and policy frequency limits should clear this up."
        ),
        "claim_amount": 285.0,
        "denied_amount": 285.0,
        "max_recoverable": 285.0,
        "difficulty": "easy",
        "personality": "reasonable",
        "insurer_profile": {
            "stubbornness": 0.1,
            "policy_sensitivity": 0.85,
            "evidence_sensitivity": 0.7,
            "escalation_sensitivity": 0.3,
            "concepts": [
                {
                    "name": "frequency_error",
                    "weight": 1.0,
                    "terms": [
                        "frequency", "canceled appointment", "cancelled", "not completed",
                        "miscounted", "wrong count", "never attended", "no-show",
                        "did not occur", "appointment record", "scheduling error",
                        "only one cleaning", "one visit", "incorrectly logged",
                    ],
                },
                {
                    "name": "coverage_period",
                    "weight": 0.8,
                    "terms": [
                        "every 6 months", "semi-annual", "twice per year", "6 month",
                        "7 months ago", "last cleaning", "interval", "eligible",
                        "coverage period", "benefit period", "calendar year",
                    ],
                },
                {
                    "name": "dental_policy",
                    "weight": 0.5,
                    "terms": [
                        "preventive", "routine", "cleaning", "prophylaxis", "exam",
                        "dental benefit", "dental plan", "covered service",
                        "policy", "schedule of benefits",
                    ],
                },
            ],
        },
    },
    "easy_auto_glass": {
        "description": (
            "Driver Alex Park's windshield was cracked by road debris on the highway. "
            "The replacement cost is $850. Insurance denied the claim classifying it as "
            "'cosmetic damage' not covered under the comprehensive policy. However, a "
            "cracked windshield is a safety hazard per state law, and the policy's "
            "comprehensive coverage explicitly includes glass damage from road hazards. "
            "The denial letter even references the wrong policy section. Pointing out the "
            "safety requirement and correct policy section should resolve this."
        ),
        "claim_amount": 850.0,
        "denied_amount": 850.0,
        "max_recoverable": 850.0,
        "difficulty": "easy",
        "personality": "passive_aggressive",
        "insurer_profile": {
            "stubbornness": 0.15,
            "policy_sensitivity": 0.85,
            "evidence_sensitivity": 0.5,
            "escalation_sensitivity": 0.4,
            "concepts": [
                {
                    "name": "glass_coverage",
                    "weight": 1.0,
                    "terms": [
                        "comprehensive", "glass coverage", "windshield", "glass damage",
                        "road debris", "road hazard", "flying object", "comprehensive coverage",
                        "full glass", "auto glass", "not cosmetic", "structural",
                    ],
                },
                {
                    "name": "safety_requirement",
                    "weight": 0.8,
                    "terms": [
                        "safety", "safety hazard", "state law", "inspection",
                        "driving hazard", "visibility", "obstruct", "crack",
                        "legal requirement", "road safety", "unsafe", "impair",
                    ],
                },
                {
                    "name": "wrong_denial_basis",
                    "weight": 0.7,
                    "terms": [
                        "wrong section", "incorrect reference", "wrong policy",
                        "misclassif", "not cosmetic", "denial error", "wrong category",
                        "incorrectly categorized", "mischaracteriz", "error in denial",
                    ],
                },
            ],
        },
    },

    # =========================================================================
    # MEDIUM TIER (3 scenarios) — ambiguous policy language or partial denials
    # =========================================================================
    "medium_partial_denial": {
        "description": (
            "Patient Robert Chen had knee surgery costing $18,500. Insurance approved "
            "$10,000 but denied $8,500, claiming the specific surgical technique (robotic-"
            "assisted arthroscopy) was 'experimental' and not covered. The policy language "
            "is ambiguous — it covers 'arthroscopic procedures' but doesn't explicitly "
            "mention robotic assistance. The surgeon chose this method as medically "
            "necessary due to the patient's prior knee damage. You'll need to argue that "
            "robotic assistance is a tool used during a covered procedure, not a separate "
            "experimental treatment, and provide supporting medical evidence."
        ),
        "claim_amount": 18500.0,
        "denied_amount": 8500.0,
        "max_recoverable": 8500.0,
        "difficulty": "medium",
        "personality": "bureaucratic",
        "insurer_profile": {
            "stubbornness": 0.3,
            "policy_sensitivity": 0.6,
            "evidence_sensitivity": 0.8,
            "escalation_sensitivity": 0.5,
            "concepts": [
                {
                    "name": "procedure_coverage",
                    "weight": 1.0,
                    "terms": [
                        "arthroscop", "covered procedure", "not experimental",
                        "standard of care", "fda approved", "fda clearance",
                        "robotic assist", "surgical tool", "surgical instrument",
                        "tool used during", "method of performing", "technique",
                        "not a separate procedure", "same procedure",
                    ],
                },
                {
                    "name": "medical_necessity",
                    "weight": 0.9,
                    "terms": [
                        "medically necessary", "medical necessity", "surgeon recommend",
                        "surgeon determined", "clinical judgment", "prior damage",
                        "knee damage", "patient history", "clinical indication",
                        "required due to", "necessary because", "physician",
                    ],
                },
                {
                    "name": "policy_ambiguity",
                    "weight": 0.7,
                    "terms": [
                        "ambiguous", "not explicitly excluded", "does not exclude",
                        "silent on", "broadly covers", "general language",
                        "interpret", "reasonable reading", "policy language",
                        "doesn't mention", "doesn't specify",
                    ],
                },
            ],
        },
    },
    "medium_travel_emergency": {
        "description": (
            "Traveler Sarah Kim was hospitalized for appendicitis while on vacation in "
            "Costa Rica. The emergency surgery and 3-day hospital stay cost $12,400. Her "
            "travel insurance denied the claim arguing the hospital was 'out of network' "
            "and she should have sought pre-authorization. However, appendicitis is a "
            "medical emergency that requires immediate surgery — pre-authorization is not "
            "feasible when you're being rushed into an OR. The policy has an emergency "
            "exception clause but the insurer is interpreting it narrowly. You'll need to "
            "establish the emergency nature and argue the network requirement doesn't apply "
            "to life-threatening situations abroad."
        ),
        "claim_amount": 12400.0,
        "denied_amount": 12400.0,
        "max_recoverable": 11000.0,
        "difficulty": "medium",
        "personality": "aggressive",
        "insurer_profile": {
            "stubbornness": 0.3,
            "policy_sensitivity": 0.65,
            "evidence_sensitivity": 0.7,
            "escalation_sensitivity": 0.5,
            "concepts": [
                {
                    "name": "emergency_exception",
                    "weight": 1.0,
                    "terms": [
                        "emergency", "emergency exception", "emergency clause",
                        "life-threatening", "immediate surgery", "acute",
                        "appendicitis", "appendectomy", "urgent", "emergent",
                        "cannot wait", "no time", "rushed to surgery",
                    ],
                },
                {
                    "name": "pre_auth_infeasible",
                    "weight": 0.9,
                    "terms": [
                        "pre-authorization", "preauthorization", "prior authorization",
                        "not feasible", "impossible to obtain", "no time to call",
                        "unconscious", "emergency admission", "immediate treatment",
                        "stabilization", "could not delay", "life at risk",
                    ],
                },
                {
                    "name": "network_inapplicable",
                    "weight": 0.8,
                    "terms": [
                        "out of network", "no network abroad", "foreign hospital",
                        "international", "overseas", "no in-network option",
                        "costa rica", "abroad", "travel", "foreign country",
                        "nearest facility", "only available hospital",
                    ],
                },
            ],
        },
    },
    "medium_homeowners_pipe": {
        "description": (
            "Homeowner David Okafor discovered water damage in his basement after a pipe "
            "burst during a cold snap. Repairs and remediation total $15,800. Insurance "
            "denied the claim categorizing it as 'flood damage' which is excluded under "
            "his homeowners policy. However, this was not a flood — it was a burst pipe "
            "due to freezing, which is a named peril covered under his HO-3 policy. The "
            "insurer seems to be conflating all water damage with flooding. You'll need "
            "to distinguish between flood damage and pipe burst damage, cite the correct "
            "peril category, and potentially provide a plumber's report."
        ),
        "claim_amount": 15800.0,
        "denied_amount": 15800.0,
        "max_recoverable": 14500.0,
        "difficulty": "medium",
        "personality": "passive_aggressive",
        "insurer_profile": {
            "stubbornness": 0.25,
            "policy_sensitivity": 0.7,
            "evidence_sensitivity": 0.75,
            "escalation_sensitivity": 0.45,
            "concepts": [
                {
                    "name": "peril_distinction",
                    "weight": 1.0,
                    "terms": [
                        "burst pipe", "frozen pipe", "pipe burst", "freezing",
                        "not a flood", "not flood", "internal water", "plumbing",
                        "plumbing failure", "pipe failure", "cold snap",
                        "frozen", "ice", "water supply line", "internal",
                    ],
                },
                {
                    "name": "named_peril",
                    "weight": 0.9,
                    "terms": [
                        "named peril", "ho-3", "ho3", "covered peril",
                        "freezing of plumbing", "water damage", "sudden and accidental",
                        "accidental discharge", "dwelling coverage", "homeowners policy",
                        "peril", "covered cause of loss",
                    ],
                },
                {
                    "name": "professional_assessment",
                    "weight": 0.7,
                    "terms": [
                        "plumber", "plumber's report", "inspection", "assessment",
                        "professional opinion", "contractor", "remediation report",
                        "cause of damage", "damage report", "expert opinion",
                    ],
                },
            ],
        },
    },

    # =========================================================================
    # HARD TIER (3 scenarios) — multi-step legal arguments, stubborn insurers
    # =========================================================================
    "hard_full_denial": {
        "description": (
            "Patient Maria Gonzalez was hospitalized for 12 days following complications "
            "from a chronic condition (lupus flare with kidney involvement). Total bill: "
            "$67,000. Insurance denied the entire claim stating the hospitalization was "
            "for a 'pre-existing condition' excluded under a waiting period clause. "
            "However, the patient has been continuously covered for 14 months, and federal "
            "regulations (ACA) prohibit pre-existing condition exclusions for plans that "
            "began after 2014. The insurer is also arguing that days 8-12 were not "
            "'medically necessary'. This requires multi-step legal argumentation: first "
            "defeat the pre-existing condition exclusion, then justify the full length of "
            "stay with medical evidence, and potentially escalate to regulatory threat."
        ),
        "claim_amount": 67000.0,
        "denied_amount": 67000.0,
        "max_recoverable": 67000.0,
        "difficulty": "hard",
        "personality": "aggressive",
        "insurer_profile": {
            "stubbornness": 0.5,
            "policy_sensitivity": 0.5,
            "evidence_sensitivity": 0.6,
            "escalation_sensitivity": 0.7,
            "concepts": [
                {
                    "name": "aca_compliance",
                    "weight": 1.0,
                    "terms": [
                        "affordable care act", "aca", "federal law", "federal regulation",
                        "pre-existing condition", "preexisting", "pre existing",
                        "illegal exclusion", "cannot deny", "prohibited",
                        "unlawful", "2014", "patient protection",
                    ],
                },
                {
                    "name": "continuous_coverage",
                    "weight": 0.8,
                    "terms": [
                        "continuous coverage", "continuously covered", "14 months",
                        "waiting period", "enrollment", "coverage gap",
                        "no lapse", "without interruption", "maintained coverage",
                        "active policy", "effective date",
                    ],
                },
                {
                    "name": "medical_necessity_stay",
                    "weight": 0.9,
                    "terms": [
                        "medically necessary", "medical necessity", "lupus",
                        "kidney", "renal", "complication", "hospitalization required",
                        "length of stay", "12 days", "days 8", "clinical record",
                        "medical record", "physician documentation", "flare",
                        "organ involvement", "inpatient",
                    ],
                },
                {
                    "name": "regulatory_threat",
                    "weight": 0.6,
                    "terms": [
                        "department of insurance", "state regulator", "complaint",
                        "attorney general", "bad faith", "regulatory",
                        "commissioner", "appeal", "external review", "legal action",
                        "lawsuit", "cms", "hhs",
                    ],
                },
            ],
        },
    },
    "hard_disability_mental": {
        "description": (
            "Software engineer Priya Nair filed a long-term disability claim after being "
            "diagnosed with severe major depressive disorder and generalized anxiety that "
            "left her unable to work. Her employer-provided disability policy pays 60% of "
            "salary ($7,200/month). The insurer denied the claim stating she 'does not meet "
            "the definition of total disability' and that mental health conditions are "
            "limited to 24 months under the policy. However, Priya's condition has lasted "
            "8 months so far (well within 24 months), and three treating physicians have "
            "documented her functional limitations. The insurer appears to be applying the "
            "24-month cap retroactively and ignoring the clinical evidence of functional "
            "impairment. You must establish functional limitations with medical evidence, "
            "challenge the misapplication of the mental health limitation, and push for "
            "peer review of the clinical documentation."
        ),
        "claim_amount": 57600.0,
        "denied_amount": 57600.0,
        "max_recoverable": 50000.0,
        "difficulty": "hard",
        "personality": "passive_aggressive",
        "insurer_profile": {
            "stubbornness": 0.5,
            "policy_sensitivity": 0.45,
            "evidence_sensitivity": 0.7,
            "escalation_sensitivity": 0.6,
            "concepts": [
                {
                    "name": "functional_limitations",
                    "weight": 1.0,
                    "terms": [
                        "functional limitation", "unable to work", "cannot perform",
                        "functional capacity", "cognitive impairment", "concentration",
                        "cannot focus", "daily activities", "work duties",
                        "occupational function", "impaired", "incapacitated",
                        "disability assessment", "functional evaluation",
                    ],
                },
                {
                    "name": "clinical_evidence",
                    "weight": 0.9,
                    "terms": [
                        "treating physician", "psychiatrist", "therapist",
                        "clinical documentation", "medical records", "diagnosis",
                        "major depressive", "depression", "anxiety", "dsm",
                        "three physicians", "three doctors", "clinical evidence",
                        "treatment records", "physician statement",
                    ],
                },
                {
                    "name": "policy_misapplication",
                    "weight": 0.85,
                    "terms": [
                        "24 month", "mental health limitation", "within the limit",
                        "8 months", "retroactive", "misapplied", "misapplication",
                        "incorrect interpretation", "not yet reached", "cap",
                        "limitation period", "still within", "has not exceeded",
                    ],
                },
                {
                    "name": "peer_review_demand",
                    "weight": 0.6,
                    "terms": [
                        "peer review", "independent review", "independent medical",
                        "ime", "qualified reviewer", "board certified",
                        "specialty review", "psychiatry review", "mental health expert",
                        "external review", "fair evaluation",
                    ],
                },
            ],
        },
    },
    "hard_dental_implant": {
        "description": (
            "Patient James Whitfield needs a dental implant ($4,800) after losing a molar "
            "due to an infection that required emergency extraction. Insurance denied the "
            "implant as 'cosmetic' and suggests a cheaper partial denture ($600) instead. "
            "However, the implant is restorative — not cosmetic — because the missing tooth "
            "causes bone loss and bite misalignment that will lead to further dental "
            "problems. The treating dentist and an oral surgeon both recommend the implant "
            "as the standard of care. The policy covers 'restorative procedures' but has "
            "ambiguous language around implants. You need to establish the implant as "
            "medically necessary restorative care, distinguish it from cosmetic work, and "
            "argue that the cheaper alternative creates long-term harm."
        ),
        "claim_amount": 4800.0,
        "denied_amount": 4200.0,
        "max_recoverable": 3800.0,
        "difficulty": "hard",
        "personality": "reasonable",
        "insurer_profile": {
            "stubbornness": 0.45,
            "policy_sensitivity": 0.55,
            "evidence_sensitivity": 0.7,
            "escalation_sensitivity": 0.55,
            "concepts": [
                {
                    "name": "restorative_not_cosmetic",
                    "weight": 1.0,
                    "terms": [
                        "restorative", "not cosmetic", "functional", "restoration",
                        "tooth replacement", "missing tooth", "lost tooth",
                        "necessary restoration", "functional restoration",
                        "structural", "chewing function", "bite",
                    ],
                },
                {
                    "name": "medical_necessity_implant",
                    "weight": 0.9,
                    "terms": [
                        "bone loss", "bone deterioration", "resorption",
                        "bite misalignment", "malocclusion", "further damage",
                        "standard of care", "dentist recommend", "oral surgeon",
                        "medically necessary", "long-term", "prevent",
                    ],
                },
                {
                    "name": "cheaper_alternative_harm",
                    "weight": 0.7,
                    "terms": [
                        "denture", "partial denture", "inferior", "inadequate",
                        "long-term harm", "bone continues", "additional procedures",
                        "future cost", "complications", "not equivalent",
                        "poor outcome", "substandard",
                    ],
                },
                {
                    "name": "professional_opinions",
                    "weight": 0.6,
                    "terms": [
                        "dentist", "oral surgeon", "specialist", "professional opinion",
                        "clinical recommendation", "treating provider", "expert",
                        "two providers", "both recommend", "clinical judgment",
                    ],
                },
            ],
        },
    },

    # =========================================================================
    # EXPERT TIER (3 scenarios) — complex multi-vector arguments, very stubborn
    # =========================================================================
    "expert_auto_diminished_value": {
        "description": (
            "After a rear-end collision that wasn't her fault, driver Lisa Yamamoto's car "
            "was repaired for $9,200 (paid by the at-fault driver's insurer). However, "
            "the car — a 2-year-old sedan worth $34,000 before the accident — now has a "
            "permanent accident history that reduces its resale value by an estimated "
            "$6,800. Lisa filed a diminished value claim for $6,800. The insurer denied it "
            "outright, claiming repairs 'restored the vehicle to pre-accident condition' "
            "and that diminished value is 'speculative'. However, the state recognizes "
            "inherent diminished value claims, and multiple dealer appraisals confirm the "
            "value loss. The insurer is banking on claimants not knowing their rights. "
            "You'll need to cite state case law on diminished value, provide appraisal "
            "evidence, argue that repair history objectively reduces market value, and "
            "potentially threaten a bad faith complaint if they continue stonewalling."
        ),
        "claim_amount": 6800.0,
        "denied_amount": 6800.0,
        "max_recoverable": 5500.0,
        "difficulty": "expert",
        "personality": "aggressive",
        "insurer_profile": {
            "stubbornness": 0.6,
            "policy_sensitivity": 0.4,
            "evidence_sensitivity": 0.65,
            "escalation_sensitivity": 0.7,
            "concepts": [
                {
                    "name": "diminished_value_law",
                    "weight": 1.0,
                    "terms": [
                        "diminished value", "inherent diminished value", "dv claim",
                        "case law", "state law", "precedent", "court ruling",
                        "legal right", "recognized claim", "tort", "damages",
                        "third-party claim", "not-at-fault",
                    ],
                },
                {
                    "name": "market_value_evidence",
                    "weight": 0.9,
                    "terms": [
                        "appraisal", "dealer appraisal", "market value",
                        "resale value", "carfax", "autocheck", "accident history",
                        "vehicle history report", "comparable sales",
                        "kelley blue book", "kbb", "nada", "trade-in value",
                    ],
                },
                {
                    "name": "repair_doesnt_restore_value",
                    "weight": 0.8,
                    "terms": [
                        "repair history", "repaired does not equal", "stigma",
                        "accident record", "permanent record", "buyer perception",
                        "would you pay full price", "disclosure requirement",
                        "material fact", "cannot undo", "still shows",
                    ],
                },
                {
                    "name": "bad_faith_pressure",
                    "weight": 0.65,
                    "terms": [
                        "bad faith", "unfair claim practice", "stonewalling",
                        "department of insurance", "regulatory complaint",
                        "attorney", "lawyer", "legal action", "sue",
                        "claims handling", "duty to settle", "good faith",
                    ],
                },
            ],
        },
    },
    "expert_homeowners_mold": {
        "description": (
            "After a covered water heater burst caused significant water damage to their "
            "home, homeowners Pat and Chris Sawyer discovered extensive mold growth 6 weeks "
            "later. The water damage repairs ($11,000) were approved and paid, but the mold "
            "remediation ($23,500) was denied under the policy's mold exclusion. The "
            "homeowners argue this mold is a direct consequence of the covered water event "
            "and would not exist otherwise — the policy's 'ensuing loss' provision should "
            "apply. The insurer points to the blanket mold exclusion and argues the "
            "homeowners waited too long to discover it. This requires arguing that ensuing "
            "loss doctrine overrides the mold exclusion when mold results from a covered "
            "peril, providing timeline evidence that discovery was reasonable, citing the "
            "original approved claim as proof of the covered cause, and potentially filing "
            "a formal appeal with state insurance department backing."
        ),
        "claim_amount": 23500.0,
        "denied_amount": 23500.0,
        "max_recoverable": 18000.0,
        "difficulty": "expert",
        "personality": "bureaucratic",
        "insurer_profile": {
            "stubbornness": 0.6,
            "policy_sensitivity": 0.5,
            "evidence_sensitivity": 0.6,
            "escalation_sensitivity": 0.65,
            "concepts": [
                {
                    "name": "ensuing_loss_doctrine",
                    "weight": 1.0,
                    "terms": [
                        "ensuing loss", "ensuing damage", "resulting from",
                        "direct consequence", "caused by", "proximate cause",
                        "chain of causation", "but-for", "covered peril caused",
                        "would not exist", "originated from", "traceable to",
                    ],
                },
                {
                    "name": "covered_origin_event",
                    "weight": 0.9,
                    "terms": [
                        "water heater", "burst", "water damage", "original claim",
                        "already approved", "already paid", "covered event",
                        "covered peril", "same incident", "same event",
                        "prior approval", "claim number",
                    ],
                },
                {
                    "name": "reasonable_discovery",
                    "weight": 0.8,
                    "terms": [
                        "6 weeks", "discovery", "hidden", "behind walls",
                        "not visible", "concealed", "reasonable time",
                        "could not have known", "latent", "mold growth takes time",
                        "incubation", "no way to detect", "timeline",
                    ],
                },
                {
                    "name": "exclusion_override",
                    "weight": 0.7,
                    "terms": [
                        "mold exclusion", "exclusion does not apply", "exception",
                        "override", "ensuing loss overrides", "anti-concurrent",
                        "concurrent causation", "cannot exclude", "covered cause",
                        "blanket exclusion", "overbroad", "state law",
                    ],
                },
            ],
        },
    },
    "expert_health_balance_billing": {
        "description": (
            "Patient Andre Washington had emergency heart surgery at the nearest hospital "
            "after a cardiac event. The hospital was in-network but the surgeon assigned "
            "to his case was out-of-network. Total surgical charges: $45,000. Insurance "
            "paid the in-network rate of $18,000 and the surgeon is balance billing Andre "
            "for $27,000. Andre's state has a surprise billing protection law (similar to "
            "the federal No Surprises Act) that should prevent balance billing for "
            "emergency services. The insurer claims the law only applies to facility fees, "
            "not physician charges, which is an incorrect reading of the statute. This "
            "requires citing the specific surprise billing protections, arguing that "
            "emergency patients cannot choose their surgeon, providing the legislative "
            "text showing physician services are covered, and escalating through both "
            "the formal appeals process and regulatory channels."
        ),
        "claim_amount": 27000.0,
        "denied_amount": 27000.0,
        "max_recoverable": 25000.0,
        "difficulty": "expert",
        "personality": "passive_aggressive",
        "insurer_profile": {
            "stubbornness": 0.65,
            "policy_sensitivity": 0.45,
            "evidence_sensitivity": 0.5,
            "escalation_sensitivity": 0.75,
            "concepts": [
                {
                    "name": "surprise_billing_law",
                    "weight": 1.0,
                    "terms": [
                        "no surprises act", "surprise billing", "balance billing",
                        "surprise billing law", "state law", "federal law",
                        "balance bill protection", "prohibition", "illegal",
                        "statute", "legislation", "consumer protection",
                    ],
                },
                {
                    "name": "emergency_no_choice",
                    "weight": 0.9,
                    "terms": [
                        "emergency", "no choice", "cannot choose surgeon",
                        "assigned surgeon", "cardiac event", "heart surgery",
                        "life-threatening", "did not choose", "involuntary",
                        "emergency admission", "no opportunity to select",
                        "unconscious", "incapacitated",
                    ],
                },
                {
                    "name": "physician_services_covered",
                    "weight": 0.85,
                    "terms": [
                        "physician services", "physician charges", "surgeon fee",
                        "professional fee", "not just facility", "includes physicians",
                        "all providers", "all services", "legislative text",
                        "statutory language", "plain reading", "congressional intent",
                    ],
                },
                {
                    "name": "regulatory_escalation",
                    "weight": 0.7,
                    "terms": [
                        "department of insurance", "state regulator", "cms",
                        "formal appeal", "external review", "independent review",
                        "attorney general", "complaint", "enforcement",
                        "regulatory complaint", "bad faith", "violation",
                    ],
                },
            ],
        },
    },
}


def get_scenario(task_id: str) -> State:
    if task_id not in SCENARIOS:
        raise ValueError(f"Unknown task_id: {task_id}. Available: {list(SCENARIOS.keys())}")
    s = SCENARIOS[task_id]
    return State(
        task_id=task_id,
        description=s["description"],
        claim_amount=s["claim_amount"],
        denied_amount=s["denied_amount"],
        max_recoverable=s["max_recoverable"],
        current_offer=0.0,
        step=0,
        difficulty=s["difficulty"],
    )


def get_insurer_profile(task_id: str) -> dict:
    scenario = SCENARIOS[task_id]
    profile = scenario["insurer_profile"].copy()
    profile["personality"] = scenario.get("personality", "bureaucratic")
    return profile


def list_task_ids() -> list[str]:
    return list(SCENARIOS.keys())
