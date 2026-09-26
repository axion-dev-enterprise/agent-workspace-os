"""Modular 3D Film Renderer for Motion Render Service."""
from __future__ import annotations

import math
from pathlib import Path
import subprocess
import time
from typing import Callable, Sequence

import moderngl
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from motion_engine.math3d import normal, ortho, look_at, ease
from motion_engine.pipeline import find_ffmpeg_binary

try:
    from .scenes import SCENE_REGISTRY, get_autonomous_core_scene, get_autonomous_core_camera
except (ImportError, ValueError):
    from scenes import SCENE_REGISTRY, get_autonomous_core_scene, get_autonomous_core_camera

SHADERS_DIR = Path(__file__).resolve().parent / "shaders"


def create_beveled_cube() -> np.ndarray:
    """Generate beveled cube mesh (vertices + normals)."""
    r = 0.12
    steps = np.array([-1.0, -0.99, -0.96, -0.91, -0.87, 0.87, 0.91, 0.96, 0.99, 1.0])
    vertices = []
    for axis in range(3):
        others = [a for a in range(3) if a != axis]
        for sign in [-1, 1]:
            face = []
            for u in steps:
                row = []
                for v in steps:
                    p = np.zeros(3)
                    p[axis], p[others[0]], p[others[1]] = sign, u, v
                    center = np.clip(p, -1.0 + r, 1.0 - r)
                    n = normal(p - center)
                    row.append(np.concatenate([center + n * r, n]))
                face.append(row)
            for i in range(len(steps) - 1):
                for j in range(len(steps) - 1):
                    a, b, c, d = face[i][j], face[i + 1][j], face[i + 1][j + 1], face[i][j + 1]
                    vertices.extend([a, b, c, a, c, d])
    return np.array(vertices, dtype="f4")


class TypographyOverlay:
    """Editorial, high-precision typography compositor for video frames."""

    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.factor = width / 1080.0
        self.font_path = "C:/Windows/Fonts/bahnschrift.ttf"
        self.fonts = {}

    def font(self, size: int):
        pixels = max(8, round(size * self.factor))
        if pixels not in self.fonts:
            self.fonts[pixels] = ImageFont.truetype(self.font_path, pixels)
        return self.fonts[pixels]

    def spaced(self, draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, size: int, spacing: float, fill: tuple):
        x, y = xy[0] * self.factor, xy[1] * self.factor
        f = self.font(size)
        for letter in text:
            draw.text((x, y), letter, font=f, fill=fill)
            x += draw.textlength(letter, font=f) + spacing * self.factor

    def render(self, t: float) -> bytes:
        layer = Image.new("RGBA", (self.width, self.height))
        d = ImageDraw.Draw(layer)

        # Header and Footer Brand Framing
        self.spaced(d, (88, 92), "A X I O N", 32, 2, (230, 235, 242, 255))
        self.spaced(d, (89, 1795), "THE AUTONOMOUS OPERATING SYSTEM", 18, 3, (135, 155, 175, 255))

        # Narrative Chapters
        chapters = [
            (0.0, 3.2, "01 / ORIGEM", ["Uma nova ordem", "de inteligência."], 108),
            (3.2, 7.8, "02 / ACOPLAMENTO", ["Autonomia. Precisão.", "Governança."], 104),
            (7.8, 11.8, "03 / ESCALA", ["Do conceito", "à escala global."], 108),
        ]
        for start, end, label, lines, size in chapters:
            alpha = ease(start, start + 0.35, t) * (1.0 - ease(end - 0.30, end, t))
            if alpha <= 0.0:
                continue
            drift = 16.0 * (1.0 - ease(start, start + 0.6, t))
            self.spaced(d, (90, 268 + drift), label, 22, 3, (130, 165, 195, round(255 * alpha)))
            for k, line in enumerate(lines):
                d.text(
                    (86 * self.factor, (330 + k * (size * 1.14) + drift) * self.factor),
                    line,
                    font=self.font(size),
                    fill=(236, 242, 248, round(255 * alpha))
                )

        # Final Lockup
        end_alpha = ease(12.0, 12.6, t)
        if end_alpha > 0.0:
            self.spaced(d, (90, 275), "O FUTURO É DETERMINÍSTICO.", 21, 3, (135, 170, 205, round(255 * end_alpha)))
            self.spaced(d, (78, 360), "AXION", 192, 2, (240, 245, 250, round(255 * end_alpha)))
            d.text(
                (92 * self.factor, 620 * self.factor),
                "Construa o próximo.",
                font=self.font(46),
                fill=(205, 225, 245, round(255 * end_alpha))
            )

        # Baseline
        d.line(
            [(88 * self.factor, 1730 * self.factor), (992 * self.factor, 1730 * self.factor)],
            fill=(140, 170, 200, 55),
            width=max(1, round(self.factor))
        )
        return layer.tobytes()


