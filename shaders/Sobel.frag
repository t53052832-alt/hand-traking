#version 330
in vec2 uv;
out vec4 f_color;

uniform sampler2D bg_tex;
uniform vec2 tex_resolution;   // e.g. (WIDTH, HEIGHT) — set from Python

void main() {
    mat3 sobelX = mat3(-1.0, -2.0, -1.0,
                         0.0,  0.0,  0.0,
                         1.0,  2.0,  1.0);
    mat3 sobelY = mat3(-1.0,  0.0,  1.0,
                        -2.0,  0.0,  2.0,
                        -1.0,  0.0,  1.0);

    float sumX = 0.0;
    float sumY = 0.0;

    for (int i = -1; i <= 1; i++) {
        for (int j = -1; j <= 1; j++) {
            vec2 offset = vec2(float(i), float(j)) / tex_resolution;
            float lum = length(texture(bg_tex, uv + offset).xyz);
            sumX += lum * sobelX[1 + i][1 + j];
            sumY += lum * sobelY[1 + i][1 + j];
        }
    }

    float g = abs(sumX) + abs(sumY);
    vec3 col = (g > 1.0) ? vec3(1.0) : vec3(0.0);
    f_color = vec4(col, 1.0);
}