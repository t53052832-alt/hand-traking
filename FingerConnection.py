import cv2
import math

class FingerConnection:
    def __init__(self, finger_id1: int, hand1: int, finger_id2: int, hand2: int, color: tuple, thickness: int):
        self.Finger1 = finger_id1
        self.Finger2 = finger_id2

        self.Hand1 = hand1
        self.Hand2 = hand2

        self.current_color = color  # Preserved original intended color
        self.thickness = thickness

    def draw_connection(self, img, all_hands: list, show_data: bool):
        # 1. Boundary check to prevent IndexError if a hand suddenly disappears
        if self.Hand1 >= len(all_hands) or self.Hand2 >= len(all_hands):
            return
            
        hand1_dict = all_hands[self.Hand1]
        hand2_dict = all_hands[self.Hand2]

        if self.Finger1 in hand1_dict and self.Finger2 in hand2_dict:
            # 2. Unpack coordinates ONCE to avoid heavy repeated dictionary hash lookups
            x1, y1 = hand1_dict[self.Finger1]
            x2, y2 = hand2_dict[self.Finger2]

            # 3. Compute deltas once for both distance and angle formulas
            dx = x2 - x1
            dy = y2 - y1
            
            distance = math.hypot(dx, dy)

            
            if distance > 30:
                # Use dynamic color instead of permanently overwriting instance state
                cv2.line(img, (x1, y1), (x2, y2), self.current_color, self.thickness)
            
                if show_data:
                    angle = math.degrees(math.atan2(dy, dx))

                    # 4. Math optimization: bitwise shift/integer division for center
                    center_line_x = x1 + (dx // 2)
                    center_line_y = y1 + (dy // 2)

                    cv2.putText(img, f"dist: {distance:.0f}", (center_line_x, center_line_y + 20),
                                cv2.FONT_HERSHEY_PLAIN, 1.1, (0, 0, 0), 2)
                    cv2.putText(img, f"angle: {angle:.0f} deg", (center_line_x, center_line_y - 20),
                                cv2.FONT_HERSHEY_PLAIN, 1.1, (0, 0, 0), 2)

    def get_data(self, all_hands: list):
        if self.Hand1 >= len(all_hands) or self.Hand2 >= len(all_hands):
            return

        hand1_dict = all_hands[self.Hand1]
        hand2_dict = all_hands[self.Hand2]

        if self.Finger1 in hand1_dict and self.Finger2 in hand2_dict:                    
            x1, y1 = hand1_dict[self.Finger1]
            x2, y2 = hand2_dict[self.Finger2]

            dx = x2 - x1
            dy = y2 - y1
            
            return math.hypot(dx, dy) # distance