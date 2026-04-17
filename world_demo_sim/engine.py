from __future__ import annotations

import math
from copy import deepcopy
from typing import Dict, List, Tuple

import numpy as np

from .io_helpers import clamp, sigmoid, weighted_average
from .selection import expand_event_country_effects
from .types import ScenarioRunResult


State = Dict[str, float]
DOMESTIC_STAGES = [
    "stable",
    "grievance",
    "protest",
    "mass_protest",
    "riot",
    "insurgency",
    "civil_conflict",
]
DOMESTIC_STAGE_INDEX = {name: idx for idx, name in enumerate(DOMESTIC_STAGES)}


def domestic_stage_name(index: int | float) -> str:
    bounded = max(0, min(int(index), len(DOMESTIC_STAGES) - 1))
    return DOMESTIC_STAGES[bounded]


def build_initial_states(config: dict) -> Dict[str, State]:
    states: Dict[str, State] = {}
    defaults = {
        "energy_exporter": False,
        "military_capacity": 0.50,
        "regime_rigidity": 0.40,
        "revisionism": 0.30,
        "gray_zone_capability": 0.40,
        "nuclear_deterrent": 0.0,
        "war_burden": 0.0,
        "military_posture": 0.0,
        "domestic_burden": 0.0,
    }
    for country in config["countries"]:
        state = deepcopy(country)
        for key, value in defaults.items():
            state.setdefault(key, value)

        state.setdefault(
            "tax_burden",
            clamp(0.20 + 0.12 * state["institutional_capacity"] + 0.08 * state["conflict_risk"]),
        )
        state.setdefault(
            "housing_pressure",
            clamp(0.18 + 0.24 * state["import_dependency"] + 0.20 * state["inequality_pressure"]),
        )
        state.setdefault(
            "youth_unemployment",
            clamp(0.08 + 0.28 * state["labor_displacement"] + 0.18 * state["inequality_pressure"]),
        )
        state.setdefault(
            "policing_capacity",
            clamp(
                0.38 * state["institutional_capacity"]
                + 0.32 * state["military_capacity"]
                + 0.30 * state["regime_rigidity"]
            ),
        )
        state.setdefault(
            "elite_cohesion",
            clamp(
                0.36 * state["institutional_capacity"]
                + 0.24 * state["capital_surplus"]
                + 0.22 * state["regime_rigidity"]
                + 0.18 * (1.0 - state["sanction_exposure"])
            ),
        )

        initial_economic_stress = clamp(
            0.28 * max(0.0, 1.0 - state["cash_stability"])
            + 0.22 * state["labor_displacement"]
            + 0.18 * state["inequality_pressure"]
            + 0.16 * state["housing_pressure"]
            + 0.08 * state["tax_burden"]
            + 0.08 * state["conflict_risk"]
        )
        initial_legitimacy_stress = clamp(
            0.30 * max(0.0, 1.0 - state["institutional_capacity"])
            + 0.24 * max(0.0, 1.0 - state["social_cohesion"])
            + 0.20 * state["inequality_pressure"]
            + 0.14 * max(0.0, 1.0 - state["elite_cohesion"])
            + 0.12 * state["sanction_exposure"]
        )
        initial_grievance = clamp(0.58 * initial_economic_stress + 0.42 * initial_legitimacy_stress)
        initial_stage_index = 1 if initial_grievance >= 0.48 else 0

        state.setdefault("economic_stress", initial_economic_stress)
        state.setdefault("legitimacy_stress", initial_legitimacy_stress)
        state.setdefault(
            "mobilization_capacity",
            clamp(
                0.30 * state["compute_access"]
                + 0.18 * state["population_weight"]
                + 0.16 * state["social_cohesion"]
                + 0.18 * (1.0 - state["regime_rigidity"])
                + 0.18 * state["youth_unemployment"]
            ),
        )
        state.setdefault(
            "elite_fragmentation",
            clamp(
                0.40 * max(0.0, 1.0 - state["elite_cohesion"])
                + 0.24 * state["inequality_pressure"]
                + 0.18 * state["sanction_exposure"]
                + 0.18 * max(0.0, 1.0 - state["institutional_capacity"])
            ),
        )
        state.setdefault(
            "communal_polarization",
            clamp(
                0.46 * max(0.0, 1.0 - state["social_cohesion"])
                + 0.22 * state["conflict_risk"]
                + 0.20 * state["inequality_pressure"]
                + 0.12 * state["sanction_exposure"]
            ),
        )
        state.setdefault("grievance_pressure", initial_grievance)
        state.setdefault("protest_pressure", clamp(initial_grievance * 0.78))
        state.setdefault("riot_pressure", clamp(initial_grievance * 0.58))
        state.setdefault("civil_conflict_pressure", clamp(initial_grievance * 0.38))
        state.setdefault("domestic_diversion_incentive", clamp(initial_grievance * 0.44))
        state.setdefault("domestic_stage_index", initial_stage_index)
        state["domestic_stage"] = domestic_stage_name(state["domestic_stage_index"])
        state["domestic_burden"] = clamp(
            max(state["domestic_burden"], 0.025 * int(state["domestic_stage_index"]))
        )
        states[state["code"]] = state
    return states


def metric_snapshot(state: State) -> Dict[str, float]:
    dependency_risk = clamp(state["import_dependency"] * (1.0 - state["supply_chain_resilience"]))
    displacement_gap = max(0.0, state["labor_displacement"] - state["distribution_capacity"])

    M = (
        0.15 * state["energy_security"]
        + 0.10 * state["food_security"]
        + 0.11 * state["compute_access"]
        + 0.14 * state["institutional_capacity"]
        + 0.10 * state["social_cohesion"]
        + 0.08 * state["alliance_support"]
        + 0.11 * state["distribution_capacity"]
        + 0.08 * state["supply_chain_resilience"]
        + 0.05 * state["capital_surplus"]
        + 0.05 * (1.0 - state["war_burden"])
        + 0.05 * (1.0 - state["domestic_burden"])
    )
    L = (
        0.16 * state["labor_displacement"]
        + 0.12 * state["inequality_pressure"]
        + 0.12 * state["conflict_risk"]
        + 0.11 * state["sanction_exposure"]
        + 0.09 * state["climate_stress"]
        + 0.11 * dependency_risk
        + 0.10 * state["war_burden"]
        + 0.11 * state["domestic_burden"]
        + 0.09 * max(0.0, 1.0 - state["cash_stability"])
        + 0.05 * state["protest_pressure"]
        + 0.04 * state["riot_pressure"]
    )
    S = M * math.exp(-L)
    horizon = max(
        0.0,
        2.0
        + 10.0 * S
        + 1.6 * state["distribution_capacity"]
        + 1.1 * state["alliance_support"]
        - 2.7 * displacement_gap
        - 2.2 * state["conflict_risk"]
        - 1.7 * state["war_burden"],
        - 1.5 * state["domestic_burden"],
    )
    support_needed = clamp(
        (0.72 - S) * 0.75
        + displacement_gap * 0.55
        + state["conflict_risk"] * 0.20
        + dependency_risk * 0.20
        + state["war_burden"] * 0.22
        + state["domestic_burden"] * 0.28
        + state["protest_pressure"] * 0.12,
        0.0,
        1.0,
    )

    return {
        "M": round(M, 4),
        "L": round(L, 4),
        "S": round(S, 4),
        "dependency_risk": round(dependency_risk, 4),
        "displacement_gap": round(displacement_gap, 4),
        "horizon_turns": round(horizon, 2),
        "support_needed": round(support_needed, 4),
        "domestic_stage": state["domestic_stage"],
    }


