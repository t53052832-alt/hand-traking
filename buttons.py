import cv2
import numpy as np

class Button:
    WIDTH = 140
    HEIGHT = 50
    GAP = 50

    def __init__(self, index: int, label: str, frame_w: int,states_n: int):
        self.x1 = frame_w - self.WIDTH - 10
        self.y1 = 10 + index * (self.HEIGHT + self.GAP)
        self.x2 = self.x1 + self.WIDTH
        self.y2 = self.y1 + self.HEIGHT
        self.label = label
        
        self.num_states = states_n        
        self.state_index = 0
        self.color_options = [(255,0,0,255),(0,255,0,255),(0,0,255,255)] #R G B

        if self.num_states < 3:
            self.is_active = False
        else:
            self.current_color = self.color_options[self.state_index]
    
        self.was_hovering = False

        # Pre-calculate text position ONCE during initialization to save CPU cycles on every frame
        (tw, th), _ = cv2.getTextSize(self.label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        self.tx = self.x1 + (self.WIDTH - tw) // 2
        self.ty = self.y1 + (self.HEIGHT + th) // 2

    @property
    def color(self) -> np.ndarray: 
        if self.num_states < 3:
            if self.is_active :
                return self.color_options[1]
            else:
                return self.color_options[0]
        else:
            return self.color_options[self.state_index]

    def toggle_state(self):
        self.is_active = not self.is_active

    def next_state(self):
        self.state_index += 1
        if self.state_index >= self.num_states:
            self.state_index = 0
        self.current_color = self.color_options[self.state_index]

    def draw(self, canvas):
        # Uses the dynamic @property self.color
        cv2.rectangle(canvas, (self.x1, self.y1), (self.x2, self.y2),self.color, cv2.FILLED)
        cv2.putText(canvas, self.label, (self.tx, self.ty), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255, 255), 2)

    def check_hover(self, cx: int, cy: int):
        # Fast bounding box check
        is_hovering = self.x1 < cx < self.x2 and self.y1 < cy < self.y2
        
        if is_hovering and not self.was_hovering:
            if self.num_states == 2:
                self.toggle_state()
            else:
                self.next_state()
            
        self.was_hovering = is_hovering