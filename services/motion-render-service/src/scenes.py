"""Scene definitions and choreography generators for Motion Render Service."""
from __future__ import annotations

import math
from typing import Sequence
import numpy as np

from motion_engine.math3d import (
    ease,
    create_instance_buffer,
    look_at,
    perspective
)


def mix_color(c1: np.ndarray, c2: np.ndarray, factor: float) -> np.ndarray:
    return c1 * (1.0 - factor) + c2 * factor


def get_autonomous_core_scene(t: float) -> np.ndarray:
    """Computes the 3D instanced geometry for 'The Autonomous Core' at time t."""
    blocks = []
    intro = ease(0.0, 3.2, t)
    assembly = ease(3.2, 7.8, t)
    expansion = ease(7.8, 11.8, t)
    monolith = ease(11.8, 14.5, t)

    titanium = np.array([0.10, 0.12, 0.16])
    silver = np.array([0.75, 0.80, 0.88])
    cyan_glow = np.array([0.25, 0.72, 1.0])

    # Central Core
    core_scale = 0.95 + 0.15 * math.sin(t * 3.5) * (1.0 - monolith)
    core_rot = t * 0.4 * (1.0 - monolith)
    core_mat = silver if monolith > 0.5 else mix_color(titanium, silver, assembly)
    blocks.append(create_instance_buffer(
        position=[0.0, 0.0, 0.0],
        scale=[core_scale, core_scale, core_scale],
        color=core_mat,
        roughness=0.18,
        angles=[core_rot * 0.5, core_rot, 0.0]
    ))

    # Inner Ring (8 modules)
    for i in range(8):
        theta = i * (2.0 * math.pi / 8.0)
        r_orbit = 3.8 * (1.0 - intro * 0.4) * (1.0 - assembly * 0.5) * (1.0 - monolith * 0.5)
        orbit_angle = theta + t * (0.8 + i * 0.05) * (1.0 - monolith)
        dock_x = math.cos(theta) * 1.5
        dock_y = math.sin(theta) * 1.5

        px = math.cos(orbit_angle) * r_orbit * (1.0 - monolith) + dock_x * monolith
        py = (math.sin(orbit_angle * 2.0) * 0.6) * (1.0 - monolith) + dock_y * monolith
        pz = math.sin(orbit_angle) * r_orbit * (1.0 - monolith)

        s = 0.35 + 0.15 * assembly
        color = cyan_glow if (i % 2 == 0 and assembly > 0.3) else silver
        blocks.append(create_instance_buffer(
            position=[px, py, pz],
            scale=[s, s, s],
            color=color,
            roughness=0.22,
            angles=[t * 1.2, t * 0.8, theta]
        ))

    # Outer Ring (8 modules)
    for j in range(8):
        phi = j * (2.0 * math.pi / 8.0) + (math.pi / 8.0)
        r_outer = 5.5 * (1.0 - intro * 0.3) * (1.0 - assembly * 0.3) * (1.0 - monolith * 0.7)
        orbit_outer = phi - t * 0.5 * (1.0 - monolith)

        px = math.cos(orbit_outer) * r_outer * (1.0 - monolith)
        py = math.sin(phi * 3.0 + t) * 1.2 * (1.0 - monolith)
        pz = math.sin(orbit_outer) * r_outer * (1.0 - monolith)

        s = 0.45 * (1.0 - monolith * 0.5)
        blocks.append(create_instance_buffer(
            position=[px, py, pz],
            scale=[s, s, s],
            color=titanium,
            roughness=0.28,
            angles=[0.0, orbit_outer, 0.0]
        ))

    # Satellite Constellation (Act 3)
    if expansion > 0.01:
        for k in range(12):
            psi = k * (2.0 * math.pi / 12.0)
            dist = 2.0 + expansion * 6.5
            px = math.cos(psi + t * 0.2) * dist
            py = math.sin(psi * 2.0) * 1.5 * expansion
            pz = math.sin(psi + t * 0.2) * dist
            node_s = 0.18 * expansion * (1.0 - monolith)
            if node_s > 0.01:
                blocks.append(create_instance_buffer(
                    position=[px, py, pz],
                    scale=[node_s, node_s, node_s],
                    color=cyan_glow,
                    roughness=0.15,
                    angles=[0, t * 2.0, 0]
                ))

    # Base Floor Grid (25 tiles)
    for gx in range(-2, 3):
        for gz in range(-2, 3):
            dist_g = math.sqrt(gx * gx + gz * gz)
            wave_h = math.sin(dist_g * 1.5 - t * 3.0) * 0.15 * intro
            blocks.append(create_instance_buffer(
                position=[gx * 1.6, -3.2 + wave_h, gz * 1.6],
                scale=[0.7, 0.05, 0.7],
                color=titanium * 0.7,
                roughness=0.35,
                angles=[0, 0, 0]
            ))

    return np.array(blocks, dtype="f4")


def get_autonomous_core_camera(t: float, aspect: float) -> tuple[np.ndarray, np.ndarray]:
    """Computes camera eye and ViewProjection matrix for 'The Autonomous Core'."""
    intro = ease(0.0, 3.2, t)
    assembly = ease(3.2, 7.8, t)
    expansion = ease(7.8, 11.8, t)
    monolith = ease(11.8, 14.5, t)

    start_pos = np.array([0.0, 13.0, 10.0])
    act2_angle = (t - 3.2) * 0.45
    act2_pos = np.array([math.sin(act2_angle) * 7.5, 3.6, math.cos(act2_angle) * 7.5])
    act3_pos = np.array([math.sin(2.0) * 11.0, 2.2, math.cos(2.0) * 11.0])
    act4_pos = np.array([0.0, 0.5, 9.2])

    pos = start_pos * (1.0 - intro) + act2_pos * intro
    if assembly > 0.0:
        pos = pos * (1.0 - assembly) + act2_pos * assembly
    if expansion > 0.0:
        pos = pos * (1.0 - expansion) + act3_pos * expansion
    if monolith > 0.0:
        pos = pos * (1.0 - monolith) + act4_pos * monolith

    target = np.array([0.0, -0.2 * (1.0 - monolith), 0.0])
    up = np.array([0.0, 1.0, 0.0])
    view = look_at(pos, target, up)
    proj = perspective(aspect, fov=38.0, near=0.1, far=100.0)
    return pos, proj @ view


SCENE_REGISTRY = {
    "autonomous-core": {
        "title": "AXION: The Autonomous Core",
        "scene_func": get_autonomous_core_scene,
        "camera_func": get_autonomous_core_camera,
        "duration": 15.0,
        "fps": 30
    }
}