def apply_country_effects(states: Dict[str, State], effects: dict) -> None:
    for code, deltas in effects.items():
        if code not in states:
            continue
        for key, delta in deltas.items():
            states[code][key] = clamp(states[code][key] + delta)


def self_update(state: State, scenario: dict, modifiers: dict) -> Dict[str, float]:
    state["war_burden"] = clamp(state["war_burden"] * 0.82)
    state["domestic_burden"] = clamp(state["domestic_burden"] * 0.84)
    state["military_posture"] = clamp(
        state["military_posture"] * 0.86 + 0.03 * state["revisionism"] + 0.01 * state["conflict_risk"]
    )

    automation_push = (
        scenario["automation_velocity"]
        * state["automation_exposure"]
        * (0.55 + 0.45 * state["compute_access"])
    )
    physical_push = (
        scenario["physical_automation_velocity"]
        * state["physical_exposure"]
        * (0.55 + 0.45 * state["energy_security"])
    )
    displacement_bump = (
        0.62 * automation_push
        + 0.38 * physical_push
        + modifiers.get("labor_displacement_bonus", 0.0)
    )
    state["labor_displacement"] = clamp(state["labor_displacement"] + displacement_bump)

    adaptation_absorption = scenario["adaptation_velocity"] * (
        0.34 * state["distribution_capacity"]
        + 0.24 * state["institutional_capacity"]
        + 0.22 * state["social_cohesion"]
        + 0.20 * state["capital_surplus"]
    )
    structure_credit_gain = (
        scenario["structure_credit_intensity"] + modifiers.get("structure_credit_bonus", 0.0)
    ) * (
        0.30 * state["institutional_capacity"]
        + 0.25 * state["distribution_capacity"]
        + 0.20 * state["social_cohesion"]
        + 0.15 * state["alliance_support"]
        + 0.10 * state["capital_surplus"]
    )
    capital_share_gain = (
        scenario["winner_reinvestment"] + modifiers.get("winner_reinvestment_bonus", 0.0)
    ) * 0.35 * max(0.0, state["capital_surplus"] - 0.55)

    effective_buffer = adaptation_absorption + structure_credit_gain + capital_share_gain
    displacement_gap = max(0.0, state["labor_displacement"] - effective_buffer)
    war_drag = state["war_burden"] * (0.65 + 0.35 * state["import_dependency"])

    state["distribution_capacity"] = clamp(
        state["distribution_capacity"]
        + 0.020 * scenario["adaptation_velocity"]
        + 0.055 * structure_credit_gain
        - 0.020 * war_drag
    )
    state["social_cohesion"] = clamp(
        state["social_cohesion"]
        - 0.060 * displacement_gap
        + 0.050 * structure_credit_gain
        + 0.015 * scenario["adaptation_velocity"]
        - 0.040 * war_drag
    )
    state["cash_stability"] = clamp(
        state["cash_stability"]
        - 0.080 * displacement_gap
        + 0.020 * capital_share_gain
        - 0.015 * state["sanction_exposure"]
        - 0.010 * state["conflict_risk"]
        - 0.070 * war_drag
    )
    state["inequality_pressure"] = clamp(
        state["inequality_pressure"]
        + 0.070 * displacement_gap
        - 0.045 * structure_credit_gain
        + 0.025 * war_drag
    )
    state["conflict_risk"] = clamp(
        state["conflict_risk"]
        + 0.055 * displacement_gap
        + 0.020 * state["sanction_exposure"]
        + 0.020 * state["climate_stress"]
        + 0.050 * state["war_burden"]
        - 0.020 * state["alliance_support"]
    )
    state["supply_chain_resilience"] = clamp(
        state["supply_chain_resilience"]
        + 0.018 * scenario["winner_reinvestment"]
        + 0.010 * scenario["adaptation_velocity"]
        - 0.010 * state["import_dependency"] * (1.0 - state["alliance_support"])
        - 0.045 * war_drag
    )
    state["capital_surplus"] = clamp(
        state["capital_surplus"]
        + 0.020 * state["cash_stability"]
        - 0.035 * structure_credit_gain
        - 0.025 * max(0.0, displacement_gap - 0.15)
        - 0.050 * war_drag
    )
    state["alliance_support"] = clamp(
        state["alliance_support"]
        + 0.010 * scenario["cooperation_bias"]
        - 0.010 * state["conflict_risk"]
        + 0.015 * state["war_burden"]
    )
    state["military_posture"] = clamp(
        state["military_posture"]
        + 0.020 * scenario.get("war_risk_bias", 0.0)
        + 0.010 * state["conflict_risk"]
        - 0.008 * scenario.get("deescalation_capacity", 0.0)
    )
    state["youth_unemployment"] = clamp(
        state["youth_unemployment"]
        + 0.38 * displacement_bump
        - 0.24 * effective_buffer
        + 0.04 * state["domestic_burden"]
    )
    state["housing_pressure"] = clamp(
        state["housing_pressure"]
        + 0.04 * displacement_gap
        + 0.02 * state["climate_stress"]
        - 0.02 * capital_share_gain
        - 0.01 * structure_credit_gain
    )
    state["tax_burden"] = clamp(
        state["tax_burden"]
        + 0.02 * state["war_burden"]
        + 0.01 * state["domestic_burden"]
        - 0.01 * capital_share_gain
    )
    state["policing_capacity"] = clamp(
        0.40 * state["institutional_capacity"]
        + 0.32 * state["military_capacity"]
        + 0.28 * state["regime_rigidity"]
        - 0.05 * state["domestic_burden"]
    )
    state["elite_cohesion"] = clamp(
        state["elite_cohesion"]
        + 0.020 * state["capital_surplus"]
        - 0.030 * state["inequality_pressure"]
        - 0.020 * state["sanction_exposure"]
        - 0.025 * state["domestic_burden"]
    )

    return {
        "adaptation_absorption": round(adaptation_absorption, 4),
        "structure_credit_gain": round(structure_credit_gain, 4),
        "capital_share_gain": round(capital_share_gain, 4),
        "displacement_bump": round(displacement_bump, 4),
        "displacement_gap_after_buffer": round(displacement_gap, 4),
        "war_drag": round(war_drag, 4),
    }


