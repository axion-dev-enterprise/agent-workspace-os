#version 330
uniform sampler2D sceneTexture;
uniform sampler2D typeTexture;
uniform vec2 resolution;
uniform float time;
in vec2 uv;
out vec4 fragColor;

vec3 aces(vec3 x) {
    return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233)) + floor(time * 30.0)) * 43758.5453);
}

void main() {
    vec3 c = texture(sceneTexture, uv).rgb;
    vec2 radius = vec2(2.5) / resolution;
    vec3 glow = vec3(0.0);
    for (int x = -2; x <= 2; x++) {
        for (int y = -2; y <= 2; y++) {
            glow += max(texture(sceneTexture, uv + vec2(x, y) * radius).rgb - 1.1, 0.0) / 25.0;
        }
    }
    c += glow * 0.12;

    float vignette = 1.0 - 0.22 * dot((uv - 0.5) * vec2(1.25, 1.0), (uv - 0.5) * vec2(1.25, 1.0));
    c = pow(aces(c * 1.06), vec3(1.0 / 2.2)) * vignette;
    c += (hash(gl_FragCoord.xy) - 0.5) / 380.0;

    vec4 text = texture(typeTexture, vec2(uv.x, 1.0 - uv.y));
    fragColor = vec4(mix(c, text.rgb, text.a), 1.0);
}
