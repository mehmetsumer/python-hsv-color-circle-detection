from time import sleep
import time

from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtWidgets import *
from PyQt5.uic import *
import cv2
from PyQt5.Qt import QApplication, QUrl, QDesktopServices
import numpy as np
import sys
import pathlib


def alert(title, txt, type=QMessageBox.Critical):
    msg = QMessageBox()
    msg.setIcon(type)
    msg.setWindowTitle(title)
    msg.setText(txt)
    msg.exec_()

net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
classes = []
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
layer_names = net.getLayerNames()
output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
colors = np.random.uniform(0, 255, size=(len(classes), 3))

start_time = 0

class window(QMainWindow):

    def __init__(self):
        super(window, self).__init__()
        loadUi("object_detection.ui", self)
        self.bt_camera.clicked.connect(self.startCamera)
        self.bt_images.clicked.connect(self.showImagesDialog)
        self.bt_video.clicked.connect(self.showFileDialog)

    def startCamera(self):
        global start_time
        try:
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
            while(True):
                start_time = time.time()  # start time of the loop
                key = cv2.waitKey(1) & 0xFF
                ret, frame = cap.read()
                self.detectObjects(frame)
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    break
        except Exception as er:
            print(str(er))

    def detectObjects(self, frame, is_video=True):
        global start_time
        # frame = cv2.resize(frame, None, fx=0.4, fy=0.4)
        height, width, channels = frame.shape

        # Detecting objects
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        # Showing informations on the screen
        class_ids = []
        confidences = []
        boxes = []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    # Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        print(indexes)
        font = cv2.FONT_HERSHEY_SIMPLEX
        for i in range(len(boxes)):
            if i in indexes and confidences[i] >= 0.80:
                x, y, w, h = boxes[i]
                label = str(classes[class_ids[i]]) + "_" + "{:.2f}".format(confidences[i])
                color = colors[class_ids[i]]
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, label, (x, y), font, 0.8, color, 2)
        if is_video:
            cv2.putText(frame, "Fps: " + str("{:.0f}".format(round(1.0 / (time.time() - start_time), 0))), (5, 30), font, 0.8, (214, 127, 12), 2)
            cv2.imshow("Image", frame)
        else:
            cv2.imshow("Image_" + str(confidences), frame)

    def proccessVideo(self, path):
        global start_time
        try:
            cap = cv2.VideoCapture(path)
            success = True
            while success:
                start_time = time.time()  # start time of the loop
                success, frame = cap.read()
                key = cv2.waitKey(1) & 0xFF
                if key == ord('p'):
                    cv2.waitKey(0)
                self.detectObjects(frame)
                if key == ord('q'):
                    print("video kapandi")
                    break
            print("bitti")
            cap.release()
            cv2.destroyAllWindows()
        except Exception as ex:
            #alert("Error", str(ex))
            print("")

    def showFileDialog(self):
        file = QFileDialog.getOpenFileName(self, 'Choose a Video File',
                                           str(pathlib.Path().absolute()) + "/images",
                                           "Video files (*.mp4 *.h264 *.avi)")
        if file[0] != "":
            self.proccessVideo(str(file[0]))

    def showImagesDialog(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "Choose Multiple Images",
                                                str(pathlib.Path().absolute()) + "/images",
                                                "Image Files (*.jpg *.png *.jpeg)", options=options)
        for file in files:
            frame = cv2.imread(file)
            self.detectObjects(frame, False)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = window()
    window.show()
    sys.exit(app.exec())