def apply_cooperation(
    states: Dict[str, State],
    links: List[dict],
    scenario: dict,
    modifiers: dict,
) -> List[dict]:
    cooperation_bias = scenario["cooperation_bias"] + modifiers.get("cooperation_bonus", 0.0)
    transfers: List[dict] = []

    for link in links:
        donor = states[link["donor"]]
        target = states[link["target"]]
        donor_excess = max(0.0, donor["capital_surplus"] - 0.58)
        if donor_excess <= 0.0 or cooperation_bias <= 0.0:
            continue

        amount = donor_excess * link["weight"] * cooperation_bias * 0.45
        if amount <= 0.004:
            continue

        donor["capital_surplus"] = clamp(donor["capital_surplus"] - amount * 0.40)
        donor["cash_stability"] = clamp(donor["cash_stability"] + amount * 0.015)
        donor["supply_chain_resilience"] = clamp(donor["supply_chain_resilience"] + amount * 0.020)

        target["distribution_capacity"] = clamp(target["distribution_capacity"] + amount * 0.28)
        target["supply_chain_resilience"] = clamp(target["supply_chain_resilience"] + amount * 0.24)
        target["alliance_support"] = clamp(target["alliance_support"] + amount * 0.22)
        target["social_cohesion"] = clamp(target["social_cohesion"] + amount * 0.16)
        if donor.get("energy_exporter"):
            target["energy_security"] = clamp(target["energy_security"] + amount * 0.14)

        transfers.append(
            {
                "donor": link["donor"],
                "target": link["target"],
                "amount": round(amount, 4),
            }
        )

    return transfers


def transfer_relief_map(transfers: List[dict]) -> Dict[str, float]:
    relief: Dict[str, float] = {}
    for transfer in transfers:
        relief[transfer["target"]] = relief.get(transfer["target"], 0.0) + float(transfer["amount"])
    return relief


def compute_domestic_signals(
    state: State,
    turn_effect: dict,
    relief_support: float,
    event: dict,
) -> Dict[str, float]:
    stage_index = int(state["domestic_stage_index"])
    trigger_bonus = clamp(
        event.get("domestic_trigger_bonus", 0.0)
        + 0.28 * turn_effect.get("displacement_bump", 0.0)
        + 0.14 * state["war_burden"]
        + 0.08 * max(0.0, 0.55 - state["cash_stability"]),
        0.0,
        1.0,
    )

    economic_stress = clamp(
        0.23 * max(0.0, 1.0 - state["cash_stability"])
        + 0.17 * state["labor_displacement"]
        + 0.12 * state["inequality_pressure"]
        + 0.11 * state["youth_unemployment"]
        + 0.11 * state["housing_pressure"]
        + 0.07 * state["tax_burden"]
        + 0.07 * state["war_burden"]
        + 0.06 * state["domestic_burden"]
        + 0.06 * state["climate_stress"]
        - 0.10 * turn_effect.get("capital_share_gain", 0.0)
        - 0.10 * relief_support,
        0.0,
        1.0,
    )
    legitimacy_stress = clamp(
        0.26 * max(0.0, 1.0 - state["institutional_capacity"])
        + 0.18 * max(0.0, 1.0 - state["social_cohesion"])
        + 0.16 * state["inequality_pressure"]
        + 0.14 * max(0.0, 1.0 - state["elite_cohesion"])
        + 0.12 * state["sanction_exposure"]
        + 0.08 * state["war_burden"]
        + 0.06 * state["domestic_burden"],
        0.0,
        1.0,
    )
    mobilization_capacity = clamp(
        0.30 * state["compute_access"]
        + 0.18 * state["population_weight"]
        + 0.16 * state["social_cohesion"]
        + 0.18 * max(0.0, 1.0 - state["regime_rigidity"])
        + 0.18 * state["youth_unemployment"],
        0.0,
        1.0,
    )
    coercion_capacity = clamp(
        0.40 * state["policing_capacity"]
        + 0.24 * state["military_capacity"]
        + 0.18 * state["regime_rigidity"]
        + 0.18 * state["institutional_capacity"],
        0.0,
        1.0,
    )
    elite_fragmentation = clamp(
        0.42 * max(0.0, 1.0 - state["elite_cohesion"])
        + 0.22 * state["inequality_pressure"]
        + 0.18 * state["sanction_exposure"]
        + 0.18 * max(0.0, 1.0 - state["institutional_capacity"]),
        0.0,
        1.0,
    )
    communal_polarization = clamp(
        0.44 * max(0.0, 1.0 - state["social_cohesion"])
        + 0.20 * state["conflict_risk"]
        + 0.18 * state["inequality_pressure"]
        + 0.10 * state["sanction_exposure"]
        + 0.08 * state["domestic_burden"],
        0.0,
        1.0,
    )
    repression_mismatch = clamp(mobilization_capacity + communal_polarization - coercion_capacity, 0.0, 1.0)
    grievance_pressure = clamp(
        0.46 * economic_stress
        + 0.24 * legitimacy_stress
        + 0.14 * communal_polarization
        + 0.10 * trigger_bonus
        - 0.12 * relief_support
        - 0.08 * coercion_capacity,
        0.0,
        1.0,
    )
    protest_pressure = clamp(
        0.32 * economic_stress
        + 0.24 * legitimacy_stress
        + 0.18 * mobilization_capacity
        + 0.12 * trigger_bonus
        + 0.08 * (stage_index / (len(DOMESTIC_STAGES) - 1))
        - 0.10 * coercion_capacity
        - 0.08 * relief_support,
        0.0,
        1.0,
    )
    riot_pressure = clamp(
        0.24 * economic_stress
        + 0.18 * legitimacy_stress
        + 0.18 * elite_fragmentation
        + 0.16 * communal_polarization
        + 0.14 * repression_mismatch
        + 0.10 * trigger_bonus
        - 0.08 * relief_support,
        0.0,
        1.0,
    )
    armed_capacity = clamp(
        0.34 * state["military_capacity"]
        + 0.24 * state["policing_capacity"]
        + 0.16 * state["conflict_risk"]
        + 0.14 * communal_polarization
        + 0.12 * state["war_burden"],
        0.0,
        1.0,
    )
    civil_conflict_pressure = clamp(
        0.28 * riot_pressure
        + 0.18 * elite_fragmentation
        + 0.18 * armed_capacity
        + 0.10 * state["war_burden"]
        + 0.10 * state["domestic_burden"]
        + 0.08 * state["climate_stress"]
        - 0.10 * state["elite_cohesion"],
        0.0,
        1.0,
    )
    domestic_diversion_incentive = clamp(
        0.32 * economic_stress
        + 0.22 * legitimacy_stress
        + 0.18 * elite_fragmentation
        + 0.12 * (stage_index / (len(DOMESTIC_STAGES) - 1))
        + 0.10 * repression_mismatch
        + 0.06 * state["regime_rigidity"]
        - 0.08 * state["war_burden"],
        0.0,
        1.0,
    )

    return {
        "economic_stress": round(economic_stress, 4),
        "legitimacy_stress": round(legitimacy_stress, 4),
        "mobilization_capacity": round(mobilization_capacity, 4),
        "coercion_capacity": round(coercion_capacity, 4),
        "elite_fragmentation": round(elite_fragmentation, 4),
        "communal_polarization": round(communal_polarization, 4),
        "repression_mismatch": round(repression_mismatch, 4),
        "grievance_pressure": round(grievance_pressure, 4),
        "protest_pressure": round(protest_pressure, 4),
        "riot_pressure": round(riot_pressure, 4),
        "civil_conflict_pressure": round(civil_conflict_pressure, 4),
        "domestic_diversion_incentive": round(domestic_diversion_incentive, 4),
        "relief_support": round(relief_support, 4),
        "trigger_bonus": round(trigger_bonus, 4),
        "armed_capacity": round(armed_capacity, 4),
    }


