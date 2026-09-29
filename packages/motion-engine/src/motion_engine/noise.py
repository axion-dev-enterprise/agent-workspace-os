"""Procedural Multi-Octave Noise Generation via OpenSimplex."""
from __future__ import annotations

import numpy as np
import opensimplex


class ProceduralNoise:
    """Wrapper for OpenSimplex with fractional Brownian motion (fBm) multi-octave synthesis."""

    def __init__(self, seed: int = 260926):
        self.simplex = opensimplex.OpenSimplex(seed=seed)

    def noise2d(self, x: float, y: float) -> float:
        return self.simplex.noise2(x, y)

    def noise3d(self, x: float, y: float, z: float) -> float:
        return self.simplex.noise3(x, y, z)

    def noise4d(self, x: float, y: float, z: float, w: float) -> float:
        return self.simplex.noise4(x, y, z, w)

    def fbm3d(
        self,
        x: float,
        y: float,
        z: float,
        octaves: int = 4,
        lacunarity: float = 2.0,
        gain: float = 0.5
    ) -> float:
        """Fractional Brownian Motion (multi-scale turbulence) in 3D space."""
        total = 0.0
        frequency = 1.0
        amplitude = 1.0
        max_val = 0.0

        for _ in range(octaves):
            total += self.simplex.noise3(x * frequency, y * frequency, z * frequency) * amplitude
            max_val += amplitude
            amplitude *= gain
            frequency *= lacunarity

        return total / max_val

    def displace_vertices_3d(
        self,
        vertices: np.ndarray,
        time: float,
        freq: float = 1.2,
        strength: float = 0.15
    ) -> np.ndarray:
        """
        Displaces a vertex cloud [N, 3] procedurally based on 4D simplex noise (X, Y, Z, Time).
        Produces fluid, living geometric surfaces.
        """
        displaced = np.copy(vertices)
        for i in range(len(vertices)):
            vx, vy, vz = vertices[i]
            offset = self.noise4d(vx * freq, vy * freq, vz * freq, time * 0.8)
            norm = np.linalg.norm(vertices[i])
            if norm > 0.0:
                dir_v = vertices[i] / norm
                displaced[i] += dir_v * (offset * strength)
        return displaced
