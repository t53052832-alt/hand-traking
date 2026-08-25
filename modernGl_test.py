"""
Standalone moderngl + glfw demo.
Run this file BY ITSELF (not part of the hand-tracking project) to
understand how a GPU shader draws pixels, before we hook this into
main.py.

Run with:  python grid_shader_demo.py
Close the window, or press ESC, to quit.
"""

import glfw
import moderngl
import numpy as np
import sys
import cv2
import buttons

# ---------------------------------------------------------------
# STEP 1: Open a window and get an OpenGL context.
# glfw's ONLY job is: create an OS window, give us a place to draw,
# and tell us about keyboard/mouse/close events. It knows nothing
# about triangles, shaders, or colors - that part is moderngl's job.
# ---------------------------------------------------------------
if not glfw.init():
    print("glfw failed to initialize")
    sys.exit(1)

# Ask for a modern OpenGL "core" context (version 3.3+)
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)

WIDTH, HEIGHT = 1280, 720
window = glfw.create_window(WIDTH, HEIGHT, "Grid Shader Demo", None, None)
if not window:
    glfw.terminate()
    print("glfw failed to create window")
    sys.exit(1)

glfw.make_context_current(window)  # "this window is now the active drawing surface"

# ---------------------------------------------------------------
# STEP 2: Hand control to moderngl.
# ctx is your handle for everything GPU-related from now on:
# compiling shaders, uploading data, issuing draw calls.
# ---------------------------------------------------------------
ctx = moderngl.create_context()

# ---------------------------------------------------------------
# STEP 3: Define a "fullscreen quad" - two triangles that exactly
# cover the visible screen, so every pixel gets shaded.
#
# GL screen coordinates go from -1 to 1 on both axes (called
# "Normalized Device Coordinates" / NDC). (-1,-1) is bottom-left,
# (1,1) is top-right.
#
# Alongside each corner we ALSO store a UV coordinate (0..1). This
# is what the fragment shader actually uses to figure out "where am
# I inside the shape" for the grid pattern - it has nothing to do
# with screen position directly.
# ---------------------------------------------------------------
#      x,     y,     u,   v
quad = np.array([
    -1.0, -1.0,     0.0, 0.0,   # bottom-left
     1.0, -1.0,     1.0, 0.0,   # bottom-right
    -1.0,  1.0,     0.0, 1.0,   # top-left
     1.0,  1.0,     1.0, 1.0,   # top-right
], dtype='f4')

vbo = ctx.buffer(quad.tobytes())  # upload this array into GPU memory

# ---------------------------------------------------------------
# STEP 4: The shaders.
#
# VERTEX SHADER runs once PER CORNER (4 times, here). Its only job
# is "this corner belongs at this screen position", and it passes
# the UV coordinate onward for the fragment shader to use.
#
# FRAGMENT SHADER runs once PER PIXEL on screen (hundreds of
# thousands of times, every frame). This is where the grid pattern
# actually gets decided, pixel by pixel.
# ---------------------------------------------------------------
vertex_shader = """
#version 330
in vec2 in_pos;   // corner position, from our numpy array
in vec2 in_uv;    // corner UV, from our numpy array
out vec2 uv;      // passed onward to the fragment shader

void main() {
    uv = in_uv;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

fragment_shader = """
#version 330
in vec2 uv;
out vec4 f_color;

uniform sampler2D bg_tex;
uniform float grid_size;
uniform float line_width;

void main() {
    vec3 bg_color = texture(bg_tex, uv).rgb;

    vec2 scaled = uv * grid_size;
    vec2 cell_pos = fract(scaled);
    float near_left_or_bottom = 1.0 - step(line_width, cell_pos.x) * step(line_width, cell_pos.y);
    float near_right_or_top = step(1.0 - line_width, cell_pos.x) + step(1.0 - line_width, cell_pos.y);
    float on_line = clamp(near_left_or_bottom + near_right_or_top, 0.0, 1.0);

    vec3 line_color = vec3(0.0, 0.4, 1.0);
    vec3 result = mix(bg_color, line_color, on_line);
    f_color = vec4(result, 1.0);
}
"""

program = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)

# Tell moderngl how to read the numpy array: 2 floats = position,
# then 2 floats = uv, matching in_pos/in_uv in the vertex shader.
vao = ctx.vertex_array(program, [(vbo, '2f 2f', 'in_pos', 'in_uv')])

# Send values into the shader's "uniform" variables - constants that
# don't change per-vertex/per-pixel, but that you CAN update every
# frame from Python (useful later for animation).
program['grid_size'].value = 1.0
program['line_width'].value = 0.006

# ---------------------------------------------------------------
# STEP 5: Enable alpha blending.
# Without this, GL just overwrites pixels outright - alpha is
# ignored, and your "transparent" areas look solid black instead of
# letting whatever's behind them show through.
# ---------------------------------------------------------------
ctx.enable(moderngl.BLEND)
ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

# ---------------------------------------------------------------
# STEP 6: The render loop.
# Every frame: clear the screen to a background color (this stands
# in for where your camera frame will go later), draw the quad
# (which runs the fragment shader for every pixel), show it, and
# check for window events (like closing / ESC).
# ---------------------------------------------------------------

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

succsess,frame = cap.read()               
frame = cv2.flip(frame,0)
frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)       
#bg_texture = ctx.texture((WIDTH,HEIGHT),3,frame.tobytes())
hud_canvas = np.zeros((WIDTH,HEIGHT,4), dtype=np.uint8)

test_button = buttons.Button(0,"Test Button",WIDTH,2)



while not glfw.window_should_close(window):

    test_button.draw(hud_canvas)
    hud_texture.write(hud_canvas.tobytes())

    succsess,frame = cap.read()    
    frame = cv2.cvtColor(cv2.flip(frame,0),cv2.COLOR_BGR2RGB)       

    # Inside your loop: Create a completely blank (black & transparent) image
    hud_canvas = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)

    hud_canvas.write(frame.tobytes())
    
    hud_canvas.build_mipmaps()
    hud_canvas.use(location=0)    
    
    program['bg_tex'].value = 0

    vao.render(moderngl.TRIANGLE_STRIP)

    glfw.swap_buffers(window)  # show what we just drew
    glfw.poll_events()         # check for keyboard/mouse/close events

    if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
        glfw.set_window_should_close(window, True)

glfw.terminate()