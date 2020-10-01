import cv2
import numpy as np
from time import sleep

#success,image = vidcap.read()

redsay = 0
logo = cv2.imread("images/logo2.png")
h_logo, w_logo, _ = logo.shape

out = cv2.VideoWriter('output.avi', -1, 20.0, (640,480))

def calcPerc(total, current):
    return 100 * current / total

def putText(frame, text, x, y, found):
    global logo, h_logo, w_logo
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
    coor = (w_img - 115, h_img - 10)
    cv2.putText(frame, "25m/s",
                coor,
                font,
                fontScale,
                fontColor,
                lineType)

    center_y = int(h_img / 2)
    center_x = int(w_img / 2)
    top_y = center_y - int(h_logo / 2)
    left_x = center_x - int(w_logo / 2)
    bottom_y = top_y + h_logo
    right_x = left_x + w_logo
    roi = frame[top_y: bottom_y, left_x: right_x]
    # Add the Logo to the Roi
    result = cv2.addWeighted(roi, 1, logo, 0.2, 0)
    # Replace the ROI on the image
    frame[top_y: bottom_y, left_x: right_x] = result
    return frame

def detectRedColor(frame):
    global redsay, out
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, (0, 250, 100), (180, 255, 255))
    mask2 = cv2.inRange(hsv, (0, 217, 120), (180, 255, 255))
    mask = mask1 + mask2
    rows, cols = mask.shape
    square = rows * cols
    perc = calcPerc(square, cv2.countNonZero(mask))
    redmask = cv2.bitwise_and(frame, frame, mask=mask)
    if perc >= 2:
        cv2.imshow("yazi", putText(frame, "%" + "{:.2f}".format(perc) + " match", 10, rows - 10, 1))
        sleep(0.05)
        #cv2.waitKey()
    else:
        cv2.imshow("yazi", putText(frame, "%" + "{:.2f}".format(perc) + " match", 10, rows - 10, 0))

    out.write(putText(frame, "%" + "{:.2f}".format(perc) + " match", 10, rows - 10, 1))


def detectCircles(frame):
    global redsay
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, (0, 250, 100), (180, 255, 255))
    mask2 = cv2.inRange(hsv, (0, 217, 120), (180, 255, 255))
    mask = mask1 + mask2
    gau_blur = cv2.GaussianBlur(mask, (9, 9), 2, 2)  # 2, 100
    rows, cols = gau_blur.shape                    #1, (rows / 8), 200, 100)
    circles = cv2.HoughCircles(gau_blur, cv2.HOUGH_GRADIENT, 2, 100)
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            cv2.circle(frame, (x, y), r, (0, 255, 0), 4)
            cv2.rectangle(frame, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)
    cv2.imshow("circle", frame)
    #redsay += 1
    #cv2.imshow("mask" + str(redsay), mask)
    #cv2.imshow("circle" + str(redsay), frame)

def videodanIsle(type = 0):
    global out
    try:
        cap = cv2.VideoCapture('images/60_fps.h264')
        success = True
        print("basladi")
        while success:
            success, frame = cap.read()
            if type == 0:
                detectRedColor(frame)
            elif type == 1:
                detectCircles(frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("video kapandi")
                break
        cap.release()
        cv2.destroyAllWindows()
        out.release()
    except Exception as ex:
        print("")

videodanIsle(0)

"""
image = cv2.imread("20m.png")
detectRedColor(image)

image = cv2.imread("20m1.png")
detectRedColor(image)

image = cv2.imread("20m2.png")
detectRedColor(image)

image = cv2.imread("c_20.png")
detectRedColor(image)

image = cv2.imread("c_47.png")
detectRedColor(image)


image = cv2.imread("c_15.png")
detectRedColor(image)

image = cv2.imread("c_16.png")
detectRedColor(image)

image = cv2.imread("c_17.png")
detectRedColor(image)
"""
#image = cv2.imread("3.png")
#detectRedColor(image)
"""
try:
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
    print("Kamera Açıldı")
    while (True):
        ret, frame = cap.read()
        detectRedColor(frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("kamera kapandi")
            break
    cap.release()
    cv2.destroyAllWindows()
    self.findByImage(classId)
except Exception as er:
    print(str(er))   
"""


