#version 330
in vec3 inPosition;
in vec3 inNormal;
in vec4 model0;
in vec4 model1;
in vec4 model2;
in vec4 model3;
in vec4 material;
uniform mat4 viewProjection;
uniform mat4 lightProjection;
out vec3 worldPosition;
out vec3 worldNormal;
out vec4 surface;
out vec4 shadowPosition;
void main() {
    mat4 model = mat4(model0, model1, model2, model3);
    vec4 world = model * vec4(inPosition, 1.0);
    worldPosition = world.xyz;
    worldNormal = normalize(transpose(inverse(mat3(model))) * inNormal);
    surface = material;
    shadowPosition = lightProjection * world;
    gl_Position = viewProjection * world;
}
