#version 330
in vec3 worldPosition;
in vec3 worldNormal;
in vec4 surface;
in vec4 shadowPosition;
uniform vec3 eye;
uniform sampler2DShadow shadowMap;
out vec4 fragColor;
const float PI = 3.14159265;

vec3 studio(vec3 r, float roughness) {
    vec3 c = vec3(0.08, 0.11, 0.16) * (0.6 + 0.4 * max(r.y, 0.0));
    float power = mix(75.0, 8.0, roughness);
    c += vec3(4.0, 3.8, 3.4) * pow(max(dot(r, normalize(vec3(-3, 6, 4))), 0.0), power * 0.22);
    c += vec3(0.4, 0.95, 1.8) * pow(max(dot(r, normalize(vec3(4, 2, -3))), 0.0), power * 0.55);
    c += vec3(1.2, 1.35, 1.5) * pow(max(dot(r, normalize(vec3(0, 6, -1))), 0.0), power * 0.6);
    return c;
}

float shadowVisibility(vec3 n) {
    vec3 p = shadowPosition.xyz / shadowPosition.w * 0.5 + 0.5;
    if (p.z > 1.0 || p.x < 0.0 || p.x > 1.0 || p.y < 0.0 || p.y > 1.0) return 1.0;
    float bias = max(0.0007 * (1.0 - dot(n, normalize(vec3(-3, 6, 4)))), 0.00015);
    float s = 0.0;
    for (int x = -2; x <= 2; x++) {
        for (int y = -2; y <= 2; y++) {
            s += texture(shadowMap, vec3(p.xy + vec2(x, y) / 2048.0 * 1.4, p.z - bias));
        }
    }
    return s / 25.0;
}

vec3 brdf(vec3 n, vec3 v, vec3 l, vec3 radiance, vec3 albedo, float roughness, float metal) {
    vec3 h = normalize(v + l);
    float nv = max(dot(n, v), 0.001), nl = max(dot(n, l), 0.0);
    float nh = max(dot(n, h), 0.0), hv = max(dot(h, v), 0.0);
    float a2 = pow(roughness, 4.0);
    float d = a2 / max(PI * pow(nh * nh * (a2 - 1.0) + 1.0, 2.0), 0.0001);
    float k = pow(roughness + 1.0, 2.0) / 8.0;
    float g = nv / (nv * (1.0 - k) + k) * nl / (nl * (1.0 - k) + k);
    vec3 f0 = mix(vec3(0.04), albedo, metal);
    vec3 f = f0 + (1.0 - f0) * pow(1.0 - hv, 5.0);
    vec3 diffuse = (1.0 - f) * (1.0 - metal) * albedo / PI;
    return (diffuse + d * g * f / max(4.0 * nv * nl, 0.001)) * radiance * nl;
}

void main() {
    vec3 n = normalize(worldNormal), v = normalize(eye - worldPosition);
    vec3 albedo = surface.rgb;
    float roughness = surface.a;
    float metal = roughness > 0.65 ? 0.08 : 0.88;
    vec3 light = normalize(vec3(-3, 6, 4));
    float shadow = shadowVisibility(n);

    vec3 c = brdf(n, v, light, vec3(4.6, 4.3, 4.0), albedo, roughness, metal) * shadow;
    c += brdf(n, v, normalize(vec3(4, 2, -3)), vec3(0.65, 1.35, 2.3), albedo, roughness, metal);
    c += brdf(n, v, normalize(vec3(0, 6, -1)), vec3(1.1, 1.2, 1.4), albedo, roughness, metal);

    vec3 f0 = mix(vec3(0.04), albedo, metal);
    float nv = max(dot(n, v), 0.0);
    vec3 fresnel = f0 + (max(vec3(1.0 - roughness), f0) - f0) * pow(1.0 - nv, 5.0);
    c += studio(reflect(-v, n), roughness) * fresnel * 0.75;
    c += albedo * vec3(0.22, 0.26, 0.33) * (1.0 - metal * 0.7) * (0.55 + 0.45 * max(n.y, 0.0));

    float fog = 1.0 - exp(-0.012 * max(length(eye - worldPosition) - 8.0, 0.0));
    c = mix(c, vec3(0.008, 0.011, 0.018), fog);

    fragColor = vec4(c, 1.0);
}
