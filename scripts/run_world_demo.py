#!/usr/bin/env python3
"""
Run a coarse world simulation for a small set of major countries.

The goal is not forecasting accuracy. The goal is to make the design memo
concrete enough that we can compare:

- high automation / low adaptation
- high automation / high adaptation

using country-level state, cooperation, and structure-sustain metrics.

This version also models survival-driven conflict escalation in a way that
leans toward modern patterns:

- gray-zone coercion is common
- proxy or coercive campaigns appear under sustained stress
- direct limited war is rarer and suppressed by deterrence, especially in
  nuclear pairings
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import yaml

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - plotting is optional
    plt = None


State = Dict[str, float]
Row = Dict[str, float]

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


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def domestic_stage_name(index: int | float) -> str:
    bounded = max(0, min(int(index), len(DOMESTIC_STAGES) - 1))
    return DOMESTIC_STAGES[bounded]


def deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    extends = payload.pop("extends", None)
    if not extends:
        return payload
    base_path = (path.parent / extends).resolve()
    base_payload = load_yaml(base_path)
    return deep_merge(base_payload, payload)


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
        code = country["code"]
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
        states[code] = state
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
    metrics: Dict[str, float],
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
        metrics = metric_snapshot(state)
        relief_support = clamp(
            0.30 * turn_effects[code].get("structure_credit_gain", 0.0)
            + 0.20 * turn_effects[code].get("capital_share_gain", 0.0)
            + 0.18 * turn_effects[code].get("adaptation_absorption", 0.0)
            + 0.50 * relief_map.get(code, 0.0),
            0.0,
            1.0,
        )
        signals = compute_domestic_signals(state, metrics, turn_effects[code], relief_support, event)

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


def weighted_average(rows: List[dict], key: str) -> float:
    total_weight = sum(row["population_weight"] for row in rows)
    if total_weight == 0:
        return 0.0
    return sum(row[key] * row["population_weight"] for row in rows) / total_weight


def scenario_output_dir(base_dir: Path, scenario_key: str) -> Path:
    path = base_dir / scenario_key
    path.mkdir(parents=True, exist_ok=True)
    return path


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


def scenario_seed(config: dict, scenario: dict) -> int:
    base_seed = int(config.get("meta", {}).get("seed", 20260416))
    scenario_offset = sum((index + 1) * ord(char) for index, char in enumerate(scenario["key"]))
    return (base_seed + scenario_offset) % (2**32 - 1)


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


def write_csv(path: Path, rows: List[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_markdown_summary(path: Path, summary: dict, final_rows: List[dict], event_log: List[dict]) -> None:
    lines = [
        f"# {summary['scenario_name']}",
        "",
        f"- Final global average `S`: `{summary['global_avg_S_final']}`",
        f"- Final global average horizon: `{summary['global_avg_horizon_final']}` turns",
        f"- Final global average cash stability: `{summary['global_avg_cash_final']}`",
        f"- Final global average war burden: `{summary['global_avg_war_burden_final']}`",
        f"- Final global average domestic burden: `{summary['global_avg_domestic_burden_final']}`",
        f"- Final global average protest pressure: `{summary['global_avg_protest_pressure_final']}`",
        f"- Top resilient: `{', '.join(summary['top_resilient'])}`",
        f"- Most fragile: `{', '.join(summary['most_fragile'])}`",
        f"- Most domestically fragile: `{', '.join(summary['most_domestically_fragile'])}`",
        f"- Conflict mix: `gray={summary['gray_zone_events']}, proxy={summary['proxy_events']}, limited={summary['limited_war_events']}`",
        f"- Domestic escalation mix: `protest={summary['protest_events']}, mass={summary['mass_protest_events']}, riot={summary['riot_events']}, insurgency={summary['insurgency_events']}, civil={summary['civil_conflict_events']}`",
        "",
        "## Final Country Snapshot",
        "",
        "| Code | S | Horizon | Support Needed | Cash | Domestic Stage | Domestic Burden | Protest | War Burden | War Pressure | Likely Mode |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in final_rows:
        lines.append(
            f"| {row['code']} | {row['S']} | {row['horizon_turns']} | {row['support_needed']} | "
            f"{row['cash_stability']} | {row['domestic_stage']} | {row['domestic_burden']} | {row['protest_pressure']} | "
            f"{row['war_burden']} | {row['war_pressure']} | {row['likely_mode']} |"
        )

    lines.extend(
        [
            "",
            "## Event Timeline",
            "",
        ]
    )
    for entry in event_log:
        transfer_text = ", ".join(
            f"{item['donor']}->{item['target']}:{item['amount']}" for item in entry["cooperation_transfers"][:5]
        )
        if not transfer_text:
            transfer_text = "none"
        conflict_text = ", ".join(
            f"{item['actor']}->{item['target']}:{item['mode']}:{item['intensity']}" for item in entry["conflict_events"]
        )
        if not conflict_text:
            conflict_text = "none"
        domestic_text = ", ".join(
            f"{item['country']}:{item['from_stage']}->{item['to_stage']}" for item in entry.get("domestic_events", [])[:5]
        )
        if not domestic_text:
            domestic_text = "none"
        lines.append(
            f"- Turn {entry['turn']}: {entry['name']} | transfers: {transfer_text} | conflict: {conflict_text} | domestic: {domestic_text}"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_comparison_report(base_dir: Path, scenario_results: Dict[str, dict]) -> None:
    scenario_keys = list(scenario_results.keys())
    if len(scenario_keys) < 2:
        return

    first = scenario_results[scenario_keys[0]]
    second = scenario_results[scenario_keys[1]]

    final_a = {row["code"]: row for row in first["final_rows"]}
    final_b = {row["code"]: row for row in second["final_rows"]}

    comparison_rows: List[dict] = []
    lines = [
        "# Major Powers 10-Turn Comparison",
        "",
        f"- `{first['summary']['scenario_name']}` final avg `S`: `{first['summary']['global_avg_S_final']}`",
        f"- `{second['summary']['scenario_name']}` final avg `S`: `{second['summary']['global_avg_S_final']}`",
        f"- Delta avg `S`: `{round(second['summary']['global_avg_S_final'] - first['summary']['global_avg_S_final'], 4)}`",
        f"- Delta avg war burden: `{round(second['summary']['global_avg_war_burden_final'] - first['summary']['global_avg_war_burden_final'], 4)}`",
        f"- Delta avg domestic burden: `{round(second['summary']['global_avg_domestic_burden_final'] - first['summary']['global_avg_domestic_burden_final'], 4)}`",
        f"- Conflict mix `{first['summary']['scenario_name']}`: "
        f"`gray={first['summary']['gray_zone_events']}, proxy={first['summary']['proxy_events']}, limited={first['summary']['limited_war_events']}`",
        f"- Conflict mix `{second['summary']['scenario_name']}`: "
        f"`gray={second['summary']['gray_zone_events']}, proxy={second['summary']['proxy_events']}, limited={second['summary']['limited_war_events']}`",
        f"- Domestic mix `{first['summary']['scenario_name']}`: "
        f"`riot={first['summary']['riot_events']}, insurgency={first['summary']['insurgency_events']}, civil={first['summary']['civil_conflict_events']}`",
        f"- Domestic mix `{second['summary']['scenario_name']}`: "
        f"`riot={second['summary']['riot_events']}, insurgency={second['summary']['insurgency_events']}, civil={second['summary']['civil_conflict_events']}`",
        "",
        "## Final Country Delta",
        "",
        "| Code | S low-adaptation | S high-adaptation | Delta S | Horizon delta | Support delta | War burden delta | Domestic burden delta |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for code in sorted(final_a.keys()):
        row_a = final_a[code]
        row_b = final_b[code]
        delta_s = round(row_b["S"] - row_a["S"], 4)
        delta_h = round(row_b["horizon_turns"] - row_a["horizon_turns"], 2)
        delta_support = round(row_b["support_needed"] - row_a["support_needed"], 4)
        delta_war = round(row_b["war_burden"] - row_a["war_burden"], 4)
        delta_domestic = round(row_b["domestic_burden"] - row_a["domestic_burden"], 4)
        lines.append(
            f"| {code} | {row_a['S']} | {row_b['S']} | {delta_s} | {delta_h} | {delta_support} | {delta_war} | {delta_domestic} |"
        )
        comparison_rows.append(
            {
                "code": code,
                "s_low_adaptation": row_a["S"],
                "s_high_adaptation": row_b["S"],
                "delta_s": delta_s,
                "delta_horizon": delta_h,
                "delta_support_needed": delta_support,
                "delta_war_burden": delta_war,
                "delta_domestic_burden": delta_domestic,
            }
        )

    (base_dir / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_csv(base_dir / "comparison.csv", comparison_rows)

    if plt is not None:
        plot_comparison(base_dir, scenario_results)


def plot_scenario_dashboard(output_dir: Path, result: dict) -> None:
    if plt is None:
        return

    turns = [row["turn"] for row in result["aggregate_rows"]]
    avg_s = [row["avg_S"] for row in result["aggregate_rows"]]
    avg_cash = [row["avg_cash_stability"] for row in result["aggregate_rows"]]
    avg_war = [row["avg_war_burden"] for row in result["aggregate_rows"]]
    avg_domestic = [row["avg_domestic_burden"] for row in result["aggregate_rows"]]
    avg_conflict = [row["avg_conflict_risk"] for row in result["aggregate_rows"]]
    avg_protest = [row["avg_protest_pressure"] for row in result["aggregate_rows"]]
    avg_riot = [row["avg_riot_pressure"] for row in result["aggregate_rows"]]
    avg_civil = [row["avg_civil_conflict_pressure"] for row in result["aggregate_rows"]]
    gray_counts = [row["gray_zone_events"] for row in result["aggregate_rows"]]
    proxy_counts = [row["proxy_events"] for row in result["aggregate_rows"]]
    limited_counts = [row["limited_war_events"] for row in result["aggregate_rows"]]
    grievance_counts = [row["grievance_stage_count"] for row in result["aggregate_rows"]]
    protest_counts = [row["protest_stage_count"] for row in result["aggregate_rows"]]
    mass_counts = [row["mass_protest_stage_count"] for row in result["aggregate_rows"]]
    riot_counts = [row["riot_stage_count"] for row in result["aggregate_rows"]]
    insurgency_counts = [row["insurgency_stage_count"] for row in result["aggregate_rows"]]
    civil_counts = [row["civil_conflict_stage_count"] for row in result["aggregate_rows"]]

    countries = [row["code"] for row in result["final_rows"]]
    rows_by_country = {code: [] for code in countries}
    for row in result["rows"]:
        rows_by_country[row["code"]].append(row)
    s_matrix = np.array([[entry["S"] for entry in rows_by_country[code]] for code in countries])

    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.0, 1.0, 1.0], height_ratios=[1.0, 1.0])

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(turns, avg_s, marker="o", label="avg S", color="#1b5e20")
    ax1.plot(turns, avg_cash, marker="o", label="avg cash stability", color="#1565c0")
    ax1.plot(turns, avg_domestic, marker="o", label="avg domestic burden", color="#8e24aa")
    ax1.plot(turns, avg_war, marker="o", label="avg war burden", color="#b71c1c")
    ax1.set_title(f"{result['summary']['scenario_name']}: global trajectory")
    ax1.set_xlabel("Turn")
    ax1.set_ylabel("0-1 scale")
    ax1.grid(alpha=0.25)
    ax1.legend(loc="best")

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(turns, avg_conflict, marker="o", label="avg conflict risk", color="#ef6c00")
    ax2.plot(turns, avg_protest, marker="o", label="avg protest pressure", color="#ffb300")
    ax2.plot(turns, avg_riot, marker="o", label="avg riot pressure", color="#fb8c00")
    ax2.plot(turns, avg_civil, marker="o", label="avg civil conflict pressure", color="#6d4c41")
    ax2.set_title("Conflict and domestic pressure")
    ax2.set_xlabel("Turn")
    ax2.set_ylabel("0-1 scale")
    ax2.grid(alpha=0.25)
    ax2.legend(loc="best")

    ax3 = fig.add_subplot(gs[0, 2])
    heat = ax3.imshow(s_matrix, aspect="auto", cmap="YlGnBu", vmin=0.20, vmax=0.55)
    ax3.set_title("Country S heatmap")
    ax3.set_xlabel("Turn")
    ax3.set_ylabel("Country")
    ax3.set_xticks(range(len(turns)))
    ax3.set_xticklabels(turns)
    ax3.set_yticks(range(len(countries)))
    ax3.set_yticklabels(countries)
    fig.colorbar(heat, ax=ax3, fraction=0.046, pad=0.04)

    ax4 = fig.add_subplot(gs[1, 0])
    final_s = [row["S"] for row in result["final_rows"]]
    final_support = [row["support_needed"] for row in result["final_rows"]]
    y = np.arange(len(countries))
    ax4.barh(y - 0.18, final_s, height=0.32, label="final S", color="#2e7d32")
    ax4.barh(y + 0.18, final_support, height=0.32, label="support needed", color="#ef6c00")
    ax4.set_yticks(y)
    ax4.set_yticklabels(countries)
    ax4.set_xlabel("Score")
    ax4.set_title("Final resilience vs support need")
    ax4.invert_yaxis()
    ax4.legend(loc="best")

    ax5 = fig.add_subplot(gs[1, 1])
    ax5.bar(turns, gray_counts, label="gray-zone", color="#6a1b9a")
    ax5.bar(turns, proxy_counts, bottom=gray_counts, label="proxy", color="#e53935")
    ax5.bar(
        turns,
        limited_counts,
        bottom=np.array(gray_counts) + np.array(proxy_counts),
        label="limited war",
        color="#212121",
    )
    ax5.set_title("Conflict events by turn")
    ax5.set_xlabel("Turn")
    ax5.set_ylabel("Event count")
    ax5.legend(loc="best")

    ax6 = fig.add_subplot(gs[1, 2])
    stage_bottom = np.zeros(len(turns))
    stage_series = [
        ("grievance", grievance_counts, "#5c6bc0"),
        ("protest", protest_counts, "#fdd835"),
        ("mass protest", mass_counts, "#fb8c00"),
        ("riot", riot_counts, "#e53935"),
        ("insurgency", insurgency_counts, "#8e24aa"),
        ("civil conflict", civil_counts, "#212121"),
    ]
    for label, values, color in stage_series:
        ax6.bar(turns, values, bottom=stage_bottom, label=label, color=color, alpha=0.92)
        stage_bottom = stage_bottom + np.array(values)
    ax6.set_title("Domestic stage counts by turn")
    ax6.set_xlabel("Turn")
    ax6.set_ylabel("Country count")
    ax6.legend(loc="best", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_dir / "dashboard.png", dpi=180)
    plt.close(fig)


def plot_comparison(base_dir: Path, scenario_results: Dict[str, dict]) -> None:
    if plt is None:
        return

    scenario_keys = list(scenario_results.keys())
    first = scenario_results[scenario_keys[0]]
    second = scenario_results[scenario_keys[1]]

    fig, axes = plt.subplots(2, 3, figsize=(18, 9))

    for scenario_key, result in scenario_results.items():
        label = result["summary"]["scenario_name"]
        turns = [row["turn"] for row in result["aggregate_rows"]]
        axes[0, 0].plot(turns, [row["avg_S"] for row in result["aggregate_rows"]], marker="o", label=label)
        axes[0, 1].plot(
            turns,
            [row["avg_war_burden"] for row in result["aggregate_rows"]],
            marker="o",
            label=f"{label} war",
        )
        axes[0, 1].plot(
            turns,
            [row["avg_domestic_burden"] for row in result["aggregate_rows"]],
            marker="o",
            linestyle="--",
            alpha=0.9,
            label=f"{label} domestic",
        )
        axes[0, 2].plot(
            turns,
            [row["avg_protest_pressure"] for row in result["aggregate_rows"]],
            marker="o",
            label=f"{label} protest",
        )
        axes[0, 2].plot(
            turns,
            [row["avg_riot_pressure"] for row in result["aggregate_rows"]],
            linestyle="--",
            alpha=0.9,
            label=f"{label} riot",
        )

    axes[0, 0].set_title("Average S by turn")
    axes[0, 0].set_xlabel("Turn")
    axes[0, 0].set_ylabel("Average S")
    axes[0, 0].grid(alpha=0.25)
    axes[0, 0].legend(loc="best")

    axes[0, 1].set_title("War burden and domestic burden")
    axes[0, 1].set_xlabel("Turn")
    axes[0, 1].set_ylabel("Burden")
    axes[0, 1].grid(alpha=0.25)
    axes[0, 1].legend(loc="best", fontsize=8)

    axes[0, 2].set_title("Domestic instability pressure")
    axes[0, 2].set_xlabel("Turn")
    axes[0, 2].set_ylabel("Pressure")
    axes[0, 2].grid(alpha=0.25)
    axes[0, 2].legend(loc="best", fontsize=8)

    final_a = {row["code"]: row for row in first["final_rows"]}
    final_b = {row["code"]: row for row in second["final_rows"]}
    codes = sorted(final_a.keys())
    delta_s = [final_b[code]["S"] - final_a[code]["S"] for code in codes]
    delta_domestic = [final_b[code]["domestic_burden"] - final_a[code]["domestic_burden"] for code in codes]

    axes[1, 0].barh(codes, delta_s, color=["#2e7d32" if value >= 0 else "#c62828" for value in delta_s])
    axes[1, 0].set_title("Delta S: high adaptation minus low adaptation")
    axes[1, 0].set_xlabel("Delta S")
    axes[1, 0].axvline(0.0, color="black", linewidth=1)

    y = np.arange(len(codes))
    axes[1, 1].barh(y - 0.18, [final_a[code]["support_needed"] for code in codes], height=0.32, label="low adaptation", color="#ef9a9a")
    axes[1, 1].barh(y + 0.18, [final_b[code]["support_needed"] for code in codes], height=0.32, label="high adaptation", color="#90caf9")
    axes[1, 1].set_yticks(y)
    axes[1, 1].set_yticklabels(codes)
    axes[1, 1].set_xlabel("Support needed")
    axes[1, 1].set_title("Final support needed by country")
    axes[1, 1].legend(loc="best")

    axes[1, 2].barh(
        codes,
        delta_domestic,
        color=["#2e7d32" if value <= 0 else "#c62828" for value in delta_domestic],
    )
    axes[1, 2].set_title("Delta domestic burden: high minus low")
    axes[1, 2].set_xlabel("Delta domestic burden")
    axes[1, 2].axvline(0.0, color="black", linewidth=1)

    for axis in axes.flat:
        if axis not in (axes[1, 0], axes[1, 2]):
            axis.grid(alpha=0.20)

    fig.tight_layout()
    fig.savefig(base_dir / "comparison.png", dpi=180)
    plt.close(fig)


def run_scenario(config: dict, scenario: dict, output_dir: Path, rng: np.random.Generator) -> dict:
    states = build_initial_states(config)
    event_map = {event["turn"]: event for event in config.get("events", [])}
    rows: List[dict] = []
    event_log: List[dict] = []
    aggregate_rows: List[dict] = []
    conflict_rows: List[dict] = []

    for turn in range(1, config["meta"]["turns"] + 1):
        event = event_map.get(turn, {})
        modifiers = deepcopy(event.get("modifiers", {}))
        if event.get("country_effects"):
            apply_country_effects(states, event["country_effects"])

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
                "cooperation_transfers": transfers,
                "domestic_events": domestic_events,
                "conflict_events": conflict_events,
            }
        )

    write_csv(output_dir / "turns.csv", rows)
    write_csv(output_dir / "aggregate.csv", aggregate_rows)
    write_csv(output_dir / "conflicts.csv", conflict_rows)
    write_jsonl(output_dir / "events.jsonl", event_log)

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
    write_json(output_dir / "summary.json", summary)
    write_markdown_summary(output_dir / "summary.md", summary, final_rows, event_log)
    plot_scenario_dashboard(output_dir, {
        "rows": rows,
        "aggregate_rows": aggregate_rows,
        "final_rows": final_rows,
        "summary": summary,
    })

    return {
        "rows": rows,
        "aggregate_rows": aggregate_rows,
        "event_log": event_log,
        "summary": summary,
        "final_rows": final_rows,
        "conflict_rows": conflict_rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a coarse world simulation demo.")
    parser.add_argument(
        "--config",
        default="scenarios/major_powers_world_demo.yaml",
        help="Path to the world demo YAML config.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    base_dir = Path(config["meta"]["output_dir"])
    base_dir.mkdir(parents=True, exist_ok=True)

    scenario_results = {}
    for scenario in config["scenarios"]:
        out_dir = scenario_output_dir(base_dir, scenario["key"])
        rng = np.random.default_rng(scenario_seed(config, scenario))
        scenario_results[scenario["key"]] = run_scenario(config, scenario, out_dir, rng)

    write_comparison_report(base_dir, scenario_results)

    manifest = {
        "config": str(config_path),
        "output_dir": str(base_dir),
        "scenarios": [
            {
                "key": scenario["key"],
                "name": scenario["name"],
            }
            for scenario in config["scenarios"]
        ],
        "viewer": {
            "turn_duration_months": config.get("meta", {}).get("turn_duration_months", 1),
            "default_scenario": config.get("meta", {}).get(
                "default_scenario",
                config["scenarios"][0]["key"],
            ),
        },
        "graph": {
            "cooperation": [
                {
                    "source": edge["donor"],
                    "target": edge["target"],
                    "weight": edge["weight"],
                    "kind": "cooperation",
                }
                for edge in config.get("cooperation_links", [])
            ],
            "rivalries": [
                {
                    "source": edge["actor"],
                    "target": edge["target"],
                    "weight": edge["base_tension"],
                    "domain": edge["domain"],
                    "kind": "rivalry",
                }
                for edge in config.get("rivalries", [])
            ],
        },
    }
    write_json(base_dir / "manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
