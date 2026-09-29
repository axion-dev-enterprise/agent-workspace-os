"""Advanced 3D Geometry and Mesh Processing via Trimesh."""
from __future__ import annotations

from pathlib import Path
from typing import Literal
import numpy as np
import trimesh


def mesh_to_vbo_bytes(mesh: trimesh.Trimesh) -> bytes:
    """
    Extract interleaved position (3f) and normal (3f) buffer for ModernGL.
    Returns contiguous bytes of format (N_triangles * 3, 6 floats).
    """
    # Unroll faces to get per-face-vertex arrays for strict flat/smooth shading
    vertices = mesh.vertices[mesh.faces].reshape(-1, 3).astype(np.float32)
    
    # Compute or recompute face normals if needed
    if mesh.vertex_normals is not None and len(mesh.vertex_normals) == len(mesh.vertices):
        normals = mesh.vertex_normals[mesh.faces].reshape(-1, 3).astype(np.float32)
    else:
        mesh.recompute_normals()
        normals = mesh.vertex_normals[mesh.faces].reshape(-1, 3).astype(np.float32)

    interleaved = np.hstack([vertices, normals]).astype(np.float32)
    return interleaved.tobytes()


def create_primitive(
    kind: Literal["icosphere", "torus", "cylinder", "capsule", "box"] = "icosphere",
    **kwargs
) -> trimesh.Trimesh:
    """Generate high-fidelity procedural 3D geometric meshes."""
    if kind == "icosphere":
        subdivisions = kwargs.get("subdivisions", 3)
        radius = kwargs.get("radius", 1.0)
        return trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)
    elif kind == "torus":
        major_radius = kwargs.get("major_radius", 2.0)
        minor_radius = kwargs.get("minor_radius", 0.3)
        major_sections = kwargs.get("major_sections", 32)
        minor_sections = kwargs.get("minor_sections", 32)
        return trimesh.creation.torus(major_radius=major_radius, minor_radius=minor_radius, major_sections=major_sections, minor_sections=minor_sections)
    elif kind == "cylinder":
        radius = kwargs.get("radius", 0.5)
        height = kwargs.get("height", 2.0)
        sections = kwargs.get("sections", 32)
        return trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    elif kind == "capsule":
        height = kwargs.get("height", 2.0)
        radius = kwargs.get("radius", 0.5)
        return trimesh.creation.capsule(height=height, radius=radius)
    elif kind == "box":
        extents = kwargs.get("extents", (1.0, 1.0, 1.0))
        return trimesh.creation.box(extents=extents)
    else:
        raise ValueError(f"Unknown primitive kind: {kind}")


def load_mesh_asset(path: str | Path) -> trimesh.Trimesh:
    """Load external 3D asset (.glb, .gltf, .obj, .stl) and merge into single Trimesh."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"3D asset file not found: {p}")
    
    loaded = trimesh.load(str(p), force="mesh")
    if isinstance(loaded, trimesh.Scene):
        # Merge all scene geometries into one
        mesh = trimesh.util.concatenate(tuple(loaded.geometry.values()))
    else:
        mesh = loaded

    mesh.fix_normals()
    return mesh
