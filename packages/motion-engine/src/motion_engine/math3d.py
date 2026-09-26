"""3D Mathematics, Projections and Parametric Kinematics for Deterministic Renders."""
from __future__ import annotations

import math
from typing import Sequence
import numpy as np


def ease(start: float, end: float, value: float) -> float:
    """Perlin quintic smoothstep (C2 continuous curvature) between start and end."""
    if end <= start:
        return 1.0 if value >= end else 0.0
    x = float(np.clip((value - start) / (end - start), 0.0, 1.0))
    return float(x * x * x * (x * (x * 6.0 - 15.0) + 10.0))


def normal(v: Sequence[float] | np.ndarray) -> np.ndarray:
    """Normalize a 3D vector safely."""
    a = np.asarray(v, dtype=np.float32)
    norm = np.linalg.norm(a)
    if norm == 0.0:
        return a
    return a / norm


def look_at(
    eye: Sequence[float] | np.ndarray,
    target: Sequence[float] | np.ndarray,
    up: Sequence[float] | np.ndarray = (0.0, 1.0, 0.0)
) -> np.ndarray:
    """Standard OpenGL LookAt view matrix (column-major layout)."""
    eye_arr = np.asarray(eye, dtype=np.float32)
    f = normal(np.asarray(target, dtype=np.float32) - eye_arr)
    s = normal(np.cross(f, np.asarray(up, dtype=np.float32)))
    u = np.cross(s, f)

    result = np.eye(4, dtype=np.float32)
    result[:3, :3] = np.array([s, u, -f], dtype=np.float32)
    result[:3, 3] = -result[:3, :3] @ eye_arr
    return result


def perspective(aspect: float, fov: float = 36.0, near: float = 0.1, far: float = 100.0) -> np.ndarray:
    """Standard OpenGL perspective projection matrix."""
    f = 1.0 / math.tan(math.radians(fov) / 2.0)
    return np.array([
        [f / aspect, 0.0, 0.0, 0.0],
        [0.0, f, 0.0, 0.0],
        [0.0, 0.0, (far + near) / (near - far), (2.0 * far * near) / (near - far)],
        [0.0, 0.0, -1.0, 0.0]
    ], dtype=np.float32)


def ortho(size: float, near: float = -10.0, far: float = 10.0) -> np.ndarray:
    """Orthographic projection matrix for shadow maps and HUDs."""
    return np.array([
        [1.0 / size, 0.0, 0.0, 0.0],
        [0.0, 1.0 / size, 0.0, 0.0],
        [0.0, 0.0, -2.0 / (far - near), -(far + near) / (far - near)],
        [0.0, 0.0, 0.0, 1.0]
    ], dtype=np.float32)


def rotation_matrix(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> np.ndarray:
    """Euler XYZ rotation matrix."""
    cx, sx = math.cos(x), math.sin(x)
    cy, sy = math.cos(y), math.sin(y)
    cz, sz = math.cos(z), math.sin(z)
    
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float32)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float32)
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float32)
    return rz @ ry @ rx


def create_instance_buffer(
    position: Sequence[float],
    scale: Sequence[float],
    color: Sequence[float],
    roughness: float = 0.3,
    angles: Sequence[float] = (0.0, 0.0, 0.0)
) -> np.ndarray:
    """
    Pack an instanced model matrix (16 floats) + RGB (3 floats) + Roughness (1 float).
    Total: 20 floats (80 bytes per instance).
    """
    model = np.eye(4, dtype=np.float32)
    model[:3, :3] = rotation_matrix(*angles) @ np.diag(np.maximum(scale, 0.0001))
    model[:3, 3] = position
    return np.concatenate([
        model.T.reshape(-1),
        np.asarray(color, dtype=np.float32),
        np.array([roughness], dtype=np.float32)
    ]).astype(np.float32)
