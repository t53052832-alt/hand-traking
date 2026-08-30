import mediapipe as mp
import cv2
import time
import buttons
import FingerConnection
from OneEuroFilter import OneEuroFilter
import fillpoly


class HandTracker:

    def __init__(self, width, height):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            max_num_hands = 2,
            min_detection_confidence = 0.7,
            min_tracking_confidence = 0.99,
        )

        dis = 40
        #----------normal----------
        self.more_buttons =     buttons.Button(0,"more buttons",(1280-dis),2)
        self.line =             buttons.Button(1,"line",(1280-dis),2)
        self.line_data =        buttons.Button(2,"line data",(1280-dis),2)
        self.cords =            buttons.Button(3,"cords",(1280-dis),2)
        self.points =           buttons.Button(4,"points",(1280-dis),2)
    
        dis = 180
        #----------more------------
        self.set_color =        buttons.Button(0,"color",(dis),3)
        self.rectalgel =        buttons.Button(1,"rec",(dis),2)
        self.big_circel =       buttons.Button(2,"big circle",(dis),2)
        self.small_circel =     buttons.Button(3,"small circle",(dis),2)
        self.circel_on_finger = buttons.Button(4,"circle on finger",(dis),2)

        self.buttons_list = [self.more_buttons, self.line, self.line_data, self.cords, self.points]
        self.more_buttons_list_multistates = [self.set_color]    
        self.more_buttons_list_doule_state = [self.rectalgel,self.big_circel,self.small_circel,self.circel_on_finger]
        self.all_more_buttons = self.more_buttons_list_multistates + self.more_buttons_list_doule_state

        self.y_offset = 30
        self.num_of_hands = 0
        self.filter_is_on = False
        self.points.is_active = not self.points.is_active

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
        canvas = cv2.flip(hud_canvas,0)                 
        rgba = cv2.cvtColor(canvas,cv2.COLOR_BGR2RGBA)
        results = self.hands.process(frame)                   

        for btn in self.buttons_list:
            btn.draw(canvas)

        if self.more_buttons.is_active:
            for btn in self.all_more_buttons:
                btn.draw(canvas)    

        if results.multi_hand_landmarks:
            num_of_hands = len(results.multi_hand_landmarks)
            all_hands_cords = []
            for hand_landmarks in results.multi_hand_landmarks:   
                
                finger_cords = {}
                
                                    
                for id in self.FINGER_IDS.items():
                    
                    lm = hand_landmarks.landmark[id]                        

                    if self.filter_is_on:
                        fx = self.get_filter(0, id, 'x')
                        fy = self.get_filter(0, id, 'y')

                        cx = int(fx.filter(lm.x * self.WIDTH, timestamp=self.current_time))
                        cy = int(fy.filter(lm.y * self.HEIGTH, timestamp=self.current_time))
                    else:
                        cx,cy = int(lm.x * self.WIDTH),int(lm.y * self.HEIGTH)
    
                    finger_cords[id] = (cx, cy)
                
                    if self.points.is_active:                            
                        cv2.circle(canvas, (cx, cy),10, (255, 0, 255,255), cv2.FILLED,1)

                    if id == 8:  # index finger tip
                        if self.more_buttons.is_active:
                            for btn in self.buttons_list + self.all_more_buttons:
                                btn.check_hover(cx, cy)
                        else:
                            for btn in self.buttons_list:
                                btn.check_hover(cx, cy)
                                                                                            
                all_hands_cords.append(finger_cords)                                  
            
                if  self.more_buttons.is_active and any(b.is_active for b in self.more_buttons_list_doule_state):
                    self.extra_buttons()                                                  

                if self.cords.is_active:                        
                    self.show_cords()
            
                if self.line.is_active and 0 > 1:                        
                    for i in range(num_of_hands):
                        if i < len(all_hands_cords):
                            line1 = FingerConnection.FingerConnection(0, i, 4, i, (0, 255, 0, 255), 2)   
                            line1.draw_connection(canvas,all_hands_cords, self.line_data.is_active)                                
                
            if num_of_hands == 2 and self.line.is_active:
                #for n ,i in FINGER_IDS.items():
                    #line1 = FingerConnection.FingerConnection(i,0,i,1,(0, 255, 0), 2)  
                    #line1.draw_connection(img,all_hands_cords,line_data.is_active)
                poly = fillpoly.fill_poly(8,4,(0,255,0,255))
                poly.poly(canvas,all_hands_cords)
        
        #cv2.imshow("image", canvas)                         
        

    def get_filter(self,hand_idx, landmark_id, axis):
        key = (hand_idx, landmark_id, axis)
        if key not in self.filters:
            self.filters[key] = OneEuroFilter(**self.config)
        return self.filters[key]

    def extra_buttons(self,canvas,hand_landmarks, all_hands_cords):
        x_cords = [lm.x for lm in hand_landmarks.landmark]
        y_cords = [lm.y for lm in hand_landmarks.landmark]
        x_min, x_max = int(min(x_cords)*self.WIDTH), int(max(x_cords)*self.WIDTH)
        y_min, y_max = int(min(y_cords)*self.HEIGTH), int(max(y_cords)*self.HEIGTH)       
        x_diff, y_diff = abs(x_max - x_min), abs(y_max - y_min)
        x_center_of_hand, y_center_of_hand =  int(abs(x_max-x_min)/2)+x_min , int(abs(y_max - y_min)/2)+y_min                                   
        current_color = self.set_color.color_options[self.set_color.state_index]

        if self.rectalgel.is_active:                          
            cv2.rectangle(canvas, (x_min, y_min), (x_max, y_max),current_color,2)

        if self.big_circel.is_active:                                                                          
            big_r = int(max(x_diff, y_diff)/2)                            
            cv2.circle(self.img,(x_center_of_hand, y_center_of_hand),big_r,current_color,2)
                                    
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

    def show_cords(self,canvas,hand_landmarks, all_hands_cords):
        x_offset = 200                    
        y_offset = 30
        for name, id in self.FINGER_IDS.items():                                                        
            cv2.putText(canvas, f'{name}: {all_hands_cords[0][id]}', (10, y_offset),cv2.FONT_HERSHEY_PLAIN, 1.1, (0, 0, 0, 255), 2)
            if len(all_hands_cords) == 2:
                cv2.putText(canvas, f'{name}: {all_hands_cords[1][id]}', (x_offset+10, y_offset),cv2.FONT_HERSHEY_PLAIN, 1.1, (0, 0, 0, 255), 2)
            y_offset += 20     
