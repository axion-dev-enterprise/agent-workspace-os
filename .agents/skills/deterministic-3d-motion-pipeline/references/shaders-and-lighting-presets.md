# Shaders & Lighting Presets — ModernGL / GLSL

Presets de materiais PBR, técnicas de iluminação de estúdio e efeitos de pós-processamento para renderização determinística em OpenGL 3.3 Core Profile.

---

## 1. Iluminação de Estúdio de Três Pontos (Three-Point Studio Lighting)

```
                     [Top-Down / Rim Light]
                       (-3.0, 2.0, -4.0)
                             \
                              \
          [Objeto 3D] <--- (0, 0, 0)
          /         \
         /           \
  [Key Light]       [Fill Light / Ambient]
(4.0, 7.0, 5.0)     (-4.0, 1.0, 3.0)
```

1. **Key Light (Luz Principal)**:
   - Tipo: Direcional potente com projeção ortográfica para o shadow map.
   - Posição: Superior diagonal $(4.0, 7.0, 5.0)$.
   - Cor: Branco frio / neutro `vec3(1.0, 0.98, 0.95)`.
   - Gera sombras nítidas suavizadas por filtro PCF.
2. **Rim Light (Luz de Contorno)**:
   - Tipo: Direcional rasante traseira.
   - Posição: Traseira oposta $(-3.0, 2.0, -4.0)$.
   - Cor: Azul glacial `vec3(0.35, 0.75, 1.0)`.
   - Propósito: Descolar o objeto 3D do plano de fundo escuro.
3. **Ambient / Synthetic HDRI**:
   - Gradiente hemisférico vertical:
     $$L_{\text{amb}} = \text{lerp}(C_{\text{chão}}, C_{\text{céu}}, 0.5 \cdot (N_y + 1.0))$$
   - $C_{\text{céu}} = \text{vec3}(0.08, 0.12, 0.22)$, $C_{\text{chão}} = \text{vec3}(0.02, 0.03, 0.05)$.

---

## 2. Sombreamento Metálico GGX / Trowbridge-Reitz

Equação de microfacetas para destaque especular fisicamente baseado:

$$D_{\text{GGX}}(N, H, \alpha) = \frac{\alpha^2}{\pi \left((N \cdot H)^2 (\alpha^2 - 1) + 1\right)^2}$$

Implementação em GLSL:
```glsl
float distribution_ggx(vec3 N, vec3 H, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float NdotH = max(dot(N, H), 0.0);
    float NdotH2 = NdotH * NdotH;
    float denom = (NdotH2 * (a2 - 1.0) + 1.0);
    return a2 / (3.14159265 * denom * denom);
}

float geometry_schlick_ggx(float NdotV, float roughness) {
    float r = (roughness + 1.0);
    float k = (r * r) / 8.0;
    return NdotV / (NdotV * (1.0 - k) + k);
}

vec3 fresnel_schlick(float cos_theta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cos_theta, 0.0, 1.0), 5.0);
}
```

---

## 3. Shader de Sombra Suave com PCF (Percentage-Closer Filtering)

```glsl
#version 330 core

float calc_shadow(sampler2D shadow_tex, vec4 shadow_coord, vec3 normal, vec3 light_dir) {
    vec3 proj = shadow_coord.xyz / shadow_coord.w * 0.5 + 0.5;
    if (proj.z > 1.0 || proj.x < 0.0 || proj.x > 1.0 || proj.y < 0.0 || proj.y > 1.0) {
        return 0.0;
    }
    
    float current_depth = proj.z;
    float bias = max(0.002 * (1.0 - dot(normal, light_dir)), 0.0006);
    float shadow = 0.0;
    vec2 texel = 1.0 / textureSize(shadow_tex, 0);
    
    // Kernel 3x3 PCF
    for (int x = -1; x <= 1; ++x) {
        for (int y = -1; y <= 1; ++y) {
            float pcf_depth = texture(shadow_tex, proj.xy + vec2(x, y) * texel).r;
            shadow += current_depth - bias > pcf_depth ? 1.0 : 0.0;
        }
    }
    return shadow / 9.0;
}
```

---

## 4. Tone Mapping Fílmico ACES (Academy Color Encoding System)

A curva ACES comprime altas intensidades de luz (luzes de estúdio e reflexos solares) com saturação natural de cores sem estourar o branco no canal RGB:

```glsl
vec3 aces_tone_mapping(vec3 color) {
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;
    return clamp((color * (a * color + b)) / (color * (c * color + d) + e), 0.0, 1.0);
}
```
