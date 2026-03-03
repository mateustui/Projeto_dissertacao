from __future__ import annotations

import numpy as np

from orquestrador.core.geometry import compute_intrinsics, euler_to_rotation, triangulate


def test_compute_intrinsics_shapes() -> None:
    k, k_inv = compute_intrinsics(640, 480, 90)
    assert k.shape == (3, 3)
    assert k_inv.shape == (3, 3)
    eye = k @ k_inv
    assert np.allclose(eye, np.eye(3), atol=1e-6)


def test_euler_to_rotation_identity() -> None:
    r = euler_to_rotation(0, 0, 0)
    assert np.allclose(r, np.eye(3), atol=1e-9)


def test_triangulate_returns_expected_depth() -> None:
    k, k_inv = compute_intrinsics(640, 480, 90)

    r1 = np.eye(3)
    t1 = np.array([0.0, 0.0, 0.0])

    r2 = np.eye(3)
    t2 = np.array([0.10, 0.0, 0.0])

    px1 = (320, 240)
    px2 = (288, 240)

    p, err_mm = triangulate(k_inv, r1, t1, px1, r2, t2, px2)

    assert abs(p[2] - 1.0) < 0.05
    assert err_mm < 20.0
