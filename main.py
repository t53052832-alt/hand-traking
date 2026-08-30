import glfw
import numpy as np
import cv2
import buttons
import renderer
import hand_tracker

WIDTH, HEIGHT= 1280, 720
all_effect_names = ["thermal","distort","sobel","invert"]
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

app_renderer = renderer.Renderer(WIDTH,HEIGHT,'main',all_effect_names)
hand =  hand_tracker.HandTracker(WIDTH,HEIGHT,all_effect_names)
while not glfw.window_should_close(app_renderer.window):

    succsess,raw_frame = cap.read()    
    ai_frame = cv2.cvtColor(cv2.flip(raw_frame,1),cv2.COLOR_BGR2RGB)       
    gpu_frame = cv2.flip(ai_frame, 0)

    hud_canvas = np.zeros((HEIGHT,WIDTH, 4), dtype=np.uint8)
    hand.track_and_draw(ai_frame,hud_canvas)

    hud_canvas = cv2.flip(hud_canvas,0)

    app_renderer.render(gpu_frame,hud_canvas,hand.current_poly_points,hand.current_effect)
    #app_renderer.draw_stacked_poly(hand.current_poly_points,["thermal","invert"])

    app_renderer.update_screen()

    if glfw.get_key(app_renderer.window, glfw.KEY_ESCAPE) == glfw.PRESS:
        glfw.set_window_should_close(app_renderer.window, True)

cap.release()
glfw.terminate()


