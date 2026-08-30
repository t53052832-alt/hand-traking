import mediapipe as mp
import cv2
import time
import buttons
import FingerConnection
from OneEuroFilter import OneEuroFilter
import numpy as np
 

class HandTracker:

    def __init__(self, width, height,all_effect_names):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.all_effect_names = all_effect_names

        self.hands = self.mp_hands.Hands(
            max_num_hands = 2,
            min_detection_confidence = 0.1,
            min_tracking_confidence = 0.99,
        )

        dis = 40
        #----------normal----------
        self.more_buttons =     buttons.Button(0,"more buttons",(1280-dis),2)
        self.poly =             buttons.Button(1,"poly",(1280-dis),2)
        self.line_data =        buttons.Button(2,"line data",(1280-dis),2)
        self.cords =            buttons.Button(3,"cords",(1280-dis),2)
        self.points =           buttons.Button(2,"points",(1280-dis),2)

        dis = 180
        #----------more------------
        self.set_effect =       buttons.Button(1,"effect",(dis),len(all_effect_names))        
        self.set_color =        buttons.Button(0,"color",(dis),3)
        self.rectalgel =        buttons.Button(2,"rec",(dis),2)
        self.big_circel =       buttons.Button(3,"big circle",(dis),2)
        self.small_circel =     buttons.Button(4,"small circle",(dis),2)
        self.circel_on_finger = buttons.Button(5,"circle on finger",(dis),2)

        # ---- flip True/False here to turn buttons on/off, nothing else to touch ----
        normal_button_configs = [
            (self.more_buttons, True),
            (self.poly,         True),
            (self.line_data,    False),
            (self.cords,        False),
            (self.points,       True),
        ]

        multistate_button_configs = [
            (self.set_color,  False),
            (self.set_effect, True),
        ]

        double_state_button_configs = [
            (self.rectalgel,        True),
            (self.big_circel,       True),
            (self.small_circel,     True),
            (self.circel_on_finger, True),
        ]

        self.buttons_list = [btn for btn, enabled in normal_button_configs if enabled]
        self.more_buttons_list_multistates = [btn for btn, enabled in multistate_button_configs if enabled]
        self.more_buttons_list_doule_state = [btn for btn, enabled in double_state_button_configs if enabled]
        self.all_more_buttons = self.more_buttons_list_multistates + self.more_buttons_list_doule_state

        self.draw_buttons = True
        self.draw_only_multistates = True

        self.y_offset = 30
        self.num_of_hands = 0
        self.filter_is_on = False
        self.current_poly_points = None       

        self.points.is_active = not self.points.is_active
        self.poly.is_active = not self.poly.is_active
        
        self.show_main_hand = True

        self.WIDTH = width
        self.HEIGHT = height

        self.FINGER_IDS = {        
            "Thumb": 4,
            "Index": 8,
            "Middle": 12,
            "Ring": 16,
            "Pinky": 20,            
        }

        self.config = {
            'freq': 120,       # Expected data frequency in Hz
            'mincutoff': 1.0,  # Minimum cutoff frequency (low speed)
            'beta': 0.007,     # Speed coefficient (high speed lag reduction)
            'dcutoff': 1.0     # Cutoff frequency for the derivative
        }

        
        self.filters = {}
        self.filter_x = OneEuroFilter(**self.config)

        self.current_time = time.time()        

    def track_and_draw(self, frame, hud_canvas):        
        canvas = hud_canvas             

        self.current_poly_points = None            
        results = self.hands.process(frame)                   

        if self.draw_buttons:
            for btn in self.buttons_list:
                btn.draw(canvas)

            if self.more_buttons.is_active:
                if self.draw_only_multistates:
                    for btn in self.more_buttons_list_multistates:
                        btn.draw(canvas)    
                else:
                    for btn in self.all_more_buttons:
                        btn.draw(canvas)  

        if results.multi_hand_landmarks:
            num_of_hands = len(results.multi_hand_landmarks)
            all_hands_cords = []
            for self.hand_index, hand_landmarks in enumerate(results.multi_hand_landmarks):
                
                finger_cords = {}
                
                                    
                for name,id in self.FINGER_IDS.items():                    
                    lm = hand_landmarks.landmark[id]                        

                    if self.filter_is_on:
                        fx = self.get_filter(0, id, 'x')
                        fy = self.get_filter(0, id, 'y')

                        cx = int(fx.filter(lm.x * self.WIDTH, timestamp=self.current_time))
                        cy = int(fy.filter(lm.y * self.HEIGHT, timestamp=self.current_time))
                    else:
                        cx,cy = int(lm.x * self.WIDTH),int(lm.y * self.HEIGHT)
    
                    finger_cords[id] = (cx, cy)
                
                    if self.points.is_active:                            
                        cv2.circle(canvas, (cx, cy),10, (255, 0, 255,255), cv2.FILLED,1)

                    if self.hand_index == 0 and id == 8:  # index finger tip
                        if self.more_buttons.is_active:
                            for btn in self.buttons_list + self.all_more_buttons:
                                btn.check_hover(cx, cy)
                        else:
                            for btn in self.buttons_list:
                                btn.check_hover(cx, cy)
                                                                                            
                all_hands_cords.append(finger_cords)                                  
            
                if  self.more_buttons.is_active and any(b.is_active for b in self.more_buttons_list_doule_state):
                    self.extra_buttons(canvas,hand_landmarks,all_hands_cords)                                                  

                if self.cords.is_active:                        
                    self.show_cords(canvas,all_hands_cords)
            
                if self.poly.is_active and 0 > 1:                        
                    for i in range(num_of_hands):
                        if i < len(all_hands_cords):
                            line1 = FingerConnection.FingerConnection(0, i, 4, i, (0, 255, 0, 255), 2)   
                            line1.draw_connection(canvas,all_hands_cords, self.line_data.is_active)                                
               
            if num_of_hands == 2 and self.poly.is_active:                
                self.fill_poly([4,8],all_hands_cords)                      

    def get_filter(self,hand_idx, landmark_id, axis):
        key = (hand_idx, landmark_id, axis)
        if key not in self.filters:
            self.filters[key] = OneEuroFilter(**self.config)
        return self.filters[key]

    def extra_buttons(self,canvas,hand_landmarks, all_hands_cords):
        x_cords = [lm.x for lm in hand_landmarks.landmark]
        y_cords = [lm.y for lm in hand_landmarks.landmark]
        x_min, x_max = int(min(x_cords)*self.WIDTH), int(max(x_cords)*self.WIDTH)
        y_min, y_max = int(min(y_cords)*self.HEIGHT), int(max(y_cords)*self.HEIGHT)       
        x_diff, y_diff = abs(x_max - x_min), abs(y_max - y_min)
        x_center_of_hand, y_center_of_hand =  int(abs(x_max-x_min)/2)+x_min , int(abs(y_max - y_min)/2)+y_min                                   
        current_color = self.set_color.color_options[self.set_color.state_index]

        if self.show_main_hand and self.hand_index == 0:            
            cv2.circle(canvas, (x_center_of_hand, y_center_of_hand),10, (255, 255, 255,255), cv2.FILLED,1)            

        if self.rectalgel.is_active:                          
            cv2.rectangle(canvas, (x_min, y_min), (x_max, y_max),current_color,2)

        if self.big_circel.is_active:                                                                          
            big_r = int(max(x_diff, y_diff)/2)                            
            cv2.circle(canvas,(x_center_of_hand, y_center_of_hand),big_r,current_color,2)
                                    
        if self.small_circel.is_active:
            small_r = int(min(x_diff, y_diff)/2)
            cv2.circle(canvas,(x_center_of_hand, y_center_of_hand),small_r,current_color,2)

        if self.circel_on_finger.is_active:
            finger_id = 8                                                        
            distance_line_radios = FingerConnection.FingerConnection(finger_id,0,finger_id,1,current_color,2)
            distance = distance_line_radios.get_data(all_hands_cords)
            if distance != None:
                distance = int(distance)
                
                distance_line_radios.draw_connection(canvas,all_hands_cords,self.line_data.is_active)
                cv2.circle(canvas,all_hands_cords[0][finger_id],distance,current_color)

    def show_cords(self,canvas,all_hands_cords):
        x_offset = 200                    
        y_offset = 30
        for name, id in self.FINGER_IDS.items():                                                        
            cv2.putText(canvas, f'{name}: {all_hands_cords[0][id]}', (10, y_offset),cv2.FONT_HERSHEY_PLAIN, 1.1, (0, 0, 0, 255), 2)            
            if len(all_hands_cords) == 2:
                cv2.putText(canvas, f'{name}: {all_hands_cords[1][id]}', (x_offset+10, y_offset),cv2.FONT_HERSHEY_PLAIN, 1.1, (0, 0, 0, 255), 2)
            y_offset += 20     

    def fill_poly(self,fingers:list,all_hands_cords):
        if len(all_hands_cords) > 1:
            points = self.make_arr_for_n_fingers(fingers,all_hands_cords)

            for i in range(len(points)):
                points[i] = self.convert(points[i])

            self.current_poly_points = points
        else:
            self.current_poly_points = None

    def convert(self,pt):
        x = [2*(pt[0]/self.WIDTH)-1] 
        y = [1-(2*(pt[1]/self.HEIGHT))] 
        return [x,y]

    def make_arr_for_n_fingers(self,fingers,all_hands_cords):        
        points = []
        # 1. First hand (Hand 0) - Normal order
        for finger_id in fingers:
            points.append(all_hands_cords[0][finger_id])
            
        # 2. Second hand (Hand 1) - REVERSE order!
        # reversed(fingers) makes it read the list backwards.
        for finger_id in reversed(fingers):
            points.append(all_hands_cords[1][finger_id])
            
        return points

    @property
    def current_effect(self):
        return self.all_effect_names[self.set_effect.state_index]