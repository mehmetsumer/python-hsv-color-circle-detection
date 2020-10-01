import math
import os
import random
from datetime import datetime

from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import *
from PyQt5.uic import *
import sys
import cv2
from skimage import io, color
import numpy as np
from skimage.transform import resize
from skimage import data, img_as_float
from skimage.metrics import structural_similarity
import studentSingle
import yoklamaSingle
from DBHelper import Database
from PyQt5 import QtWidgets

db = Database.db
users = []
classes = []
uCount = 0
nw = ""
editClass = False
ranks = ["Seviye Yok", "Öğrenci", "Öğretmen", "Yönetici"]

path = "mainImages/yuzler"
camFileName = "mainImages/tempKamera.png"
dbFileName = "mainImages/tempDb.png"
sonucFileName = "mainImages/tempSonuc.png"
userFileName = "mainImages/userImage.png"
gurultuFileName = "mainImages/gurultuOutput.png"
pixSize = [225, 225]
numberTut = ""
started = False
tabanDegeri = 70
sliderMax = 80
gurultuImg = ""
w = 0
h = 0
toplu = False
facesTut = []
imgTut =[]
usersTut = []

def alert(title, txt):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(txt)
    msg.exec_()

def tespit_et_mse(image1, image2):
    err = np.sum((image1.astype("float") - image2.astype("float")) ** 2)
    err /= float(image1.shape[0] * image1.shape[1])
    return err * 10

def tespit_et_ssim(image1, image2):
    image1 = img_as_float(image1)
    image2 = img_as_float(image2)
    return structural_similarity(image1, image2, dynamic_range=image2.max() - image2.min())

def write_file(data, filename):
    with open(filename, 'wb') as f:
        f.write(data)

