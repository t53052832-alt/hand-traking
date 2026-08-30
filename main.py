import glfw
import numpy as np
import cv2
import buttons
import renderer
import hand_tracker

WIDTH, HEIGHT= 1280, 720

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

test_button = buttons.Button(0,"Test Button",WIDTH,2)

app_renderer = renderer.Renderer(WIDTH,HEIGHT,'main')
hand = hand_tracker.HandTracker(WIDTH,HEIGHT)
while not glfw.window_should_close(app_renderer.window):

    succsess,frame = cap.read()    
    frame = cv2.cvtColor(cv2.flip(frame,-1),cv2.COLOR_BGR2RGB)       

    hud_canvas = np.zeros((HEIGHT,WIDTH, 4), dtype=np.uint8)

    test_button.draw(hud_canvas)
    hud_canvas = cv2.flip(hud_canvas,0)

    hand.track_and_draw(frame,hud_canvas)
    app_renderer.render(frame,hud_canvas)
    
    if glfw.get_key(app_renderer.window, glfw.KEY_ESCAPE) == glfw.PRESS:
        glfw.set_window_should_close(app_renderer.window, True)

cap.release()
glfw.terminate()