def apply_domestic_instability(
    states: Dict[str, State],
    event: dict,
    turn_effects: Dict[str, dict],
    transfers: List[dict],
    rng: np.random.Generator,
) -> Tuple[List[dict], Dict[str, dict]]:
    relief_map = transfer_relief_map(transfers)
    signals_by_country: Dict[str, dict] = {}
    domestic_events: List[dict] = []

    for code, state in states.items():
        relief_support = clamp(
            0.30 * turn_effects[code].get("structure_credit_gain", 0.0)
            + 0.20 * turn_effects[code].get("capital_share_gain", 0.0)
            + 0.18 * turn_effects[code].get("adaptation_absorption", 0.0)
            + 0.50 * relief_map.get(code, 0.0),
            0.0,
            1.0,
        )
        signals = compute_domestic_signals(state, turn_effects[code], relief_support, event)

        old_stage_index = int(state["domestic_stage_index"])
        next_stage_index = old_stage_index
        stage_probabilities = {
            "grievance": sigmoid(6.0 * (signals["grievance_pressure"] - 0.48)),
            "protest": sigmoid(6.3 * (signals["protest_pressure"] - 0.52)),
            "mass_protest": sigmoid(6.3 * (signals["protest_pressure"] - 0.60)),
            "riot": sigmoid(6.5 * (signals["riot_pressure"] - 0.56)),
            "insurgency": sigmoid(6.5 * (signals["civil_conflict_pressure"] - 0.62)),
            "civil_conflict": sigmoid(6.8 * (signals["civil_conflict_pressure"] - 0.70)),
        }
        cooldown_probability = sigmoid(
            5.5
            * (
                0.55 * relief_support
                + 0.18 * signals["coercion_capacity"]
                + 0.14 * state["institutional_capacity"]
                - 0.58 * max(
                    signals["protest_pressure"],
                    signals["riot_pressure"],
                    signals["civil_conflict_pressure"],
                )
                - 0.34
            )
        )

        escalation_probability = 0.0
        if old_stage_index == DOMESTIC_STAGE_INDEX["stable"]:
            escalation_probability = stage_probabilities["grievance"]
        elif old_stage_index == DOMESTIC_STAGE_INDEX["grievance"]:
            escalation_probability = stage_probabilities["protest"]
        elif old_stage_index == DOMESTIC_STAGE_INDEX["protest"]:
            escalation_probability = stage_probabilities["mass_protest"]
        elif old_stage_index == DOMESTIC_STAGE_INDEX["mass_protest"]:
            escalation_probability = stage_probabilities["riot"]
        elif old_stage_index == DOMESTIC_STAGE_INDEX["riot"]:
            escalation_probability = stage_probabilities["insurgency"]
        elif old_stage_index == DOMESTIC_STAGE_INDEX["insurgency"]:
            escalation_probability = stage_probabilities["civil_conflict"]

        if rng.random() < escalation_probability:
            next_stage_index = min(old_stage_index + 1, len(DOMESTIC_STAGES) - 1)
        elif old_stage_index > 0 and rng.random() < cooldown_probability:
            next_stage_index = old_stage_index - 1

        stage_drag = 0.010 + 0.012 * next_stage_index
        if next_stage_index >= DOMESTIC_STAGE_INDEX["protest"]:
            state["cash_stability"] = clamp(state["cash_stability"] - 0.55 * stage_drag)
            state["social_cohesion"] = clamp(state["social_cohesion"] - 0.60 * stage_drag)
            state["conflict_risk"] = clamp(state["conflict_risk"] + 0.35 * stage_drag)
        if next_stage_index >= DOMESTIC_STAGE_INDEX["mass_protest"]:
            state["supply_chain_resilience"] = clamp(state["supply_chain_resilience"] - 0.45 * stage_drag)
            state["institutional_capacity"] = clamp(state["institutional_capacity"] - 0.35 * stage_drag)
        if next_stage_index >= DOMESTIC_STAGE_INDEX["riot"]:
            state["capital_surplus"] = clamp(state["capital_surplus"] - 0.40 * stage_drag)
            state["alliance_support"] = clamp(state["alliance_support"] - 0.12 * stage_drag)
        if next_stage_index >= DOMESTIC_STAGE_INDEX["insurgency"]:
            state["war_burden"] = clamp(state["war_burden"] + 0.20 * stage_drag)
            state["energy_security"] = clamp(state["energy_security"] - 0.18 * stage_drag)
        if next_stage_index >= DOMESTIC_STAGE_INDEX["civil_conflict"]:
            state["food_security"] = clamp(state["food_security"] - 0.14 * stage_drag)
            state["military_posture"] = clamp(state["military_posture"] + 0.25 * stage_drag)

        state["domestic_burden"] = clamp(
            max(state["domestic_burden"], 0.02 + 0.035 * next_stage_index)
            + (0.03 if next_stage_index > old_stage_index else -0.015 if next_stage_index < old_stage_index else 0.0),
            0.0,
            1.0,
        )

        state["economic_stress"] = signals["economic_stress"]
        state["legitimacy_stress"] = signals["legitimacy_stress"]
        state["mobilization_capacity"] = signals["mobilization_capacity"]
        state["elite_fragmentation"] = signals["elite_fragmentation"]
        state["communal_polarization"] = signals["communal_polarization"]
        state["grievance_pressure"] = signals["grievance_pressure"]
        state["protest_pressure"] = signals["protest_pressure"]
        state["riot_pressure"] = signals["riot_pressure"]
        state["civil_conflict_pressure"] = signals["civil_conflict_pressure"]
        state["domestic_diversion_incentive"] = signals["domestic_diversion_incentive"]
        state["domestic_stage_index"] = next_stage_index
        state["domestic_stage"] = domestic_stage_name(next_stage_index)

        signals_by_country[code] = {
            **signals,
            "domestic_stage": state["domestic_stage"],
            "domestic_stage_index": next_stage_index,
            "escalation_probability": round(escalation_probability, 4),
            "cooldown_probability": round(cooldown_probability, 4),
        }

        if next_stage_index != old_stage_index or next_stage_index >= DOMESTIC_STAGE_INDEX["riot"]:
            domestic_events.append(
                {
                    "country": code,
                    "from_stage": domestic_stage_name(old_stage_index),
                    "to_stage": state["domestic_stage"],
                    "event_type": state["domestic_stage"],
                    "escalation_probability": round(escalation_probability, 4),
                    "cooldown_probability": round(cooldown_probability, 4),
                    "protest_pressure": signals["protest_pressure"],
                    "riot_pressure": signals["riot_pressure"],
                    "civil_conflict_pressure": signals["civil_conflict_pressure"],
                    "economic_stress": signals["economic_stress"],
                    "legitimacy_stress": signals["legitimacy_stress"],
                }
            )

    return domestic_events, signals_by_country


