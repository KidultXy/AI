import cv2
import numpy as np
from handDetect import HandDetector
import time
import autopy
import pyautogui
import win32gui, win32process, psutil
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# 接收手部检测方法
#detector = HandDetector(mode=False,  # 视频流图像
#                        maxHands=1,  # 最多检测一只手
#                        detectionCon=0.8,  # 最小检测置信度
#                        minTrackCon=0.5)  # 最小跟踪置信度

def videoControl(detector, flag=True):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volumeRange = volume.GetVolumeRange()  # (-63.5, 0.0, 0.03125)
    minVol = volumeRange[0]
    maxVol = volumeRange[1]

    # 导入视频数据
    wScr, hScr = autopy.screen.size()  # 返回电脑屏幕的宽和高(1920.0, 1080.0)
    wCam, hCam = 1280, 720  # 视频显示窗口的宽和高
    pt1, pt2 = (0, 0), (1280, 720)  # 虚拟鼠标的移动范围，左上坐标pt1，右下坐标pt2

    cap = cv2.VideoCapture(0)  # 0代表自己电脑的摄像头
    cap.set(3, wCam)  # 设置显示框的宽度1280
    cap.set(4, hCam)  # 设置显示框的高度720

    pTime = 0  # 设置第一帧开始处理的起始时间
    pLocx, pLocy = 0, 0  # 上一帧时的鼠标所在位置
    smooth = 5  # 自定义平滑系数，让鼠标移动平缓一些
    frame = 0  # 初始化累计帧数
    prev_state = [1, 1, 1, 1, 1]  # 初始化上一帧状态
    current_state = [1, 1, 1, 1, 1]  # 初始化当前正状态

    while flag:
        # 图片是否成功接收、img帧图像
        success, img = cap.read()
        # 翻转图像，使自身和摄像头中的自己呈镜像关系
        img = cv2.flip(img, flipCode=1)  # 1代表水平翻转，0代表竖直翻转
        # 在图像窗口上创建一个矩形框，在该区域内移动鼠标
        cv2.rectangle(img, pt1, pt2, (0, 255, 255), 5)
        # 判断当前的活动窗口的进程名字
        try:
            pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
            print("pid:", pid)
            active_window_process_name = psutil.Process(pid[-1]).name()
            print("acitiveprocess:", active_window_process_name)
        except:
            pass
        # 手部关键点检测
        # 传入每帧图像, 返回手部关键点的坐标信息(字典)，绘制关键点后的图像
        hands, img = detector.findHands(img, flipType=False, draw=True)  # 上面反转过了，这里就不用再翻转了
        print("hands:", hands)

        # 如果能检测到手那么就进行下一步
        if hands:
            # 获取手部信息hands中的21个关键点信息
            lmList = hands[0]['lmList']  # hands是由N个字典组成的列表，字典包括每只手的关键点信息,此处代表第0个手
            # 获取食指指尖坐标，和中指指尖坐标
            x1, y1, z1 = lmList[8]  # 食指尖的关键点索引号为8
            # 检查哪个手指是朝上的
            fingers = detector.fingersUp(hands[0])  # 传入
            print("fingers", fingers)  # 返回 [0,1,1,0,0] 代表 只有食指和中指竖起
            # 确定鼠标移动的范围
            # 将食指指尖的移动范围从预制的窗口范围，映射到电脑屏幕范围
            x3 = np.interp(x1, (pt1[0], pt2[0]), (0, wScr))
            y3 = np.interp(y1, (pt1[1], pt2[1]), (0, hScr))
            # 平滑，使手指在移动鼠标时，鼠标箭头不会一直晃动
            cLocx = pLocx + (x3 - pLocx) / smooth  # 当前的鼠标所在位置坐标
            cLocy = pLocy + (y3 - pLocy) / smooth
            # 记录当前手势状态
            current_state = fingers
            # 记录相同状态的帧数
            if (prev_state == current_state):
                frame = frame + 1
            else:
                frame = 0
            prev_state = current_state

            # 只有食指竖起，就认为是移动鼠标
            if fingers == [0, 1, 0, 0, 0] and frame >= 1:
                cv2.putText(img, "Move", (150, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
                autopy.mouse.move(cLocx, cLocy)  # 给出鼠标移动位置坐标
                print("移动鼠标")
                # 更新前一帧的鼠标所在位置坐标，将当前帧鼠标所在位置，变成下一帧的鼠标前一帧所在位置
                pLocx, pLocy = cLocx, cLocy

            # 握拳
            elif fingers == [0, 0, 0, 0, 0] and frame >= 5:
                # 视频暂停/继续
                if (active_window_process_name == "QQLive.exe"):
                    cv2.putText(img, "Space", (150, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                    print("#############################################")
                    pyautogui.press('space')
                    print("暂停")
                    time.sleep(0.5)
                # 食指放下，左击
                else:
                    cv2.putText(img, "Left Click", (150, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                    cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
                    autopy.mouse.click(button=autopy.mouse.Button.LEFT, delay=0)
                    print("左击鼠标")
                    time.sleep(0.5)  # 防止重复点击

            # 比耶，右击（在移动的基础上竖起中指）
            elif fingers == [0, 1, 1, 0, 0] and frame >= 2:
                cv2.putText(img, "Right Click", (150, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                autopy.mouse.click(button=autopy.mouse.Button.RIGHT, delay=0)
                print("右击鼠标")
                time.sleep(0.5)  # 防止重复点击

            # 五指张开，全屏
            elif fingers == [1, 1, 1, 1, 1] and frame >= 2:
                if (active_window_process_name == "QQLive.exe"):
                    cv2.putText(img, "Full Screen", (150, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                    print("#############################################")
                    pyautogui.hotkey('alt', 'f')
                    print("全屏")
                    time.sleep(0.5)

            # 手比四，取消全屏
            elif fingers == [0, 1, 1, 1, 1] and frame >= 2:
                if (active_window_process_name == "QQLive.exe"):
                    cv2.putText(img, "Esc", (150, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                    print("#############################################")
                    pyautogui.press('esc')
                    print("取消全屏")

            # 伸大拇指，后退
            elif fingers == [1, 0, 0, 0, 0] and frame >= 2:
                if (active_window_process_name == "QQLive.exe"):
                    cv2.putText(img, "Back", (150, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                    print("#############################################")
                    pyautogui.press('left')
                    print("后退")
                    time.sleep(0.5)

            # 申小拇指，快进
            elif fingers == [0, 0, 0, 0, 1] and frame >= 2:
                if (active_window_process_name == "QQLive.exe"):
                    cv2.putText(img, "Accelerate", (150, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                    print("#############################################")
                    pyautogui.press('right')
                    print("快进")
                    time.sleep(0.5)

            # 比六，下一集
            elif fingers == [1, 0, 0, 0, 1] and frame >= 5:
                if (active_window_process_name == "QQLive.exe"):
                    cv2.putText(img, "Next", (150, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                    print("#############################################")
                    pyautogui.hotkey('alt', 'right')
                    print("下一集")

            # ok手势，进行调整音量
            elif fingers == [1, 0, 1, 1, 1] and frame >= 5:
                autopy.mouse.move(cLocx, cLocy)  # 给出鼠标移动位置坐标
                length = cLocx - pLocx
                pLocx = cLocx
                pLocy = cLocy
                print("移动的length:", length)
                print("移动鼠标调整音量")
                currentVolumeLv = volume.GetMasterVolumeLevelScalar()
                print("currentVolume:", currentVolumeLv)
                currentVolumeLv += length / 50.0
                if currentVolumeLv > 1.0:
                    currentVolumeLv = 1.0
                elif currentVolumeLv < 0.0:
                    currentVolumeLv = 0.0
                volume.SetMasterVolumeLevelScalar(currentVolumeLv, None)
                setVolume = volume.GetMasterVolumeLevelScalar()
                volPer = setVolume
                volBar = 350 - int((volPer) * 200)
                cv2.rectangle(img, (20, 150), (50, 350), (255, 0, 255), 2)
                cv2.rectangle(img, (20, int(volBar)), (50, 350), (255, 0, 255), cv2.FILLED)
                cv2.putText(img, f'{int(volPer * 100)}%', (10, 380), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)

        # 查看FPS
        cTime = time.time()  # 处理完一帧图像的时间
        fps = 1 / (cTime - pTime)
        pTime = cTime  # 重置起始时·
        print(fps)
        # 在视频上显示fps信息，先转换成整数再变成字符串形式，文本显示坐标，文本字体，文本大小
        cv2.putText(img, str(int(fps)), (70, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

        # 显示图像，输入窗口名及图像数据
        cv2.imshow('frame', img)
        if cv2.waitKey(1) & 0xFF == 27:  # 每帧滞留20毫秒后消失，ESC键退出
            break

    # 释放视频资源
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    videoControl()