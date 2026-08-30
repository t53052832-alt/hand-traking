import glfw
import moderngl
import numpy as np
import sys

class  Renderer:
    if not glfw.init():
        print("glfw failed to initialize")
        sys.exit(1)

    def __init__(self,width,height,window_name):
        self.WIDTH = width
        self.HEIGHT = height

        # Ask for a modern OpenGL "core" context (version 3.3+)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)

        self.window = glfw.create_window(self.WIDTH, self.HEIGHT, window_name ,None, None)
                
        if not self.window:
            glfw.terminate()
            print("glfw failed to create window")
            sys.exit(1)

        glfw.make_context_current(self.window)  # "this window is now the active drawing surface"
        self.ctx  = moderngl.create_context()
        #      x,     y,     u,   v
        quad = np.array([
            -1.0, -1.0,     0.0, 0.0,   # bottom-left
            1.0, -1.0,     1.0, 0.0,   # bottom-right
            -1.0,  1.0,     0.0, 1.0,   # top-left
            1.0,  1.0,     1.0, 1.0,   # top-right
        ], dtype='f4')

        vbo = self.ctx.buffer(quad.tobytes())  # upload this array into GPU memory

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

        void main() {
            // Read all 4 channels (Red, Green, Blue, Alpha) from the texture
            vec4 tex_color = texture(bg_tex, uv);
            
            // Output that exact color to the screen
            f_color = tex_color;
        }
        """

        self.program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)

        self.vao = self.ctx.vertex_array(self.program, [(vbo, '2f 2f', 'in_pos', 'in_uv')])

        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        self.bg_texture = self.ctx.texture((self.WIDTH, self.HEIGHT), 3)
        self.hud_texture = self.ctx.texture((self.WIDTH, self.HEIGHT), 4)

    def render(self,camara_frame,hud_canvas):
        self.bg_texture.write(camara_frame.tobytes())
        self.hud_texture.write(hud_canvas.tobytes())

        self.bg_texture.use(location=0)    
        self.program['bg_tex'].value = 0
        self.vao.render(moderngl.TRIANGLE_STRIP)
        
        self.hud_texture.use(location=0)
        self.program['bg_tex'].value = 0  # We use the exact same shader variable!
        self.vao.render(moderngl.TRIANGLE_STRIP)

        glfw.swap_buffers(self.window)  # show what we just drew
        glfw.poll_events()         # check for keyboard/mouse/close events