def compute_survival_pressure(state: State, metrics: Dict[str, float]) -> float:
    horizon_pressure = clamp((6.0 - metrics["horizon_turns"]) / 6.0)
    return clamp(
        0.28 * clamp((0.52 - metrics["S"]) / 0.52)
        + 0.18 * clamp((0.48 - state["cash_stability"]) / 0.48)
        + 0.15 * metrics["displacement_gap"]
        + 0.10 * state["sanction_exposure"]
        + 0.09 * state["climate_stress"]
        + 0.08 * metrics["dependency_risk"]
        + 0.07 * state["inequality_pressure"]
        + 0.05 * horizon_pressure,
        0.0,
        1.0,
    )


def conflict_mode_from_probabilities(
    gray_zone_probability: float,
    proxy_probability: float,
    limited_war_probability: float,
) -> str | None:
    if limited_war_probability >= 0.16:
        return "limited_war"
    if proxy_probability >= 0.14:
        return "proxy"
    if gray_zone_probability >= 0.12:
        return "gray_zone"
    return None


def conflict_probabilities(
    score: float,
    gray_zone_bias: float,
    nuclear_pair: bool,
    config: dict,
    scenario: dict,
    attacker: State,
    link: dict,
) -> Dict[str, float]:
    war_model = config.get("war_model", {})
    gray_threshold = war_model.get("gray_zone_threshold", 0.52)
    proxy_threshold = war_model.get("proxy_threshold", 0.64)
    limited_threshold = war_model.get("limited_war_threshold", 0.79)
    nuclear_cap = war_model.get("nuclear_direct_war_cap", 0.73)
    fatigue = clamp(0.54 * attacker["war_burden"] + 0.46 * attacker["domestic_burden"])
    diversion = attacker["domestic_diversion_incentive"]
    deescalation = scenario.get("deescalation_capacity", 0.0)
    territorial = link["territorial_salience"]
    revisionism = attacker["revisionism"]
    posture = attacker["military_posture"]

    gray_zone_probability = clamp(
        sigmoid(
            6.1 * (score - gray_threshold)
            + 0.95 * gray_zone_bias
            + 0.34 * diversion
            - 0.28 * fatigue
            - 0.28 * deescalation
        )
        * (0.60 + 0.40 * gray_zone_bias)
    )
    proxy_probability = clamp(
        sigmoid(
            6.5 * (score - proxy_threshold)
            + 0.22 * diversion
            + 0.16 * territorial
            + 0.10 * revisionism
            - 0.24 * gray_zone_bias
            - 0.34 * fatigue
            - 0.34 * deescalation
        )
        * (0.48 + 0.26 * (1.0 - gray_zone_bias) + 0.26 * revisionism)
    )
    proxy_probability = min(proxy_probability, gray_zone_probability)

    limited_war_probability = clamp(
        sigmoid(
            7.0 * (score - limited_threshold)
            + 0.24 * territorial
            + 0.18 * revisionism
            + 0.12 * posture
            - 0.54 * gray_zone_bias
            - 0.40 * fatigue
            - 0.44 * deescalation
        )
        * (0.34 + 0.34 * territorial + 0.32 * posture)
    )
    if nuclear_pair:
        limited_war_probability *= max(0.05, 0.50 - 0.65 * nuclear_cap)
        proxy_probability = clamp(
            min(gray_zone_probability, proxy_probability + 0.08 * max(gray_zone_probability, diversion))
        )
    limited_war_probability = min(limited_war_probability, proxy_probability)
    war_pressure = clamp(0.56 * score + 0.44 * gray_zone_probability)

    return {
        "gray_zone_probability": round(gray_zone_probability, 4),
        "proxy_probability": round(proxy_probability, 4),
        "limited_war_probability": round(limited_war_probability, 4),
        "war_pressure": round(war_pressure, 4),
    }


