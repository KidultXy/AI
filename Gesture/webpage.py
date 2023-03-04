#coding:utf-8

from flask import Flask, render_template
from handDetect import HandDetector
import control
import painter
import Read
import pythoncom

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'gestureControl'   #在各种加密过程中增加安全性
detector = HandDetector(mode=False,  # 视频流图像
                            maxHands=1,  # 最多检测一只手
                            detectionCon=0.8,  # 最小检测置信度
                            minTrackCon=0.5)  # 最小跟踪置信度

# 主页
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/control")
def webcontrol():
    pythoncom.CoInitialize()
    control.videoControl(detector)
    pythoncom.CoUninitialize()
    return render_template("home.html")

@app.route("/painter")
def webpainter():
    painter.painter(detector)
    return render_template("home.html")

@app.route("/Read")
def webRead():
    Read.read(detector)
    return render_template("home.html")

if __name__ == '__main__':
    app.run()


