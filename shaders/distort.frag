#version 330
in vec2 uv;
out vec4 f_color;

uniform sampler2D bg_tex;
uniform float time;

void main() {
    vec2 offset = vec2(sin(uv.y * 20.0 + 2*time) * 0.01, 
                        cos(uv.x * 20.0 + 2*time) * 0.01);
    vec4 distorted = texture(bg_tex, uv + offset);
    f_color = distorted;
}
