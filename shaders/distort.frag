#version 330
in vec2 uv;
out vec4 f_color;

uniform sampler2D bg_tex;

void main() {
    vec2 offset = vec2(sin(uv.y * 1.0) * 0.02,
                        cos(uv.x * 1.0) * 0.1);
    vec4 distorted = texture(bg_tex, uv + offset);
    f_color = distorted;
}
