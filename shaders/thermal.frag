#version 330
in vec2 uv;
out vec4 f_color;

uniform sampler2D bg_tex;

vec3 thermal_palette(float t) {
    vec3 c1 = vec3(1.0, 0.0, 1.0); // magenta
    vec3 c2 = vec3(0.0, 0.0, 1.0); // blue
    vec3 c3 = vec3(0.0, 1.0, 1.0); // cyan
    vec3 c4 = vec3(0.0, 1.0, 0.0); // green
    vec3 c5 = vec3(1.0, 1.0, 0.0); // yellow

    if (t < 0.25) return mix(c1, c2, t / 0.25);
    else if (t < 0.5) return mix(c2, c3, (t - 0.25) / 0.25);
    else if (t < 0.75) return mix(c3, c4, (t - 0.5) / 0.25);
    else return mix(c4, c5, (t - 0.75) / 0.25);
}

void main() {
    vec4 tex_color = texture(bg_tex, uv);
    float luminance = dot(tex_color.rgb, vec3(0.299, 0.587, 0.114));
    f_color = vec4(thermal_palette(luminance), 1.0);
}