class window(QMainWindow):
    def __init__(self):
        global sliderMax
        super(window, self).__init__()
        loadUi("main.ui", self)
        self.btDelClass.setVisible(False)
        self.lbAlert.setVisible(False)
        self.btYoklama.setVisible(False)
        self.lbTime.setText(datetime.today().strftime('%H:%M'))
        self.lbDate.setText(datetime.today().strftime('%d-%m-%Y'))
        self.btCamera.clicked.connect(self.btCameraClicked)
        self.btYoklama.clicked.connect(self.btYoklamaClicked)
        self.btStart.clicked.connect(self.btStartClicked)
        self.btDetails.clicked.connect(self.btDetailsClicked)
        self.btAddStudent.clicked.connect(self.btAddStudentClicked)  # kaydet butonu click bağlantısı
        self.btDelClass.clicked.connect(self.btDelClassClicked)
        self.btAddClass.clicked.connect(self.btAddClassClicked)
        self.tableUsers.doubleClicked.connect(self.tableUsersDouble)
        self.tableUsers.cellClicked.connect(self.tableUsersClicked)
        self.tableClasses.doubleClicked.connect(self.tableClassesDouble)
        self.tbSearch.textChanged.connect(self.tbSearchChanged)
        self.gurultuSlider.valueChanged.connect(self.sliderChange)
        self.gurultuSlider.setRange(0, sliderMax)
        self.arrangeTables()
        self.getUsers(False, False)
        self.gbSonuc.move(10, 560)
        self.gbSonuc.setVisible(False)
        self.gbSonuc2.setVisible(False)
        self.getClasses()
        self.cbClasses.currentIndexChanged.connect(self.classesChanged)

    def sliderChange(self):
        global sliderMax, gurultuImg, w, h
        sliderVal = self.gurultuSlider.value()
        alan = w * h
        gurultuCount = math.ceil(alan * sliderVal / 100)
        print(str(sliderVal))
        print(str(alan))
        print(str(gurultuCount))
        self.tuzBiberEkle(gurultuCount)

    def tuzBiberEkle(self, gurultuCount):
        global gurultuImg, pixSize, w, h
        try:
            output = gurultuImg
            output = output.resize(gurultuImg.size)
            oLoad = output.load()
            for i in range(0, gurultuCount):
                x = random.randint(0, (w-1))
                y = random.randint(0, (h-1))
                if i % 2 == 0:
                    oLoad[x, y] = (0, 0, 0)
                else:
                    oLoad[x, y] = (255, 255, 255)
            output.save(gurultuFileName)
            pixmap = QPixmap(gurultuFileName)
            pixmap = pixmap.scaled(pixSize[0], pixSize[1], Qt.KeepAspectRatio)
            self.imageUser.setPixmap(pixmap)
        except Exception as e:
            print(str(e))

    def tableUsersClicked(self):
        global gurultuFileName, userFileName, pixSize, gurultuImg, w, h
        number = str(self.tableUsers.item(self.tableUsers.currentRow(), 0).text())
        cur = db.cursor()
        query = "SELECT * from users WHERE number = " + number
        cur.execute(query)
        user = cur.fetchone()
        write_file(user[4], userFileName)
        pixmap = QPixmap(userFileName)
        pixmap = pixmap.scaled(pixSize[0], pixSize[1], Qt.KeepAspectRatio)
        self.imageUser.setPixmap(pixmap)
        gurultuImg = Image.open(userFileName)
        w, h = gurultuImg.size
        self.gurultuSlider.setValue(0)
        if os.path.isfile(gurultuFileName):
            os.remove(gurultuFileName)

    def arrangeTables(self):
        # kullanıcılar tablosunu ayarla
        headerList = ["Numara", "Ad", "Soyad", "Seviye", "Sınıf", "Devamsızlık"]
        self.tableUsers.setColumnCount(6)
        self.tableUsers.setHorizontalHeaderLabels(headerList)
        header = self.tableUsers.horizontalHeader()
        for i in range(6):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        # yoklama tablosunu ayarla
        headerList = ["YoklamaId", "Sınıf", "Tarih"]
        self.tableClasses.setColumnCount(3)
        self.tableClasses.setHorizontalHeaderLabels(headerList)
        header = self.tableClasses.horizontalHeader()
        for j in range(3):
            header.setSectionResizeMode(j, QtWidgets.QHeaderView.ResizeToContents)
        self.gbYoklamalar.setVisible(False)

    def btStartClicked(self):
        global started, db, editClass, uCount
        try:
            if uCount == 0:
                alert("HATA", "Veritabanında kullanıcı yok.")
                return
            sinif = self.cbClasses.currentText()
            index = self.cbClasses.currentIndex()
            if not started: # ders başlanacak
                if index == 0 or index == 1:
                    alert("HATA", "Sınıf seçiniz")
                    return
                self.lbAlert.setText(str(sinif) + " dersi başladı..")
                self.lbAlert.setVisible(True)
                self.btYoklama.setVisible(True)
                self.btStart.setText("Dersi Bitir")
                cur = db.cursor()
                sql = "INSERT INTO yoklama (yoklamaId, classId) VALUES (%s, %s);"
                val = (None, editClass)
                cur.execute(sql, val)
                db.commit()
                started = cur.lastrowid
                print(str(started))
                self.gbSinif.setEnabled(False)
                self.cbClasses.setEnabled(False)
                self.btCamera.setEnabled(False)
                self.btAddStudent.setEnabled(False)
                self.btDetails.setVisible(False)
            else: # DERSİ BİTİRME KODLARI
                # DERSİ BİTİRİRKEN TABLODA OLMAYAN ÖĞRENCİLERİN DEVAMSIZLIKLARI 1 ARTACAK.
                self.devamsizlikArtir()
                self.btStart.setText("Dersi Başlat")
                self.lbAlert.setText(str(sinif) + " dersi bitti..")
                self.btYoklama.setVisible(False)
                self.gbSinif.setEnabled(True)
                self.btCamera.setEnabled(True)
                self.btAddStudent.setEnabled(True)
                self.btDetails.setVisible(True)
                self.cbClasses.setEnabled(True)
                self.getYoklamaTable(editClass)
                started = False
        except Exception as er:
            print(str(er))

    def devamsizlikArtir(self):
        global db, started, editClass
        cur = db.cursor()
        query = "SELECT * from yoklamadetay WHERE yoklamaId = " + str(started)
        cur.execute(query)
        detay = cur.fetchall()
        if len(detay) == 0: # BU SINIFA DAHİL HERKESİ YOK YAZ.
            sql = "UPDATE users SET yoklama = yoklama+1 WHERE classId = " + str(editClass)
            cur.execute(sql)
            db.commit()
        else:
            cur = db.cursor()
            query = "SELECT * FROM users where userId NOT IN (SELECT userId FROM yoklamadetay WHERE yoklamaId = " + str(started) + ") AND classId = " + str(editClass)
            cur.execute(query)
            users = cur.fetchall()
            if users:
                for i, data in enumerate(users):
                    sql = "UPDATE users SET yoklama = yoklama+1 WHERE userId = " + str(data[0])
                    cur.execute(sql)
                    db.commit()
        self.getUsers(False, editClass)

    def findByImage(self, tempid):
        global camFileName, db, users, tabanDegeri, toplu, facesTut, usersTut, imgTut
        number = ""
        try:
            imgIndex = 6
            nIndex = 0
            tempUsers = users
            if tempid:
                imgIndex = 4
                nIndex = 1
                cur = db.cursor()
                query = "SELECT * FROM users WHERE classId = " + str(tempid)
                cur.execute(query)
                tempUsers = cur.fetchall()
            usersTut = []
            imgTut = []
            for i, camFName in enumerate(facesTut):
                image_1 = color.rgb2gray(io.imread(camFName))
                w, h = image_1.shape[:2]
                for j, row in enumerate(tempUsers):
                    imgTemp = row[imgIndex]
                    write_file(imgTemp, dbFileName) #DB deki image tempDb.png dosyasına yazılıyor.
                    image_2 = color.rgb2gray(io.imread(dbFileName))
                    image_2 = resize(image_2, (w, h))
                    algo = self.cbAlgo.currentIndex()
                    similarity = 0
                    if algo == 0: # SSIM
                        similarity = tespit_et_ssim(image_1, image_2)
                        #print("SSIM: " + str(similarity) + " - " + str(row[nIndex]))
                    elif algo == 1: # MSE
                        similarity = tespit_et_mse(image_1, image_2)
                        #print("MSE: " + str(similarity) + " - " + str(row[nIndex]))
                    if j == 0:
                        best_ssim = similarity
                        best_image = imgTemp
                        number = str(row[nIndex])
                    else:
                        if algo == 0: # SSIM
                            if similarity > best_ssim:
                                best_ssim = similarity
                                best_image = imgTemp
                                number = str(row[nIndex])
                        elif algo == 1:  # MSE
                            if similarity < best_ssim:
                                best_ssim = similarity
                                best_image = imgTemp
                                number = str(row[nIndex])
                write_file(best_image, sonucFileName)
                best_ssim *= 100
                if algo == 1:
                    best_ssim = 100 - best_ssim
                print("Bulunan kullanıcı:", number + " %: " + str(best_ssim))
                if best_ssim >= tabanDegeri:
                    usersTut.append(number)
                    imgTut.append(camFName)
                    if tempid:
                        self.yoklamayaEkle(number)
                    else:
                        self.showResult(number, best_ssim)
            if len(imgTut) > 1:
                self.sonucGoster()
            elif len(imgTut) == 1:
                self.showResult(number, best_ssim)
            else:
                alert("HATA", "Öğrenci bulunamadı.")
        except Exception as error:
            print(format(error))

    def sonucGoster(self):
        global usersTut, imgTut
        self.gbSonuc2.setVisible(True)
        self.gbSonuc.setVisible(False)
        imW = 100
        imH = 100
        satir = QHBoxLayout()
        for i, img in enumerate(imgTut):
            sutun = QVBoxLayout()
            lbTitle = QtWidgets.QLabel(self.gbSonuc2)
            lbTitle.setAlignment(Qt.AlignCenter)
            lbTitle.setText(usersTut[i])
            lbTitle.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
            lbImage = QtWidgets.QLabel(self.gbSonuc2)
            lbImage.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
            lbImage.setAlignment(Qt.AlignCenter)
            pixmap = QPixmap(img)
            pixmap = pixmap.scaled(imW, imH, Qt.KeepAspectRatio)
            lbImage.setPixmap(pixmap)
            btDetay = QtWidgets.QPushButton(self.gbSonuc2)
            btDetay.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            btDetay.setText("Detay")
            btDetay.clicked.connect(lambda: self.goToUserSingle(usersTut[i]))
            sutun.addWidget(lbTitle)
            sutun.addWidget(lbImage)
            sutun.addWidget(btDetay)
            satir.addLayout(sutun)
        self.gbSonuc2.setLayout(satir)

    def yoklamayaEkle(self, number):
        global db, started, toplu
        cur = db.cursor()
        query = "SELECT * FROM users WHERE number = " + str(number)
        cur.execute(query)
        user = cur.fetchone()
        userId = user[0]
        cur = db.cursor()
        query = "SELECT * FROM yoklamadetay WHERE yoklamaId = " + str(started) + " AND userId = " + str(userId)
        cur.execute(query)
        user = cur.fetchone()
        if user:
            print(str(number) + " numaralı öğrencinin yoklaması zaten alınmış.")
            alert("HATA", str(number) + " numaralı öğrencinin yoklaması zaten alınmış.")
            return
        cur = db.cursor()
        sql = "INSERT INTO yoklamadetay (yoklamaId, userId) VALUES (%s, %s);"
        val = (started, userId)
        cur.execute(sql, val)
        db.commit()
        alert("BİLGİ", str(number) + " numaralı öğrencinin yoklaması alındı.")
        print(str(number) + " yoklamaya eklendi.")
        return

    def btYoklamaClicked(self):
        global editClass
        self.kameraAc(editClass)

    def btDetailsClicked(self):
        global numberTut, nw
        self.goToUserSingle(numberTut)

    def showResult(self, number, best):
        global camFileName, dbFileName, numberTut
        self.gbSonuc.setVisible(True)
        self.gbSonuc2.setVisible(False)
        pixmap = QPixmap(path + "/tempKamera_1")
        pixmap = pixmap.scaled(pixSize[0], pixSize[1], Qt.KeepAspectRatio)
        self.imageAranan.resize(pixSize[0], pixSize[1])
        self.imageAranan.setPixmap(pixmap)
        pixmap = QPixmap(sonucFileName)
        pixmap = pixmap.scaled(pixSize[0], pixSize[1], Qt.KeepAspectRatio)
        self.imageSonuc.resize(pixSize[0], pixSize[1])
        self.imageSonuc.setPixmap(pixmap)
        numberTut = number
        self.lbNumara.setText("Öğrenci Numarası: " + number)
        self.lbBasari.setText("Başarı Oranı: %" + format(best, '.2f'))

    '''def findByImage(self, tempid):
        global camFileName, db, users, tabanDegeri, toplu, facesTut
        number = ""
        try:
            imgIndex = 6
            nIndex = 0
            tempUsers = users
            if tempid:
                imgIndex = 4
                nIndex = 1
                cur = db.cursor()
                query = "SELECT * FROM users WHERE classId = " + str(tempid)
                cur.execute(query)
                tempUsers = cur.fetchall()
            image_1 = color.rgb2gray(io.imread(camFileName))
            w, h = image_1.shape[:2]
            for i, row in enumerate(tempUsers):
                imgTemp = row[imgIndex]
                write_file(imgTemp, dbFileName) #DB deki image tempDb.png dosyasına yazılıyor.
                image_2 = color.rgb2gray(io.imread(dbFileName))
                image_2 = resize(image_2, (w, h))
                #print(image_1.shape, image_2.shape)
                algo = self.cbAlgo.currentIndex()
                similarity = 0
                if algo == 0: # SSIM
                    similarity = tespit_et_ssim(image_1, image_2)
                    print("SSIM: " + str(similarity) + " - " + str(row[nIndex]))
                elif algo == 1: # MSE
                    similarity = tespit_et_mse(image_1, image_2)
                    print("MSE: " + str(similarity) + " - " + str(row[nIndex]))
                if i == 0:
                    best_ssim = similarity
                    best_image = imgTemp
                    number = str(row[nIndex])
                else:
                    if algo == 0: # SSIM
                        if similarity > best_ssim:
                            best_ssim = similarity
                            best_image = imgTemp
                            number = str(row[nIndex])
                    elif algo == 1:  # MSE
                        if similarity < best_ssim:
                            best_ssim = similarity
                            best_image = imgTemp
                            number = str(row[nIndex])
            write_file(best_image, sonucFileName)
            best_ssim *= 100
            if algo == 1:
                best_ssim = 100 - best_ssim
            print("EN YÜKSEK: ", str(best_ssim))
            print("Bulunan kullanıcı:", number)
            if best_ssim >= tabanDegeri:
                if tempid:
                    self.showResult(number, best_ssim)
                    self.yoklamayaEkle(number)
                else:
                    self.showResult(number, best_ssim)
            else:
                alert("HATA", "Öğrenci bulunamadı")
            #print("Bulunan image:", best_image)
        except Exception as error:
            print(format(error))
    '''
    def btCameraClicked(self):
        self.kameraAc(False)

    def kameraAc(self, classId):
        global uCount, facesTut
        if uCount == 0:
            alert("HATA", "Veritabanında kullanıcı yok.")
            return
        try:
            faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
            print("Kamera Açıldı")
            while (True):
                facesTut = []
                ret, frame = cap.read()
                roi = frame  # [0:500, 0:500]
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                faces = faceCascade.detectMultiScale(gray, 1.1, 4)
                for (x, y, w, h) in faces:
                    cv2.rectangle(roi, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.imshow('img', roi)
                sayac = 0
                for (x, y, w, h) in faces:
                    cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    sayac += 1  # yuzleri kaydetmek icin
                    crop_img = roi[y:y + h, x:x + w]
                    save_file_name = path + "/" + ("tempKamera_" + str(sayac)) + '.png'
                    cv2.imwrite(save_file_name, crop_img)
                    facesTut.append(save_file_name)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("kamera kapandi")
                    break
            cap.release()
            cv2.destroyAllWindows()
            self.findByImage(classId)
        except Exception as er:
            print(str(er))

    def btDelClassClicked(self):
        global db, editClass
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Bu sınıfı silerseniz bütün öğrencileri de silinecek.")
            msg.setWindowTitle("Emin misiniz?")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            retval = msg.exec_()
            if retval == 1024:
                cur = db.cursor()
                cur.execute("DELETE FROM users WHERE classId = " + str(editClass))
                db.commit()
                cur = db.cursor()
                cur.execute("DELETE FROM classes WHERE classId = " + str(editClass))
                db.commit()
                alert("Başarılı", "Sınıf başarıyla silindi.")
                self.clearTB()
                self.getClasses()
        except Exception as error:
            print(format(error))

    def btAddClassClicked(self):
        global db, editClass
        try:
            cur = db.cursor()
            alertText = ""
            className = self.tbClass.text()
            if len(className) < 2:
                alert("HATA", "Geçerli sınıf adı girin.")
                return
            if editClass:  # edit
                cur.execute(
                    "SELECT * FROM classes WHERE className LIKE '%" + className + "%' AND classId != " + str(editClass))
                classes = cur.fetchall()
                if len(classes) > 0:
                    alert("Hata", "Sınıf istemde ekli.")
                    return
                sql = "UPDATE classes SET className = %s WHERE classId = %s"
                val = (className, editClass)
                cur.execute(sql, val)
                alertText = "Sınıf başarıyla güncellendi."
            else:  # add
                cur.execute("SELECT * FROM classes WHERE className LIKE '%" + className + "%'")
                classes = cur.fetchall()
                if len(classes) > 0:
                    alert("Hata", "Sınıf istemde ekli.")
                    return
                cur = db.cursor()
                sql = "INSERT INTO classes (classId, className) VALUES (%s, %s);"
                val = (None, className)
                cur.execute(sql, val)
                alertText = "Sınıf başarıyla eklendi."
            db.commit()
            alert("BİLGİ", alertText)
            self.clearTB()
            self.getClasses()
        except Exception as er:
            alert("HATA", str(er))

    def clearTB(self):
        global editClass
        editClass = False
        self.tbClass.setText("")
        self.btDelClass.setVisible(False)

    def tbSearchChanged(self):
        keyword = self.tbSearch.text()
        if len(keyword) < 2:
            keyword = False
        cL = self.cbClasses.currentIndex()
        if cL == 0:
            cl = False
        self.getUsers(keyword, cL)

    def getClasses(self):
        global db, classes
        cur = db.cursor()
        query = "SELECT * FROM classes WHERE classId != 1 ORDER BY className"
        cur.execute(query)
        classes = cur.fetchall()
        self.cbClasses.clear()
        self.cbClasses.addItem("Hepsi", 0)
        self.cbClasses.addItem("Yönetici", 1)
        for i, data in enumerate(classes):
            self.cbClasses.addItem(data[1], data[0])

    def getYoklamaTable(self, id):
        global db
        try:
            cur = db.cursor()
            query = "SELECT y.yoklamaId, c.className, y.derstarihi FROM yoklama y INNER JOIN classes c ON y.classId = c.classId WHERE y.classId = " + str(id)
            cur.execute(query)
            yoklamalar = cur.fetchall()
            yCount = len(yoklamalar)
            self.gbYoklamalar.setVisible(True)
            if yCount == 0:
                self.gbYoklamalar.setVisible(False)
                return
            #self.resize(1241, self.height())
            self.tableClasses.setRowCount(0)
            for i, row in enumerate(yoklamalar):
                self.tableClasses.insertRow(i)
                for j, column in enumerate(row):
                    print(column)
                    if j == 2:
                        column = column.strftime('%d-%m-%Y %H:%M')
                    self.tableClasses.setItem(i, j, QtWidgets.QTableWidgetItem(str(column)))
        except Exception as er:
            print(str(er))

    def classesChanged(self):
        global editClass
        cL = self.cbClasses.itemData(self.cbClasses.currentIndex())
        keyword = self.tbSearch.text()
        if cL == 0:
            cL = False
        if len(keyword) < 2:
            keyword = False
        if cL:
            cur = db.cursor()
            query = "SELECT * from classes WHERE classId =" + str(cL)
            cur.execute(query)
            classTemp = cur.fetchone()
            if cL != 1:
                self.btAddClass.setText("Sınıf Güncelle")
                self.tbClass.setText(classTemp[1])
                self.btDelClass.setVisible(True)
                self.getYoklamaTable(cL)
            else:
                self.btAddClass.setText("Sınıf Ekle")
                #self.resize(551, self.height())
                self.gbYoklamalar.setVisible(False)
                self.clearTB()
        else:
            #self.resize(551, self.height())
            self.gbYoklamalar.setVisible(False)
            self.btAddClass.setText("Sınıf Ekle")
            self.clearTB()
        editClass = cL
        self.getUsers(keyword, cL)

    def goToUserSingle(self, number):
        global nw
        nw = studentSingle.window(str(number), False)
        nw.show()
        #self.hide()

    def tableClassesDouble(self):
        global nw, started, db, editClass
        if not started:
            yoklamaId = str(self.tableClasses.item(self.tableClasses.currentRow(), 0).text())
            cur = db.cursor()
            query = "SELECT u.number, u.name, u.surname, u.yoklama, c.className, y.* FROM users u, yoklama y, classes c WHERE  y.yoklamaId = " + str(yoklamaId) + \
                    " AND u.userId IN (SELECT userId FROM yoklamadetay WHERE yoklamaId = "+str(yoklamaId)+") AND c.classId = "+ str(editClass) + " AND u.classId = "+ str(editClass)
            cur.execute(query)
            yoklamalar = cur.fetchall()
            if len(yoklamalar) == 0:
                alert("HATA", "Bu derse hiçbir öğrenci katılmamış.")
                return
            nw = yoklamaSingle.window(yoklamalar)
            nw.show()
            self.hide()

    def tableUsersDouble(self):
        global nw, started
        if not started:
            number = str(self.tableUsers.item(self.tableUsers.currentRow(), 0).text())
            nw = studentSingle.window(str(number), True)
            nw.show()
            self.hide()

    def getUsers(self, keyword, cl):
        global db, users, uCount
        try:
            cur = db.cursor()
            word = " WHERE"
            query = "SELECT u.number, u.name, u.surname, u.rankId, c.className, u.yoklama, u.image FROM users u INNER JOIN classes c ON c.classId = u.classId"
            if keyword:
                query += " WHERE (u.number LIKE '%" + keyword + "%' OR u.name LIKE '%" + keyword + "%' OR u.surname LIKE '%" + keyword + "%')"
                word = " AND"
            if cl:
                query += word + " u.classId = " + str(cl)
            cur.execute(query)
            users = cur.fetchall()
            uCount = len(users)
            #uCount = 0
            self.gurultuSlider.setEnabled(True)
            self.tableUsers.setVisible(True)
            if uCount == 0:
                self.tableUsers.setVisible(False)
                self.gurultuSlider.setEnabled(False)
                self.imageUser.setText("Kullanıcı Yok")
                return
            self.tableUsers.setRowCount(0)
            for i, row in enumerate(users):
                self.tableUsers.insertRow(i)
                for j, column in enumerate(row):
                    if j == 3:
                        column = ranks[column]
                    elif j == 4:
                        column = column
                    self.tableUsers.setItem(i, j, QtWidgets.QTableWidgetItem(str(column)))
            self.tableUsers.setCurrentCell(0, 0)
            self.tableUsersClicked()
        except Exception as er:
            print(str(er))

    def btAddStudentClicked(self):
        global nw
        nw = studentSingle.window(False, True)
        nw.show()
        self.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = window()
    window.show()
    sys.exit(app.exec())
