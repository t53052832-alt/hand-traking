#version 330
in vec2 uv;
out vec4 f_color;

uniform sampler2D bg_tex;

void main() {
    vec4 tex_color = texture(bg_tex, uv);
    f_color = vec4(vec3(1.0) - tex_color.rgb, 1.0);
}