def compute_conflict_candidate(
    states: Dict[str, State],
    link: dict,
    scenario: dict,
    config: dict,
) -> dict:
    attacker = states[link["actor"]]
    target = states[link["target"]]
    attacker_metrics = metric_snapshot(attacker)
    target_metrics = metric_snapshot(target)

    survival_pressure = compute_survival_pressure(attacker, attacker_metrics)
    target_fragility = compute_survival_pressure(target, target_metrics)
    nuclear_pair = attacker["nuclear_deterrent"] > 0.6 and target["nuclear_deterrent"] > 0.6
    deterrence = clamp(
        0.24 * target["alliance_support"]
        + 0.18 * target["military_capacity"]
        + 0.22 * min(attacker["nuclear_deterrent"], target["nuclear_deterrent"])
        + 0.10 * scenario.get("deescalation_capacity", 0.0)
    )

    score = clamp(
        0.22 * survival_pressure
        + 0.14 * attacker["regime_rigidity"]
        + 0.14 * attacker["revisionism"]
        + 0.10 * attacker["military_capacity"]
        + 0.06 * attacker["military_posture"]
        + 0.10 * link["base_tension"]
        + 0.08 * link["historical_rivalry"]
        + 0.08 * link["territorial_salience"]
        + 0.04 * attacker["gray_zone_capability"]
        + 0.08 * target_fragility
        + 0.08 * attacker["domestic_diversion_incentive"]
        + 0.05 * attacker["riot_pressure"]
        + 0.04 * target["civil_conflict_pressure"]
        + scenario.get("war_risk_bias", 0.0)
        - 0.05 * attacker["war_burden"]
        - 0.04 * attacker["domestic_burden"]
        - deterrence,
        0.0,
        1.0,
    )
    probabilities = conflict_probabilities(
        score=score,
        gray_zone_bias=link["gray_zone_bias"],
        nuclear_pair=nuclear_pair,
        config=config,
        scenario=scenario,
        attacker=attacker,
        link=link,
    )
    likely_mode = conflict_mode_from_probabilities(
        probabilities["gray_zone_probability"],
        probabilities["proxy_probability"],
        probabilities["limited_war_probability"],
    )

    return {
        "actor": link["actor"],
        "target": link["target"],
        "domain": link["domain"],
        "score": round(score, 4),
        "mode": likely_mode,
        "nuclear_pair": nuclear_pair,
        "survival_pressure": round(survival_pressure, 4),
        "target_fragility": round(target_fragility, 4),
        "gray_zone_bias": link["gray_zone_bias"],
        "deterrence": round(deterrence, 4),
        **probabilities,
    }


def apply_conflict_event(states: Dict[str, State], event: dict, config: dict) -> dict:
    attacker = states[event["actor"]]
    target = states[event["target"]]
    intensity = clamp(
        config.get("war_model", {}).get("event_intensity_scale", 1.0)
        * (0.55 * event["score"] + 0.45 * event["survival_pressure"]),
        0.0,
        1.0,
    )
    rally = 0.012 * intensity
    target_rally = 0.008 * intensity

    if event["mode"] == "gray_zone":
        target["supply_chain_resilience"] = clamp(target["supply_chain_resilience"] - 0.055 * intensity)
        target["cash_stability"] = clamp(target["cash_stability"] - 0.040 * intensity)
        target["conflict_risk"] = clamp(target["conflict_risk"] + 0.075 * intensity)
        target["sanction_exposure"] = clamp(target["sanction_exposure"] + 0.030 * intensity)
        target["war_burden"] = clamp(target["war_burden"] + 0.065 * intensity)
        target["social_cohesion"] = clamp(target["social_cohesion"] - 0.020 * intensity + target_rally)

        attacker["social_cohesion"] = clamp(attacker["social_cohesion"] + rally)
        attacker["sanction_exposure"] = clamp(attacker["sanction_exposure"] + 0.018 * intensity)
        attacker["war_burden"] = clamp(attacker["war_burden"] + 0.020 * intensity)
        attacker["capital_surplus"] = clamp(attacker["capital_surplus"] - 0.018 * intensity)

    elif event["mode"] == "proxy":
        target["energy_security"] = clamp(target["energy_security"] - 0.040 * intensity)
        target["supply_chain_resilience"] = clamp(target["supply_chain_resilience"] - 0.075 * intensity)
        target["cash_stability"] = clamp(target["cash_stability"] - 0.060 * intensity)
        target["conflict_risk"] = clamp(target["conflict_risk"] + 0.105 * intensity)
        target["war_burden"] = clamp(target["war_burden"] + 0.120 * intensity)
        target["social_cohesion"] = clamp(target["social_cohesion"] - 0.025 * intensity + target_rally)
        target["alliance_support"] = clamp(target["alliance_support"] + 0.028 * intensity)

        attacker["social_cohesion"] = clamp(attacker["social_cohesion"] + rally)
        attacker["cash_stability"] = clamp(attacker["cash_stability"] + 0.006 * intensity)
        attacker["sanction_exposure"] = clamp(attacker["sanction_exposure"] + 0.028 * intensity)
        attacker["conflict_risk"] = clamp(attacker["conflict_risk"] + 0.030 * intensity)
        attacker["war_burden"] = clamp(attacker["war_burden"] + 0.050 * intensity)
        attacker["capital_surplus"] = clamp(attacker["capital_surplus"] - 0.030 * intensity)

    else:
        target["energy_security"] = clamp(target["energy_security"] - 0.090 * intensity)
        target["food_security"] = clamp(target["food_security"] - 0.040 * intensity)
        target["supply_chain_resilience"] = clamp(target["supply_chain_resilience"] - 0.120 * intensity)
        target["cash_stability"] = clamp(target["cash_stability"] - 0.090 * intensity)
        target["conflict_risk"] = clamp(target["conflict_risk"] + 0.160 * intensity)
        target["war_burden"] = clamp(target["war_burden"] + 0.180 * intensity)
        target["social_cohesion"] = clamp(target["social_cohesion"] - 0.035 * intensity + target_rally)
        target["alliance_support"] = clamp(target["alliance_support"] + 0.040 * intensity)

        attacker["social_cohesion"] = clamp(attacker["social_cohesion"] + 0.016 * intensity)
        attacker["cash_stability"] = clamp(attacker["cash_stability"] - 0.020 * intensity)
        attacker["sanction_exposure"] = clamp(attacker["sanction_exposure"] + 0.050 * intensity)
        attacker["conflict_risk"] = clamp(attacker["conflict_risk"] + 0.055 * intensity)
        attacker["war_burden"] = clamp(attacker["war_burden"] + 0.110 * intensity)
        attacker["capital_surplus"] = clamp(attacker["capital_surplus"] - 0.060 * intensity)

    attacker["military_posture"] = clamp(attacker["military_posture"] + 0.080 * intensity)
    target["military_posture"] = clamp(target["military_posture"] + 0.050 * intensity)

    if event["domain"] in {"technology_maritime", "maritime_island_chain", "continental_energy"}:
        target["energy_security"] = clamp(target["energy_security"] - 0.020 * intensity)

    applied = deepcopy(event)
    applied["intensity"] = round(intensity, 4)
    return applied


