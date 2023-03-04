import cv2
import mediapipe as mp
import math


class HandDetector:
    """
    利用mediapipe寻找手， 得到手部关键点坐标. 能够检测出多少只手指是伸张的
    以及两个手指指尖的距离 ，对检测到的手计算它的锚框.
    """

    def __init__(self, mode=False, maxHands=2, detectionCon=0.8, minTrackCon=0.5):
        """
        :param mode: 在静态模式会对没一张图片进行检测：比较慢
        :param maxHands: 检测到手的最大个数
        :param detectionCon: 最小检测阈值
        :param minTrackCon: 最小追踪阈值
        """
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.minTrackCon = minTrackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(static_image_mode=self.mode, max_num_hands=self.maxHands,
                                        min_detection_confidence=self.detectionCon,
                                        min_tracking_confidence=self.minTrackCon)
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]  # 从大拇指开始，依次为每个手指指尖
        self.fingers = []
        self.lmList = []

    def findHands(self, img, draw=True, flipType=True):
        """
        :param img: 需要检测的图片
        :param draw: 是否输出结果
        :return: 检测图片结果
        """
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        allHands = []
        h, w, c = img.shape
        print("self.results.multi_handedness")
        print(self.results.multi_handedness) #输出21个关键点信息

        if self.results.multi_hand_landmarks:
            for handType, handLms in zip(self.results.multi_handedness, self.results.multi_hand_landmarks):
                myHand = {}
                mylmList = []
                xList = []
                yList = []
                for id, lm in enumerate(handLms.landmark):
                    px, py, pz = int(lm.x * w), int(lm.y * h), int(lm.z * w)
                    mylmList.append([px, py, pz])
                    xList.append(px)
                    yList.append(py)

                xmin, xmax = min(xList), max(xList)  # 取最大数值
                ymin, ymax = min(yList), max(yList)
                boxW, boxH = xmax - xmin, ymax - ymin
                bbox = xmin, ymin, boxW, boxH
                cx, cy = bbox[0] + (bbox[2] // 2), \
                         bbox[1] + (bbox[3] // 2)

                myHand["lmList"] = mylmList
                myHand["bbox"] = bbox
                myHand["center"] = (cx, cy)

                if flipType:
                    if handType.classification[0].label == "Right":
                        myHand["type"] = "Left"
                    else:
                        myHand["type"] = "Right"
                else:
                    myHand["type"] = handType.classification[0].label
                allHands.append(myHand)

                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS)
                    cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20),
                                  (bbox[0] + bbox[2] + 20, bbox[1] + bbox[3] + 20),
                                  (255, 0, 255), 2)  #紫色
                    cv2.putText(img, myHand["type"], (bbox[0] - 30, bbox[1] - 30), cv2.FONT_HERSHEY_PLAIN,
                                2, (255, 0, 255), 2)
        if draw:
            return allHands, img
        else:
            return allHands

    def fingersUp(self, myHand):
        """
        识别多少手指的张合，返回坐标表，（多手识别的时候区分左右手）
        :return: 返回手指状态列表，例如[0,1,0,0,0]代表只有食指竖起
        """
        myHandType = myHand["type"]
        myLmList = myHand["lmList"]
        if self.results.multi_hand_landmarks:
            fingers = []
            # 拇指
            if myHandType == "Right":
                if myLmList[self.tipIds[0]][0] < myLmList[self.tipIds[0] - 1][0]:
                    fingers.append(1)
                else:
                    fingers.append(0)
            else:
                if myLmList[self.tipIds[0]][0] > myLmList[self.tipIds[0] - 1][0]:
                    fingers.append(1)
                else:
                    fingers.append(0)

            # 其余手指
            for id in range(1, 5):
                # 其他手指指尖的y坐标小于次指尖的点的坐标，则为竖直
                if myLmList[self.tipIds[id]][1] < myLmList[self.tipIds[id] - 2][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)
        return fingers

    def findDistance(self, p1, p2, img=None):
        """
        计算指尖距离
        :param p1: 手指1的位置
        :param p2: 手指2的位置
        :param img: 要绘制的图
        :return: 返回指尖距离，和绘制好的图
        """

        x1, y1 = p1
        x2, y2 = p2
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        length = math.hypot(x2 - x1, y2 - y1)
        info = (x1, y1, x2, y2, cx, cy)
        if img is not None:
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)   # 食指尖画紫圈
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)   # 中指尖画紫圈
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)   # 两指中间画紫圈
            return length, info, img
        else:
            return length, info


def main():
    cap = cv2.VideoCapture(0)
    detector = HandDetector(detectionCon=0.8, maxHands=2)
    while True:
        # 界面框
        success, img = cap.read()
        # 寻找手
        hands, img = detector.findHands(img)

        if hands:
            # 一只手
            hand1 = hands[0]
            lmList1 = hand1["lmList"]  # 21个关键点信息
            bbox1 = hand1["bbox"]
            centerPoint1 = hand1['center']  # 手心
            handType1 = hand1["type"]  # 左手or右手
            fingers1 = detector.fingersUp(hand1)

            if len(hands) == 2:
                # 两只手
                hand2 = hands[1]
                lmList2 = hand2["lmList"]  # 21个关键点信息
                bbox2 = hand2["bbox"]
                centerPoint2 = hand2['center']  # 手心
                handType2 = hand2["type"]  # 左手or右手
                fingers2 = detector.fingersUp(hand2)

                # 两只手的距离
                length, info, img = detector.findDistance(lmList1[8][0:2], lmList2[8][0:2], img)  # with draw
        # 展示
        cv2.imshow("Image", img)
        cv2.waitKey(1)


if __name__ == "__main__":
    main()