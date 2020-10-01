from time import sleep

from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtWidgets import *
from PyQt5.uic import *
import cv2
from PyQt5.Qt import QApplication, QUrl, QDesktopServices
import numpy as np
import sys
import pathlib
import object_detection

def alert(title, txt, type=QMessageBox.Critical):
    msg = QMessageBox()
    msg.setIcon(type)
    msg.setWindowTitle(title)
    msg.setText(txt)
    msg.exec_()

nw = ""
files = None
maskRanges = [[(0, 217, 80), (3, 255, 255)],
              [(168, 150, 0), (180, 255, 255)]]
refresh = True
videoFrame = None

class window(QMainWindow):
    logo = None

    def __init__(self):
        global maskRanges
        super(window, self).__init__()
        loadUi("main.ui", self)
        self.logo = cv2.imread("images/logo2.png")
        if self.logo is None:
            alert("Error", "Couldn't find watermark file")
        self.slider_h.setRange(0, 180)
        self.slider_s.setRange(0, 255)
        self.slider_v.setRange(0, 255)

        self.slider_h.setValue(maskRanges[0][0][0])
        self.slider_s.setValue(maskRanges[0][0][1])
        self.slider_v.setValue(maskRanges[0][0][2])

        self.cb_currentMask.currentIndexChanged.connect(self.limitsChanged)
        self.cb_maskCount.currentIndexChanged.connect(self.maskCountChanged)
        self.cb_maskCount.setCurrentIndex(1)
        for i in range(0, (self.cb_maskCount.count() - len(maskRanges))):
            maskRanges.append([(0, 0, 0), (0, 0, 0)])
        self.cb_limits.currentIndexChanged.connect(self.limitsChanged)
        self.slider_h.valueChanged.connect(self.sliderChange)
        self.slider_s.valueChanged.connect(self.sliderChange)
        self.slider_v.valueChanged.connect(self.sliderChange)

        self.lb_h.setText(str(maskRanges[0][0][0]))
        self.lb_s.setText(str(maskRanges[0][0][1]))
        self.lb_v.setText(str(maskRanges[0][0][2]))

        self.bt_object.clicked.connect(self.goToOD)
        self.bt_saveMasks.clicked.connect(self.saveMasks)
        self.bt_file.clicked.connect(self.showFileDialog)
        self.bt_images.clicked.connect(self.showImagesDialog)
        self.bt_colorPicker.clicked.connect(self.showColorPicker)
        self.cb_showMask.setChecked(True)

    def goToOD(self):
        global nw
        nw = object_detection.window()
        nw.show()
        self.hide()

    def saveMasks(self):
        global maskRanges
        maskCount = int(self.cb_maskCount.currentText())
        dialog = QFileDialog()
        file = str(dialog.getExistingDirectory(self, "Select Directory"))
        #if dialog.Accepted:
        text_file = open(str(file) + "/saved_masks.txt", "w")
        for i in range(0, maskCount):
            text_file.write(str(maskRanges[i]) + "\r\n")
        text_file.close()
        #alert("Success", "Successfully saved", QMessageBox.Information)

    def currentMaskChanged(self):
        print("")

    def maskCountChanged(self):
        global maskRanges
        maskCount = int(self.cb_maskCount.currentText())
        self.cb_currentMask.clear()
        for i in range(0, maskCount):
            self.cb_currentMask.addItem(str(i + 1), i)

    def showColorPicker(self):
        global files
        files = ['images/hsv1.png', 'images/hsv2.png']
        self.detectRedColor()

    """def hsvToImage(self):
        green = np.uint8([[[0, 255, 0]]])
        hsv_green = cv2.cvtColor(green, cv2.COLOR_BGR2HSV)
        print("HSV: " + str(hsv_green))
        #cv2.imwrite("images/hsv.png", hsv_green)"""

    def showFileDialog(self):
        file = QFileDialog.getOpenFileName(self, 'Choose a Video File',
                                           str(pathlib.Path().absolute()) + "/images",
                                           "Video files (*.mp4 *.h264 *.avi)")
        if file[0] != "":
            self.proccessVideo(str(file[0]))

    def showImagesDialog(self):
        global files, videoFrame
        videoFrame = None
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Choose Multiple Images",
                                                str(pathlib.Path().absolute()) + "/images",
                                                "Image Files (*.jpg *.png *.jpeg)", options=options)
        if files:
            self.detectRedColor()

    def putText(self, frame, text, x, y, found=0, speed=0, isLogo=1):
        font = cv2.FONT_HERSHEY_SIMPLEX
        h_img, w_img, _ = frame.shape
        coor = (x, y)
        fontScale = 1.5
        fontColor = (255, 255, 255)
        if found == 1:
            fontColor = (0, 0, 255)
        lineType = 2
        cv2.putText(frame, text,
                    coor,
                    font,
                    fontScale,
                    fontColor,
                    lineType)

        fontScale = 1
        fontColor = (214, 127, 12)
        if speed == 1:
            coor = (w_img - 115, h_img - 10)
            cv2.putText(frame, "25m/s",
                        coor,
                        font,
                        fontScale,
                        fontColor,
                        lineType)
        if isLogo == 1 and self.logo is not None:
            h_logo, w_logo, _ = self.logo.shape
            center_y = int(h_img / 2)
            center_x = int(w_img / 2)
            top_y = center_y - int(h_logo / 2)
            left_x = center_x - int(w_logo / 2)
            bottom_y = top_y + h_logo
            right_x = left_x + w_logo
            roi = frame[top_y: bottom_y, left_x: right_x]
            result = cv2.addWeighted(roi, 1, self.logo, 0.3, 0)
            frame[top_y: bottom_y, left_x: right_x] = result
        return frame

    def detectCircles(self, frame):
        global maskRanges
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, maskRanges[0][0], maskRanges[0][1])
        maskCount = int(self.cb_maskCount.currentText())
        for k in range(0, maskCount):
            mask += cv2.inRange(hsv, maskRanges[k][0], maskRanges[k][1])
        gau_blur = cv2.GaussianBlur(mask, (9, 9), 2, 2)  # 2, 100
        rows, cols = gau_blur.shape  # 1, (rows / 8), 200, 100)
        circles = cv2.HoughCircles(gau_blur, cv2.HOUGH_GRADIENT, 2, 100)
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                cv2.circle(frame, (x, y), r, (0, 255, 0), 4)
                cv2.rectangle(frame, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)
        cv2.imshow("circle", frame)

    def proccessVideo(self, path, type=0):
        global files, videoFrame
        try:
            cap = cv2.VideoCapture(path)
            success = True
            while success:
                success, frame = cap.read()
                key = cv2.waitKey(1) & 0xFF
                if key == ord('p'):
                    videoFrame = frame
                    cv2.waitKey(0)
                if type == 0:
                    files = ["random"]
                    self.detectRedColor(frame)
                elif type == 1:
                    self.detectCircles(frame)

                if key == ord('q'):
                    print("video kapandi")
                    videoFrame = None
                    break
            videoFrame = None
            print("bitti")
            cap.release()
            cv2.destroyAllWindows()
        except Exception as ex:
            #alert("Error", str(ex))
            print("")

    def limitsChanged(self):
        global refresh, maskRanges
        idx = self.cb_limits.currentIndex()
        cMIdx = self.cb_currentMask.currentIndex()
        lower_bound = maskRanges[cMIdx][0]
        upper_bound = maskRanges[cMIdx][1]
        refresh = False
        if idx == 0:
            self.slider_h.setValue(lower_bound[0])
            self.slider_s.setValue(lower_bound[1])
            self.slider_v.setValue(lower_bound[2])
            self.lb_h.setText(str(lower_bound[0]))
            self.lb_s.setText(str(lower_bound[1]))
            self.lb_v.setText(str(lower_bound[2]))
        elif idx == 1:
            self.slider_h.setValue(upper_bound[0])
            self.slider_s.setValue(upper_bound[1])
            self.slider_v.setValue(upper_bound[2])
            self.lb_h.setText(str(upper_bound[0]))
            self.lb_s.setText(str(upper_bound[1]))
            self.lb_v.setText(str(upper_bound[2]))
        refresh = True

    def sliderChange(self):
        global maskRanges, refresh, files, videoFrame
        if not refresh:
            return
        val_h = self.slider_h.value()
        val_s = self.slider_s.value()
        val_v = self.slider_v.value()
        idx = self.cb_limits.currentIndex()
        cMIdx = self.cb_currentMask.currentIndex()
        if idx == 0:
            maskRanges[cMIdx][0] = (val_h, val_s, val_v)
        else:
            maskRanges[cMIdx][1] = (val_h, val_s, val_v)

        #print(str(maskRanges))
        self.lb_h.setText(str(val_h))
        self.lb_s.setText(str(val_s))
        self.lb_v.setText(str(val_v))
        if files is not None and files[0] != "random":
            self.detectRedColor()
        elif videoFrame is not None:
            copy = videoFrame.copy()
            self.detectRedColor(copy)

    def calcPerc(self, total, current):
        return 100 * current / total

    def detectRedColor(self, is_video=None):
        global files, maskRanges
        for i, imgPath in enumerate(files):
            if is_video is not None:
                frame = is_video
            else:
                frame = cv2.imread(imgPath)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, maskRanges[0][0], maskRanges[0][1])
            maskCount = int(self.cb_maskCount.currentText())
            for k in range(0, maskCount):
                mask += cv2.inRange(hsv, maskRanges[k][0], maskRanges[k][1])
            rows, cols = mask.shape
            square = rows * cols
            perc = self.calcPerc(square, cv2.countNonZero(mask))
            redmask = cv2.bitwise_and(frame, frame, mask=mask)
            if is_video is not None:
                if self.cb_showMask.isChecked():
                    if perc >= 2:
                        self.stackAndShow(self.putText(frame, "%" + "{:.2f}".format(perc) + " match", 10, rows - 10, 1),
                                          redmask, "Press P to pause video")
                        sleep(0.06)
                    else:
                        self.stackAndShow(self.putText(frame, "%" + "{:.2f}".format(perc) + " match", 10, rows - 10, 0),
                                          redmask, "Press P to pause video")
                else:
                    cv2.imshow("Press P to pause video",
                               self.putText(frame, "%" + "{:.2f}".format(perc) + " match", 10, rows - 10, 1))
                return
            if self.cb_showMask.isChecked():
                self.stackAndShow(frame, redmask, "Image_" + str(i))
            else:
                cv2.imshow("Image_" + str(i),
                           self.putText(frame, "%" + "{:.2f}".format(perc) + " match", 10, rows - 10, 1, 0, 0))

    def stackAndShow(self, frame, mask, name):
        h, w, _ = frame.shape
        if w * 2 >= 1920:
            frame = cv2.resize(frame, (0, 0), None, .75, .75)
            mask = cv2.resize(mask, (0, 0), None, .75, .75)
        img_concat = np.concatenate((frame, mask), axis=1)
        cv2.imshow(name, img_concat)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = window()
    window.show()
    sys.exit(app.exec())
