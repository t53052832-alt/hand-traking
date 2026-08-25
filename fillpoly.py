import cv2
import math
import FingerConnection
import numpy as np

class fill_poly:
    def __init__(self,finger_id_1,finger_id_2,color:tuple):
        self.Finger_id_1 = finger_id_1
        self.Finger_id_2 = finger_id_2
        
        self.base_color = color

    def poly(self,img,all_hands_cords):
        if self.Finger_id_1 != self.Finger_id_2 and len(all_hands_cords) > 1:
            hand_1,hand_2 = all_hands_cords[0],all_hands_cords[1]            
            pt1,pt2,pt3,pt4 = hand_1[self.Finger_id_1],hand_1[self.Finger_id_2],hand_2[self.Finger_id_2],hand_2[self.Finger_id_1]  
            points = np.array([pt1, pt2, pt3, pt4],dtype=np.int32)
            cv2.fillPoly(img,pts=[points],color=self.base_color)
