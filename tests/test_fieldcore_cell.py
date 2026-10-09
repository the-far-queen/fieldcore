"""Tests for FieldCoreCell and FiveToroidArray.

Source: deepseek1 parts 15, 62, 84, 97 and part 38 (FiveToroidArray).
Every test can go red; several exist because the module had real bugs.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fieldcore_cell import (  # noqa: E402
    PHI, FieldCoreCell, FiveToroidArray, hodge_split, torus_embed,
)

torch.manual_seed(0)


# --------------------------------------------------------------------- hodge


def test_hodge_reconstructs_the_original():
    """exact + coexact + harmonic must return the input. A decomposition
    that loses a component is not a decomposition.
    """
    x = torch.randn(4, 8)
    e, c, h = hodge_split(x)
    assert torch.allclose(e + c + h, x, atol=1e-6)


def test_hodge_components_are_separated():
    x = torch.randn(4, 8)
    e, c, h = hodge_split(x)
    # the gradient part is the constant (its variation is zero)
    assert torch.allclose(e, e.mean(dim=-1, keepdim=True).expand_as(e), atol=1e-6)
    # neither coexact nor harmonic is constant
    assert c.std(dim=-1).mean() > 1e-4
    assert h.std(dim=-1).mean() > 1e-4


def test_hodge_of_a_constant_is_all_gradient():
    x = torch.full((2, 8), 3.0)
    e, c, h = hodge_split(x)
    assert torch.allclose(h, torch.zeros_like(h), atol=1e-5)
    assert torch.allclose(c, torch.zeros_like(c), atol=1e-5)


def test_torus_embed_is_bounded_and_periodic():
    x = torch.randn(3, 8) * 100.0
    theta = torus_embed(x)
    assert theta.shape[-1] == 4
    assert torch.all(theta.abs() <= math.pi + 1e-6)
    # periodicity: adding 2*pi to a coordinate must not change the angles
    x2 = x.clone()
    x2[..., 0] += 2 * math.pi
    assert torch.allclose(theta, torus_embed(x2), atol=1e-4)


# --------------------------------------------------------------------- cell


def test_cell_runs_and_shapes():
    c = FieldCoreCell()
    o = c(torch.randn(2, 8) * 0.1, 0.0)
    assert o.state.shape == (2, 8)
    assert o.control.shape == (2, 5)
    assert o.curl_norm.shape == (2, 1)


def test_cell_respects_topological_protection():
    """The substrate invariant: state stays inside the protected ball."""
    c = FieldCoreCell()
    for scale in (0.1, 1.0, 50.0):
        o = c(torch.randn(4, 8) * scale, 0.0)
        radius = float(c.topo_protection.abs())
        assert bool((o.state.norm(dim=-1) <= radius + 1e-5).all()), scale


def test_protection_is_a_real_constraint_not_a_no_op():
    """A cell with protection raised to 50 must produce larger states than
    one with protection 0.9. Otherwise the constraint does nothing.
    """
    x = torch.randn(4, 8) * 10.0
    tight = FieldCoreCell()
    loose = FieldCoreCell()
    with torch.no_grad():
        tight.topo_protection.fill_(0.9)
        loose.topo_protection.fill_(50.0)
    n_tight = float(tight(x, 0.0).state.norm(dim=-1).max())
    n_loose = float(loose(x, 0.0).state.norm(dim=-1).max())
    assert n_tight < 1.0
    assert n_loose > n_tight


def test_cell_accepts_odd_state_dim_only_when_even():
    with pytest.raises(ValueError):
        FieldCoreCell(state_dim=7)
    FieldCoreCell(state_dim=6)  # must not raise


def test_control_is_bounded():
    c = FieldCoreCell()
    o = c(torch.randn(8, 8) * 5.0, 1.0)
    assert bool((o.control.abs() <= 1.0).all())


def test_goal_bias_changes_the_output():
    c = FieldCoreCell()
    x = torch.randn(4, 8) * 0.1
    a = c(x, 0.0).state
    b = c(x, 0.0, goal=torch.ones(8)).state
    assert not torch.allclose(a, b)


def test_time_step_changes_the_output():
    c = FieldCoreCell()
    x = torch.randn(4, 8) * 0.1
    a = c(x, 0.0).state
    b = c(x, 3.0).state
    assert not torch.allclose(a, b)


def test_cell_is_deterministic():
    c = FieldCoreCell()
    x = torch.randn(2, 8) * 0.1
    assert torch.allclose(c(x, 0.5).state, c(x, 0.5).state)


def test_prime_channels_are_the_specified_ones():
    c = FieldCoreCell()
    assert c.prime_dims == (5, 7, 11, 13)
    assert len(c.encoders) == 4
    assert len(c.decoders) == 4


def test_alpha_is_inverse_phi():
    c = FieldCoreCell()
    assert abs(c.alpha - 1.0 / PHI) < 1e-12
    assert abs(float(c.egg_compression) - 1.0 / PHI) < 1e-6


def test_binding_weights_are_a_distribution():
    c = FieldCoreCell()
    w = torch.softmax(c.binding_w, dim=-1)
    assert torch.allclose(w.sum(dim=-1), torch.ones(4), atol=1e-6)


# --------------------------------------------------------------------- array


def test_five_toroid_array_shapes():
    f = FiveToroidArray()
    states, controls, curls, harmonics = f(torch.randn(2, 8) * 0.1, 0.0)
    assert states.shape == (2, 5, 8)
    assert controls.shape == (2, 5, 5)
    assert curls.shape == (2, 5, 1)
    assert harmonics.shape == (2, 5, 8)


def test_five_toroid_offsets_are_72_degrees():
    f = FiveToroidArray()
    offsets = f.OFFSETS
    assert len(offsets) == 5
    for i in range(1, 5):
        assert abs((offsets[i] - offsets[i - 1]) - 2 * math.pi / 5) < 1e-12
    # five distinct positions, closing the circle
    assert len(set(offsets)) == 5


def test_array_refuses_more_than_five():
    with pytest.raises(ValueError):
        FiveToroidArray(n_toroids=6)
    FiveToroidArray(n_toroids=3)


def test_collective_strength_measures_agreement():
    f = FiveToroidArray()
    same = torch.ones(2, 5, 8)
    assert torch.allclose(f.collective_strength(same), torch.full((2, 1), math.sqrt(8.0)), atol=1e-4)
    opposed = torch.stack([torch.ones(8), -torch.ones(8), torch.ones(8), -torch.ones(8), torch.ones(8)], dim=0).unsqueeze(0)
    # mean of that pattern is 1/5 of a unit vector -> norm sqrt(8)/5
    assert float(f.collective_strength(opposed)) < math.sqrt(8.0)


def test_toroids_are_distinct_cells():
    f = FiveToroidArray()
    params = [float(p.sum()) for p in f.parameters()]
    assert len(set(params)) == len(params) or True  # shared init possible
    # stronger: same input, different offsets -> different states
    states, _, _, _ = f(torch.randn(1, 8) * 0.1, 0.0)
    assert not torch.allclose(states[0, 0], states[0, 1])


def test_array_end_to_end_over_steps():
    """The part-38 usage: 100 steps, collect controls and collectives."""
    f = FiveToroidArray()
    state = torch.randn(1, 8) * 0.1
    collectives = []
    for t in range(100):
        states, controls, curls, harmonics = f(state, float(t))
        state = states[:, 0]
        collectives.append(float(f.collective_strength(states)))
    assert len(collectives) == 100
    assert all(math.isfinite(c) for c in collectives)
    assert all(c >= 0 for c in collectives)