class ServiceFilmRenderer:
    """Renderer managed by the service daemon."""

    def __init__(self, width: int = 1080, height: int = 1920, scene_id: str = "autonomous-core"):
        self.width, self.height = width, height
        self.scene_id = scene_id
        scene_conf = SCENE_REGISTRY.get(scene_id, SCENE_REGISTRY["autonomous-core"])
        self.scene_func = scene_conf["scene_func"]
        self.camera_func = scene_conf["camera_func"]

        self.ctx = ctx = moderngl.create_context(standalone=True, require=330)
        self.info = {k: ctx.info[k] for k in ["GL_VENDOR", "GL_RENDERER", "GL_VERSION"]}

        # 3D Mesh & Instancing
        self.vbo = ctx.buffer(create_beveled_cube().tobytes())
        self.instances = ctx.buffer(reserve=256 * 80)
        self.program = ctx.program(
            vertex_shader=(SHADERS_DIR / "scene.vert").read_text(encoding="utf-8"),
            fragment_shader=(SHADERS_DIR / "scene.frag").read_text(encoding="utf-8")
        )
        self.vao = ctx.vertex_array(
            self.program,
            [
                (self.vbo, "3f 3f", "inPosition", "inNormal"),
                (self.instances, "4f 4f 4f 4f 4f /i", "model0", "model1", "model2", "model3", "material")
            ]
        )

        # Shadow Pass (PCF depth map)
        shadow_vertex = """#version 330
in vec3 inPosition;
in vec4 model0, model1, model2, model3;
uniform mat4 lightProjection;
void main() {
    mat4 model = mat4(model0, model1, model2, model3);
    gl_Position = lightProjection * model * vec4(inPosition, 1.0);
}"""
        self.shadow_program = ctx.program(
            vertex_shader=shadow_vertex,
            fragment_shader="#version 330\nvoid main() {}"
        )
        self.shadow_vao = ctx.vertex_array(
            self.shadow_program,
            [
                (self.vbo, "3f 12x", "inPosition"),
                (self.instances, "4f 4f 4f 4f 16x /i", "model0", "model1", "model2", "model3")
            ]
        )
        self.shadow = ctx.depth_texture((2048, 2048))
        self.shadow.repeat_x = self.shadow.repeat_y = False
        self.shadow.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.shadow.compare_func = "<="
        self.shadow_fbo = ctx.framebuffer(depth_attachment=self.shadow)

        light_eye = np.array([-5.0, 9.0, 6.0], dtype="f4")
        self.light_vp = ortho(7.0, 0.1, 35.0) @ look_at(light_eye, [0.0, 0.0, 0.0])
        self.shadow_program["lightProjection"].write(self.light_vp.T.astype("f4").tobytes())
        self.program["lightProjection"].write(self.light_vp.T.astype("f4").tobytes())

        # Multisampling & HDR
        self.color = ctx.texture((width, height), 4, dtype="f2")
        self.resolved = ctx.framebuffer([self.color], ctx.depth_renderbuffer((width, height)))
        self.msaa = ctx.framebuffer(
            [ctx.renderbuffer((width, height), 4, samples=4, dtype="f2")],
            ctx.depth_renderbuffer((width, height), samples=4)
        )
        self.output = ctx.simple_framebuffer((width, height), components=3)

        # Typography Layer
        self.type_texture = ctx.texture((width, height), 4)
        self.type_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

        post_vertex = """#version 330
out vec2 uv;
void main() {
    vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2);
    uv = p;
    gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
}"""
        self.post = ctx.program(
            vertex_shader=post_vertex,
            fragment_shader=(SHADERS_DIR / "post.frag").read_text(encoding="utf-8")
        )
        self.post_vao = ctx.vertex_array(self.post, [])
        self.typography = TypographyOverlay(width, height)

    def render_frame(self, t: float) -> bytes:
        instances = self.scene_func(t)
        self.instances.write(instances.tobytes())
        cam_pos, view_proj = self.camera_func(t, self.width / self.height)

        # Shadow Pass
        self.shadow_fbo.clear()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.shadow_vao.render(moderngl.TRIANGLES, instances=len(instances))

        # Scene Pass
        self.msaa.clear(0.007, 0.010, 0.016, 1.0)
        self.program["viewProjection"].write(view_proj.T.astype("f4").tobytes())
        self.program["eye"].write(cam_pos.astype("f4").tobytes())
        self.shadow.use(0)
        self.program["shadowMap"].value = 0
        self.vao.render(moderngl.TRIANGLES, instances=len(instances))

        # Resolve MSAA
        self.ctx.copy_framebuffer(self.resolved, self.msaa)

        # Typography
        self.type_texture.write(self.typography.render(t))

        # Post Process
        self.output.use()
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.color.use(0)
        self.type_texture.use(1)
        self.post["sceneTexture"].value = 0
        self.post["typeTexture"].value = 1
        self.post["resolution"].value = (self.width, self.height)
        self.post["time"].value = t
        self.post_vao.render(moderngl.TRIANGLE_STRIP, vertices=4)

        return self.output.read(components=3)

    def save_image(self, t: float) -> Image.Image:
        raw = self.render_frame(t)
        return Image.frombytes("RGB", (self.width, self.height), raw).transpose(Image.FLIP_TOP_BOTTOM)

    def close(self):
        self.ctx.release()
