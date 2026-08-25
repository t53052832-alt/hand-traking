import cv2
import mediapipe as mp
import time
import buttons
import FingerConnection
from OneEuroFilter import OneEuroFilter
import fillpoly
import moderngl as md


mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


config = {
    'freq': 120,       # Expected data frequency in Hz
    'mincutoff': 1.0,  # Minimum cutoff frequency (low speed)
    'beta': 0.007,     # Speed coefficient (high speed lag reduction)
    'dcutoff': 1.0     # Cutoff frequency for the derivative
}

filters = {}

def get_filter(hand_idx, landmark_id, axis):
    key = (hand_idx, landmark_id, axis)
    if key not in filters:
        filters[key] = OneEuroFilter(**config)
    return filters[key]

def main():
    current_time = time.time()

    dis = 40
    #----------normal----------
    more_buttons = buttons.Button(0,"more buttons",(1280-dis),2)
    line = buttons.Button(1,"line",(1280-dis),2)
    line_data = buttons.Button(2,"line data",(1280-dis),2)
    cords = buttons.Button(3,"cords",(1280-dis),2)
    points = buttons.Button(4,"points",(1280-dis),2)

    dis = 180
    #----------more------------
    set_color = buttons.Button(0,"color",(dis),3)
    rectalgel = buttons.Button(1,"rec",(dis),2)
    big_circel = buttons.Button(2,"big circle",(dis),2)
    small_circel = buttons.Button(3,"small circle",(dis),2)
    circel_on_finger = buttons.Button(4,"circle on finger",(dis),2)

    buttons_list = [more_buttons, line, line_data, cords, points]
    more_buttons_list_multistates = [set_color]    
    more_buttons_list_doule_state = [rectalgel,big_circel,small_circel,circel_on_finger]
    all_more_buttons = more_buttons_list_multistates + more_buttons_list_doule_state

    points.is_active = not points.is_active

    y_offset = 30
    num_of_hands = 0
    #menu_expanded = False
    filter_is_on = False

    

    FINGER_IDS = {        
        "Thumb": 4,
        "Index": 8,
        "Middle": 12,
        "Ring": 16,
        "Pinky": 20,            
    }    

    filter_x = OneEuroFilter(**config)    
    
    with mp_hands.Hands(
        max_num_hands = 2,
        min_detection_confidence = 0.7,
        min_tracking_confidence = 0.99,
    ) as hands:
        while True:
            attempts = 0
            success, img = cap.read()
            while not success and attempts < 5:
                time.sleep(0.2)
                success, img = cap.read()
                attempts += 1
                print("try number:",attempts)
            if not success:
                print("Failed to capture image after 5 attempts.")
                break

            img = cv2.flip(img, 1)
            h, w, _ = img.shape
            rgb = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)                   

            for btn in buttons_list:
                btn.draw(img)

            if more_buttons.is_active:
                for btn in all_more_buttons:
                    btn.draw(img)    

            if results.multi_hand_landmarks:
                num_of_hands = len(results.multi_hand_landmarks)
                all_hands_cords = []
                for hand_landmarks in results.multi_hand_landmarks:   
                    
                    finger_cords = {}
                    
                                        
                    for name, id in FINGER_IDS.items():
                        
                        lm = hand_landmarks.landmark[id]                        

                        if filter_is_on:
                            fx = get_filter(0, id, 'x')
                            fy = get_filter(0, id, 'y')

                            cx = int(fx.filter(lm.x * w, timestamp=current_time))
                            cy = int(fy.filter(lm.y * h, timestamp=current_time))
                        else:
                            cx,cy = int(lm.x * w),int(lm.y * h)

                                                        
                        finger_cords[id] = (cx, cy)
                    

                        if points.is_active:                            
                                cv2.circle(img, (cx, cy),10, (255, 0, 255), cv2.FILLED,1)
                        if id == 8:  # index finger tip
                            if more_buttons.is_active:
                                for btn in buttons_list + all_more_buttons:
                                    btn.check_hover(cx, cy)
                            else:
                                for btn in buttons_list:
                                    btn.check_hover(cx, cy)
                                                                                                
                    all_hands_cords.append(finger_cords)                                  
                    #(rectalgel.is_active or big_circel.is_active or small_circel.is_active or circel_on_finger.is_active):
                    if  more_buttons.is_active and any(b.is_active for b in more_buttons_list_doule_state):
                        x_cords = [lm.x for lm in hand_landmarks.landmark]
                        y_cords = [lm.y for lm in hand_landmarks.landmark]
                        x_min, x_max = int(min(x_cords)*w), int(max(x_cords)*w)
                        y_min, y_max = int(min(y_cords)*h), int(max(y_cords)*h)       
                        x_diff, y_diff = abs(x_max - x_min), abs(y_max - y_min)
                        x_center_of_hand, y_center_of_hand =  int(abs(x_max-x_min)/2)+x_min , int(abs(y_max - y_min)/2)+y_min                                   
                        current_color = set_color.color_options[set_color.state_index]

                        if rectalgel.is_active:                          
                            cv2.rectangle(img, (x_min, y_min), (x_max, y_max),current_color,2)

                        if big_circel.is_active:                                                                          
                            big_r = int(max(x_diff, y_diff)/2)                            
                            cv2.circle(img,(x_center_of_hand, y_center_of_hand),big_r,current_color,2)
                                                    
                        if small_circel.is_active:
                            small_r = int(min(x_diff, y_diff)/2)
                            cv2.circle(img,(x_center_of_hand, y_center_of_hand),small_r,current_color,2)

                        if circel_on_finger.is_active:
                            finger_id = 8                                                        
                            distance_line_radios = FingerConnection.FingerConnection(finger_id,0,finger_id,1,current_color,2)
                            distance = distance_line_radios.get_data(all_hands_cords)
                            if distance != None:
                                distance = int(distance)
                                
                                distance_line_radios.draw_connection(img,all_hands_cords,line_data.is_active)
                                cv2.circle(img,all_hands_cords[0][finger_id],distance,current_color)                        

                    if cords.is_active:                        
                        x_offset = 200                    
                        y_offset = 30
                        for name, id in FINGER_IDS.items():                                                        
                            cv2.putText(img, f'{name}: {all_hands_cords[0][id]}', (10, y_offset),cv2.FONT_HERSHEY_PLAIN, 1.1, (0, 0, 0), 2)
                            if len(all_hands_cords) == 2:
                                cv2.putText(img, f'{name}: {all_hands_cords[1][id]}', (x_offset+10, y_offset),cv2.FONT_HERSHEY_PLAIN, 1.1, (0, 0, 0), 2)
                            y_offset += 20
                
                    if line.is_active and 0 > 1:                        
                        for i in range(num_of_hands):
                            if i < len(all_hands_cords):
                                line1 = FingerConnection.FingerConnection(0, i, 4, i, (0, 255, 0), 2)   
                                line1.draw_connection(img,all_hands_cords, line_data.is_active)                                
                    
                if num_of_hands == 2 and line.is_active:
                    #for n ,i in FINGER_IDS.items():
                        #line1 = FingerConnection.FingerConnection(i,0,i,1,(0, 255, 0), 2)  
                        #line1.draw_connection(img,all_hands_cords,line_data.is_active)
                    poly = fillpoly.fill_poly(8,4,(0,255,0))
                    poly.poly(img,all_hands_cords)
            
            cv2.imshow("image", img)

            if cv2.waitKey(1) & 0xFF == ord('q'): 
                break

            if cv2.getWindowProperty("image", cv2.WND_PROP_VISIBLE) < 1:
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()