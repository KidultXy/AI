import cv2
import numpy as np
from handDetect import HandDetector
import os
import time
import autopy

# 接收手部检测方法
#detector = HandDetector(mode=False,  # 视频流图像
#                        maxHands=1,  # 最多检测一只手
#                        detectionCon=0.8,  # 最小检测置信度
#                        minTrackCon=0.5)  # 最小跟踪置信度

def painter(detector, flag=True):
    folderPath = "Pictures/"
    mylist = os.listdir(folderPath)
    overlayList = []
    for imPath in mylist:
        image = cv2.imread(f'{folderPath}/{imPath}')
        overlayList.append(image)
    header = overlayList[0]
    color = [0, 0, 255]
    brushThickness = 15
    eraserThickness = 40
    minthickness = 5
    maxthickness = 100

    wScr, hScr = autopy.screen.size()
    wCam, hCam = 1280, 720  # 视频显示窗口的宽和高
    wPic, hPic = 1280, 130  # 图片大小
    pt1, pt2 = (0, 0), (1280, 720)  # 虚拟鼠标的移动范围，左上坐标pt1，右下坐标pt2

    cap = cv2.VideoCapture(0)  # 若使用笔记本自带摄像头则编号为0  若使用外接摄像头 则更改为1或其他编号
    cap.set(3, wCam)  # 设置显示框的宽度1280
    cap.set(4, hCam)  # 设置显示框的高度720

    xp, yp = 0, 0
    imgCanvas = np.zeros((hCam, wCam, 3), np.uint8)  # 新建一个画板

    pTime = 0  # 设置第一帧开始处理的起始时间
    frame = 0  # 初始化累计帧数
    prev_state = [1, 1, 1, 1, 1]  # 初始化上一帧状态
    current_state = [1, 1, 1, 1, 1]  # 初始化当前正状态
    screenshot = 0
    picnum = 0

    # 处理每一帧图像
    while flag:
        # 图片是否成功接收、img帧图像
        success, img = cap.read()
        # 翻转图像，使自身和摄像头中的自己呈镜像关系
        img = cv2.flip(img, flipCode=1)  # 1代表水平翻转，0代表竖直翻转
        # 手部关键点检测
        # 传入每帧图像, 返回手部关键点的坐标信息(字典)，绘制关键点后的图像
        hands, img = detector.findHands(img, flipType=False, draw=True)  # 上面反转过了，这里就不用再翻转了
        # 如果能检测到手那么就进行下一步
        if hands:
            # 获取手部信息hands中的21个关键点信息
            lmList = hands[0]['lmList']  # hands是由N个字典组成的列表，字典包括每只手的关键点信息,此处代表第0个手
            hand_center = hands[0]['center']
            drag_flag = 0
            # 获取食指指尖坐标，和中指指尖坐标
            x1, y1, z1 = lmList[8]  # 食指尖的关键点索引号为8
            x2, y2, z2 = lmList[4]  # 大拇指指尖索引4
            cx, cy, cz = (x1 + x2) // 2, (y1 + y2) // 2, (z1 + z2) // 2  # 计算两指之间的中点坐标
            hand_cx, hand_cy = hand_center[0], hand_center[1]
            # （5）检查哪个手指是朝上的
            fingers = detector.fingersUp(hands[0])  # 传入
            # 计算食指尖和中指尖之间的距离distance,绘制好了的图像img,指尖连线的信息info
            distance, info, img = detector.findDistance((x1, y1), (x2, y2), img)  # 会画圈
            print("fingers", fingers)  # 返回 [0,1,1,0,0] 代表 只有食指和中指竖起
            # 记录当前手势状态
            current_state = fingers
            # 记录相同状态的帧数
            if (prev_state == current_state):
                frame = frame + 1
            else:
                frame = 0
            prev_state = current_state

            # 食指和中指竖起，切换笔刷
            if fingers == [0, 1, 1, 0, 0] and frame >= 2:
                cv2.putText(img, "Change Brush", (150, hCam - 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                if y1 < hPic:
                    if 0 < x1 < 280:
                        header = overlayList[0]
                        color = [0, 0, 255]
                    elif 280 < x1 < 530:
                        header = overlayList[1]
                        color = [255, 0, 0]
                    elif 530 < x1 < 780:
                        header = overlayList[2]
                        color = [0, 255, 0]
                    elif 1000 < x1 < 1280:
                        header = overlayList[3]
                        color = [0, 0, 0]
            img[0:wPic][0:hPic] = header

            # 中指弯下食指在上，右击鼠标
            if fingers == [0, 1, 0, 0, 0] and frame >= 2:
                if xp == 0 and yp == 0:
                    xp, yp = x1, y1

                if color == [0, 0, 0]:
                    cv2.putText(img, "Erase", (150, hCam - 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                    cv2.circle(img, (x1, y1), eraserThickness, color, cv2.FILLED)
                    cv2.line(img, (xp, yp), (x1, y1), color, eraserThickness)
                    cv2.line(imgCanvas, (xp, yp), (x1, y1), color, eraserThickness)
                else:
                    cv2.putText(img, "Draw", (150, hCam - 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                    cv2.circle(img, (x1, y1), brushThickness, color, cv2.FILLED)
                    cv2.line(img, (xp, yp), (x1, y1), color, brushThickness)
                    cv2.line(imgCanvas, (xp, yp), (x1, y1), color, brushThickness)

            xp, yp = x1, y1

            if fingers == [1, 1, 1, 1, 1]:
                cv2.putText(img, "Clear", (150, hCam - 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                imgCanvas = np.zeros((hCam, wCam, 3), np.uint8)

            if fingers == [1, 1, 0, 0, 0] and frame >= 10:  # frame设大一点，防止画图的时候也在调节粗细
                cv2.putText(img, "Change Thickness", (150, hCam - 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                print("Change Thickness")

                # 长度到粗细的转换
                thickness = np.interp(distance, [15, 200], [minthickness, maxthickness])

                if color == [0, 0, 0]:
                    eraserThickness = int(thickness)
                else:
                    brushThickness = int(thickness)

                thickBar = np.interp(distance, [15, 200], [350, 150])
                thickPer = np.interp(distance, [15, 200], [0, 100])

                cv2.rectangle(img, (20, 150), (50, 350), (255, 0, 255), 2)
                cv2.rectangle(img, (20, int(thickBar)), (50, 350), (255, 0, 255), cv2.FILLED)
                cv2.putText(img, f'{int(thickPer)}%', (10, 380), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)

            if fingers == [1, 0, 1, 1, 1] and frame >= 5:
                cv2.putText(img, "Screenshot", (150, hCam - 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                cv2.circle(img, (x1, y1), 15, color, cv2.FILLED)
                print("Screenshot")
                screenshot = 1
                picnum += 1

        imgGray = cv2.cvtColor(imgCanvas, cv2.COLOR_BGR2GRAY)
        _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
        imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
        img = cv2.bitwise_and(img, imgInv)
        img = cv2.bitwise_or(img, imgCanvas)
        img[0:wPic][0:hPic] = header

        # 查看FPS
        cTime = time.time()  # 处理完一帧图像的时间
        fps = 1 / (cTime - pTime)
        pTime = cTime  # 重置起始时·
        print(fps)
        # 在视频上显示fps信息，先转换成整数再变成字符串形式，文本显示坐标，文本字体，文本大小
        cv2.putText(img, str(int(fps)), (70, hCam - 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

        # 显示图像，输入窗口名及图像数据
        cv2.imshow('Image', img)

        if (screenshot == 1):
            cv2.imwrite(f'Save/{picnum}.jpg', img)
            screenshot = 0
            time.sleep(0.5)  # 延时，防止多次截图

        if cv2.waitKey(1) & 0xFF == 27:  # 每帧滞留20毫秒后消失，ESC键退出
            break

    # 释放视频资源
    cap.release()
    cv2.destroyAllWindows()
