import glfw
import moderngl
import numpy as np
import sys

class  Renderer:
    if not glfw.init():
        print("glfw failed to initialize")
        sys.exit(1)

    def __init__(self, width, height, window_name):
        self.WIDTH = width
        self.HEIGHT = height

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)

        self.window = glfw.create_window(self.WIDTH, self.HEIGHT, window_name, None, None)
        if not self.window:
            glfw.terminate()
            print("glfw failed to create window")
            sys.exit(1)

        glfw.make_context_current(self.window)
        self.ctx = moderngl.create_context()

        quad = np.array([
            -1.0, -1.0,   0.0, 0.0,
            1.0, -1.0,   1.0, 0.0,
            -1.0,  1.0,   0.0, 1.0,
            1.0,  1.0,   1.0, 1.0,
        ], dtype='f4')
        vbo = self.ctx.buffer(quad.tobytes())

        # --- background full-frame shader (unchanged) ---
        vertex_shader = """
        #version 330
        in vec2 in_pos;
        in vec2 in_uv;
        out vec2 uv;
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
            f_color = texture(bg_tex, uv);
        }
        """
        self.program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        self.vao = self.ctx.vertex_array(self.program, [(vbo, '2f 2f', 'in_pos', 'in_uv')])

        # --- NEW: load every poly-effect shader from its own file ---
        with open("shaders/shape_vertex.glsl") as f:
            shape_vertex_src = f.read()

        self.poly_vbo = self.ctx.buffer(reserve=200)

        self.shape_programs = {}   # effect name -> compiled program
        self.shape_vaos = {}       # effect name -> its own VAO (all share poly_vbo)

        effect_names = ["thermal","distort","Sobel"]  # <-- just add a name here when you make a new .frag file
        for name in effect_names:
            with open(f"shaders/{name}.frag") as f:
                frag_src = f.read()
            program = self.ctx.program(vertex_shader=shape_vertex_src, fragment_shader=frag_src)
            vao = self.ctx.vertex_array(program, [(self.poly_vbo, '2f', 'in_pos')])
            self.shape_programs[name] = program
            self.shape_vaos[name] = vao

        if "sobel" in self.shape_programs:
            self.shape_programs["sobel"]["tex_resolution"].value = (self.WIDTH, self.HEIGHT)

        self.active_effect = "Sobel"  # whichever one is shown right now

        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        self.bg_texture = self.ctx.texture((self.WIDTH, self.HEIGHT), 3)
        self.hud_texture = self.ctx.texture((self.WIDTH, self.HEIGHT), 4)
        
    def render(self,camara_frame,hud_canvas,poly_points = None):
        self.bg_texture.write(camara_frame.tobytes())
        self.hud_texture.write(hud_canvas.tobytes())

        self.bg_texture.use(location=0)    
        self.program['bg_tex'].value = 0
        
        self.vao.render(moderngl.TRIANGLE_STRIP)

        
        if poly_points is not None and len(poly_points) > 0:
            self.draw_gpu_poly(poly_points,self.active_effect)
        
        self.hud_texture.use(location=0)
        self.program['bg_tex'].value = 0  # We use the exact same shader variable!
        self.vao.render(moderngl.TRIANGLE_STRIP)
       

    def draw_gpu_poly(self, points, effect_name=None):
        name = effect_name or self.active_effect
        program = self.shape_programs[name]
        vao = self.shape_vaos[name]

        np_points = np.array(points, dtype='f4')
        self.poly_vbo.write(np_points.tobytes())

        self.bg_texture.use(location=0)
        program['bg_tex'].value = 0

        vao.render(moderngl.TRIANGLE_FAN, vertices=len(points))

    def update_screen(self):
        glfw.swap_buffers(self.window)
        glfw.poll_events()

