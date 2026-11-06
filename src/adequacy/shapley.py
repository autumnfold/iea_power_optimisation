"""Exact two-player Shapley attribution of the change in a metric between 2019 and 2022.

Players: D (demand and resource conditions) and A (conventional availability). The value
of a scenario is the metric computed with each driver's inputs taken from its year:

    v00 = v(D 2019, A 2019)  scenario A1, modelled 2019
    v10 = v(D 2022, A 2019)  scenario A2
    v01 = v(D 2019, A 2022)  scenario A3
    v11 = v(D 2022, A 2022)  scenario A4, modelled 2022
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TwoPlayerShapley:
    total: float        # v11 - v00, the change to explain
    phi_d: float        # share of driver D
    phi_a: float        # share of driver A
    interaction: float  # v11 - v10 - v01 + v00, split equally between the players


def shapley_two_players(v00: float, v10: float, v01: float, v11: float) -> TwoPlayerShapley:
    """Each player's share is its marginal contribution averaged over the two orderings.

    Ordering "D first": D adds v10 - v00, then A adds v11 - v10.
    Ordering "A first": A adds v01 - v00, then D adds v11 - v01.
    """
    phi_d = 0.5 * ((v10 - v00) + (v11 - v01))
    phi_a = 0.5 * ((v01 - v00) + (v11 - v10))
    return TwoPlayerShapley(
        total=v11 - v00,
        phi_d=phi_d,
        phi_a=phi_a,
        interaction=v11 - v10 - v01 + v00,
    )