def apply_conflict_escalation(
    states: Dict[str, State],
    config: dict,
    scenario: dict,
    rng: np.random.Generator,
) -> Tuple[List[dict], Dict[str, dict]]:
    candidates: List[dict] = []
    war_signals = {
        code: {
            "survival_pressure": 0.0,
            "war_pressure": 0.0,
            "gray_zone_probability": 0.0,
            "proxy_probability": 0.0,
            "limited_war_probability": 0.0,
            "likely_mode": "none",
        }
        for code in states
    }

    for link in config.get("rivalries", []):
        candidate = compute_conflict_candidate(states, link, scenario, config)
        actor = link["actor"]
        actor_metrics = metric_snapshot(states[actor])
        pressure = compute_survival_pressure(states[actor], actor_metrics)
        current = war_signals[actor]
        current["survival_pressure"] = max(current["survival_pressure"], round(pressure, 4))
        if candidate["war_pressure"] > current["war_pressure"]:
            current["war_pressure"] = candidate["war_pressure"]
            current["gray_zone_probability"] = candidate["gray_zone_probability"]
            current["proxy_probability"] = candidate["proxy_probability"]
            current["limited_war_probability"] = candidate["limited_war_probability"]
            current["likely_mode"] = candidate["mode"] or "pressure_only"
        if candidate["gray_zone_probability"] >= 0.06:
            candidates.append(candidate)

    max_conflicts = config.get("war_model", {}).get("max_conflicts_per_turn", 2)
    selected: List[dict] = []
    used_actors = set()
    used_targets = set()
    for candidate in sorted(candidates, key=lambda item: item["war_pressure"], reverse=True):
        if candidate["actor"] in used_actors or candidate["target"] in used_targets:
            continue
        draw = float(rng.random())
        sampled_mode = None
        if draw < candidate["limited_war_probability"]:
            sampled_mode = "limited_war"
        elif draw < candidate["proxy_probability"]:
            sampled_mode = "proxy"
        elif draw < candidate["gray_zone_probability"]:
            sampled_mode = "gray_zone"
        if sampled_mode is None:
            continue
        event_candidate = deepcopy(candidate)
        event_candidate["mode"] = sampled_mode
        event_candidate["sample_draw"] = round(draw, 4)
        selected.append(apply_conflict_event(states, event_candidate, config))
        used_actors.add(candidate["actor"])
        used_targets.add(candidate["target"])
        if len(selected) >= max_conflicts:
            break

    return selected, war_signals


def run_scenario(config: dict, scenario: dict, rng: np.random.Generator) -> ScenarioRunResult:
    states = build_initial_states(config)
    event_map = {event["turn"]: event for event in config.get("events", [])}
    selection_metadata = config.get("_selection_metadata", {})
    rows: List[dict] = []
    event_log: List[dict] = []
    aggregate_rows: List[dict] = []
    conflict_rows: List[dict] = []

    for turn in range(1, config["meta"]["turns"] + 1):
        event = event_map.get(turn, {})
        modifiers = deepcopy(event.get("modifiers", {}))
        expanded_country_effects = event.get("country_effects", {})
        if selection_metadata:
            expanded_country_effects = expand_event_country_effects(event, selection_metadata)
        if expanded_country_effects:
            apply_country_effects(states, expanded_country_effects)

        turn_effects = {}
        for code, state in states.items():
            turn_effects[code] = self_update(state, scenario, modifiers)

        transfers = apply_cooperation(states, config.get("cooperation_links", []), scenario, modifiers)
        domestic_events, domestic_signals = apply_domestic_instability(states, event, turn_effects, transfers, rng)
        conflict_events, war_signals = apply_conflict_escalation(states, config, scenario, rng)
        conflict_rows.extend(
            {
                "scenario_key": scenario["key"],
                "turn": turn,
                **item,
            }
            for item in conflict_events
        )

        turn_rows: List[dict] = []
        for code, state in states.items():
            metrics = metric_snapshot(state)
            row = {
                "scenario_key": scenario["key"],
                "scenario_name": scenario["name"],
                "turn": turn,
                "code": code,
                "name": state["name"],
                "name_ja": state.get("name_ja", state["name"]),
                "tier": state.get("tier", ""),
                "region_id": state.get("region_id", ""),
                "lon": round(state.get("lon", 0.0), 4),
                "lat": round(state.get("lat", 0.0), 4),
                "population_weight": state["population_weight"],
                "energy_security": round(state["energy_security"], 4),
                "food_security": round(state["food_security"], 4),
                "compute_access": round(state["compute_access"], 4),
                "distribution_capacity": round(state["distribution_capacity"], 4),
                "social_cohesion": round(state["social_cohesion"], 4),
                "cash_stability": round(state["cash_stability"], 4),
                "capital_surplus": round(state["capital_surplus"], 4),
                "labor_displacement": round(state["labor_displacement"], 4),
                "inequality_pressure": round(state["inequality_pressure"], 4),
                "sanction_exposure": round(state["sanction_exposure"], 4),
                "conflict_risk": round(state["conflict_risk"], 4),
                "climate_stress": round(state["climate_stress"], 4),
                "alliance_support": round(state["alliance_support"], 4),
                "war_burden": round(state["war_burden"], 4),
                "military_posture": round(state["military_posture"], 4),
                "tax_burden": round(state["tax_burden"], 4),
                "housing_pressure": round(state["housing_pressure"], 4),
                "youth_unemployment": round(state["youth_unemployment"], 4),
                "policing_capacity": round(state["policing_capacity"], 4),
                "elite_cohesion": round(state["elite_cohesion"], 4),
                "economic_stress": round(state["economic_stress"], 4),
                "legitimacy_stress": round(state["legitimacy_stress"], 4),
                "mobilization_capacity": round(state["mobilization_capacity"], 4),
                "elite_fragmentation": round(state["elite_fragmentation"], 4),
                "communal_polarization": round(state["communal_polarization"], 4),
                "domestic_burden": round(state["domestic_burden"], 4),
                "domestic_stage": state["domestic_stage"],
                "domestic_stage_index": int(state["domestic_stage_index"]),
                "grievance_pressure": round(state["grievance_pressure"], 4),
                "protest_pressure": round(state["protest_pressure"], 4),
                "riot_pressure": round(state["riot_pressure"], 4),
                "civil_conflict_pressure": round(state["civil_conflict_pressure"], 4),
                "domestic_diversion_incentive": round(state["domestic_diversion_incentive"], 4),
                "survival_pressure": round(war_signals[code]["survival_pressure"], 4),
                "war_pressure": round(war_signals[code]["war_pressure"], 4),
                "gray_zone_probability": round(war_signals[code]["gray_zone_probability"], 4),
                "proxy_probability": round(war_signals[code]["proxy_probability"], 4),
                "limited_war_probability": round(war_signals[code]["limited_war_probability"], 4),
                "likely_mode": war_signals[code]["likely_mode"],
            }
            row.update(turn_effects[code])
            row.update(metrics)
            row.update(domestic_signals[code])
            rows.append(row)
            turn_rows.append(row)

        gray_zone_events = sum(1 for item in conflict_events if item["mode"] == "gray_zone")
        proxy_events = sum(1 for item in conflict_events if item["mode"] == "proxy")
        limited_war_events = sum(1 for item in conflict_events if item["mode"] == "limited_war")
        stage_counts = {name: sum(1 for row in turn_rows if row["domestic_stage"] == name) for name in DOMESTIC_STAGES}
        domestic_event_counts = {name: sum(1 for item in domestic_events if item["to_stage"] == name) for name in DOMESTIC_STAGES}

        aggregate_rows.append(
            {
                "scenario_key": scenario["key"],
                "turn": turn,
                "avg_S": round(weighted_average(turn_rows, "S"), 4),
                "avg_horizon_turns": round(weighted_average(turn_rows, "horizon_turns"), 4),
                "avg_cash_stability": round(weighted_average(turn_rows, "cash_stability"), 4),
                "avg_labor_displacement": round(weighted_average(turn_rows, "labor_displacement"), 4),
                "avg_conflict_risk": round(weighted_average(turn_rows, "conflict_risk"), 4),
                "avg_war_burden": round(weighted_average(turn_rows, "war_burden"), 4),
                "avg_domestic_burden": round(weighted_average(turn_rows, "domestic_burden"), 4),
                "avg_economic_stress": round(weighted_average(turn_rows, "economic_stress"), 4),
                "avg_legitimacy_stress": round(weighted_average(turn_rows, "legitimacy_stress"), 4),
                "avg_protest_pressure": round(weighted_average(turn_rows, "protest_pressure"), 4),
                "avg_riot_pressure": round(weighted_average(turn_rows, "riot_pressure"), 4),
                "avg_civil_conflict_pressure": round(weighted_average(turn_rows, "civil_conflict_pressure"), 4),
                "war_events_count": len(conflict_events),
                "domestic_events_count": len(domestic_events),
                "gray_zone_events": gray_zone_events,
                "proxy_events": proxy_events,
                "limited_war_events": limited_war_events,
                "stable_stage_count": stage_counts["stable"],
                "grievance_stage_count": stage_counts["grievance"],
                "protest_stage_count": stage_counts["protest"],
                "mass_protest_stage_count": stage_counts["mass_protest"],
                "riot_stage_count": stage_counts["riot"],
                "insurgency_stage_count": stage_counts["insurgency"],
                "civil_conflict_stage_count": stage_counts["civil_conflict"],
                "grievance_events": domestic_event_counts["grievance"],
                "protest_events": domestic_event_counts["protest"],
                "mass_protest_events": domestic_event_counts["mass_protest"],
                "riot_events": domestic_event_counts["riot"],
                "insurgency_events": domestic_event_counts["insurgency"],
                "civil_conflict_events": domestic_event_counts["civil_conflict"],
            }
        )

        event_log.append(
            {
                "scenario_key": scenario["key"],
                "turn": turn,
                "name": event.get("name", "Baseline dynamics"),
                "description": event.get("description", "No exogenous event."),
                "modifiers": modifiers,
                "country_effects": expanded_country_effects,
                "cooperation_transfers": transfers,
                "domestic_events": domestic_events,
                "conflict_events": conflict_events,
            }
        )

    final_rows = [row for row in rows if row["turn"] == config["meta"]["turns"]]
    final_rows.sort(key=lambda item: item["S"], reverse=True)
    summary = {
        "scenario_key": scenario["key"],
        "scenario_name": scenario["name"],
        "turns": config["meta"]["turns"],
        "global_avg_S_final": aggregate_rows[-1]["avg_S"],
        "global_avg_horizon_final": aggregate_rows[-1]["avg_horizon_turns"],
        "global_avg_cash_final": aggregate_rows[-1]["avg_cash_stability"],
        "global_avg_war_burden_final": aggregate_rows[-1]["avg_war_burden"],
        "global_avg_domestic_burden_final": aggregate_rows[-1]["avg_domestic_burden"],
        "global_avg_protest_pressure_final": aggregate_rows[-1]["avg_protest_pressure"],
        "gray_zone_events": sum(row["gray_zone_events"] for row in aggregate_rows),
        "proxy_events": sum(row["proxy_events"] for row in aggregate_rows),
        "limited_war_events": sum(row["limited_war_events"] for row in aggregate_rows),
        "grievance_events": sum(row["grievance_events"] for row in aggregate_rows),
        "protest_events": sum(row["protest_events"] for row in aggregate_rows),
        "mass_protest_events": sum(row["mass_protest_events"] for row in aggregate_rows),
        "riot_events": sum(row["riot_events"] for row in aggregate_rows),
        "insurgency_events": sum(row["insurgency_events"] for row in aggregate_rows),
        "civil_conflict_events": sum(row["civil_conflict_events"] for row in aggregate_rows),
        "top_resilient": [row["code"] for row in final_rows[:3]],
        "most_fragile": [row["code"] for row in final_rows[-3:]],
        "most_domestically_fragile": [
            row["code"]
            for row in sorted(
                final_rows,
                key=lambda item: (
                    item["domestic_stage_index"],
                    item["domestic_burden"],
                    item["civil_conflict_pressure"],
                ),
                reverse=True,
            )[:3]
        ],
    }
    return ScenarioRunResult(
        rows=rows,
        aggregate_rows=aggregate_rows,
        event_log=event_log,
        summary=summary,
        final_rows=final_rows,
        conflict_rows=conflict_rows,
    )
