from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QPixmap, QImage, QPalette, QPainter
from PyQt5.QtCore import pyqtSignal
import os
import sys
import datetime
import threading
import time
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy.linalg import inv
from numpy.linalg import pinv
import itertools as it
import os
from PIL import Image
import skimage.color
from skimage import io
import time
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.uic import loadUi
import io
import socket
import struct

st_extend_20 = 0
st_extend_21 = 1
st_extend_30 = 2


class SpectrumTransfer:

    def __init__(self):
        self.extend_mode = 0
        self.pca_eigenvectors = None
        self.pca_mean = None
        self.M = None
        self.TransM = None
        self.TransMin = 0.0
        self.TransMax = 1.0

    def get_extend_color(self, src_rgb):

        extend = None

        if self.extend_mode == 0:
            extend = np.array(
                [src_rgb[:, 0], src_rgb[:, 1], src_rgb[:, 2], np.power(src_rgb[:, 0], 2), np.power(src_rgb[:, 1], 2),
                 np.power(src_rgb[:, 2], 2)])
        elif self.extend_mode == 1:
            extend = np.array(
                [src_rgb[:, 0], src_rgb[:, 1], src_rgb[:, 2], np.power(src_rgb[:, 0], 2), np.power(src_rgb[:, 1], 2),
                 np.power(src_rgb[:, 2], 2), src_rgb[:, 0] * src_rgb[:, 1], src_rgb[:, 0] * src_rgb[:, 2],
                 src_rgb[:, 1] * src_rgb[:, 2]])
        elif self.extend_mode == 2:
            extend = np.array(
                [src_rgb[:, 0], src_rgb[:, 1], src_rgb[:, 2], np.power(src_rgb[:, 0], 2), np.power(src_rgb[:, 1], 2),
                 np.power(src_rgb[:, 2], 2), src_rgb[:, 0] * src_rgb[:, 1], src_rgb[:, 0] * src_rgb[:, 2],
                 src_rgb[:, 1] * src_rgb[:, 2], np.power(src_rgb[:, 0], 3), np.power(src_rgb[:, 1], 3),
                 np.power(src_rgb[:, 2], 3)])

        return extend

    def prepare(self):
        self.TransM = np.dot(self.M.T, self.pca_eigenvectors)
        return

    def train(self, extend_mode, train_spec, train_color, pca_comps=6):
        self.extend_mode = extend_mode

        pca = PCA(n_components=pca_comps, whiten=False)
        pca.fit(train_spec)

        self.pca_eigenvectors = pca.components_
        self.pca_mean = pca.mean_

        trans_pca_a = pca.transform(train_spec)
        trans_extend_c = self.get_extend_color(train_color)

        self.M = np.dot(trans_pca_a.T, pinv(trans_extend_c))

        self.prepare()

        c = np.arange(256)
        all_color = np.array(np.meshgrid(c, c, c)).T.reshape(-1, 3)

        self.TransMin = 0.0
        self.TransMax = 1.0
        return

    def save(self, setup_file):
        np.savez(setup_file, a=self.M, b=self.pca_eigenvectors, c=self.pca_mean,
                 d=np.array([self.TransMin, self.TransMax]), e=np.array([self.extend_mode]))

    def load(self, setup_file):
        weight = np.load(setup_file)

        self.M = weight["a"]
        self.pca_eigenvectors = weight["b"]
        self.pca_mean = weight["c"]
        self.extend_mode = weight['e'][0]
        self.prepare()
        return

    def transfer1D(self, src_data):

        src_data = src_data.astype(np.float32)

        tar_sepc = np.dot(self.get_extend_color(src_data).T, self.TransM) + self.pca_mean

        tar_sepc = (tar_sepc - self.TransMin) / (self.TransMax - self.TransMin)

        return tar_sepc

    def transfer(self, src_data):

        src_data = src_data.astype(np.float32)

        src_shape = src_data.shape

        if len(src_shape) >= 3:
            src_data = src_data.reshape(-1, src_shape[-1])

        tar_sepc = np.dot(self.get_extend_color(src_data).T, self.TransM) + self.pca_mean

        if len(src_shape) >= 3:
            tar_sepc = tar_sepc.reshape(src_shape[0:-1] + tuple([self.pca_mean.shape[0]]))

        tar_sepc = (tar_sepc - self.TransMin) / (self.TransMax - self.TransMin)

        return tar_sepc


class ColorReproducer:

    def __init__(self):
        self.light_spec = None
        self.cmf = None
        self.ma = None
        self.d65 = np.array([0.95047, 1.00000000, 1.08883])
        self.is_ignore_ca = False

        self.light_spec_x3 = None
        self.cal_fact = None
        self.k = None
        self.white_light_k = None

    def prepare(self):
        self.light_spec_x3 = np.array([self.light_spec, self.light_spec, self.light_spec]).T
        self.cal_fact = self.cmf * self.light_spec_x3
        self.k = 100.0 / sum(self.cal_fact[:, 1])
        self.white_light_k = np.dot(self.cmf.T, self.light_spec) * (self.k / 100.0)
        self.cal_fact = self.cal_fact * self.k

        return

    def load(self, setup_path):
        self.light_spec = np.loadtxt(os.path.join(setup_path, 'CR_light.txt'))
        self.cmf = np.loadtxt(os.path.join(setup_path, 'CR_cmf.txt'))
        self.ma = np.loadtxt(os.path.join(setup_path, 'CR_ma.txt'))

        self.prepare()
        return

    def reproduce(self, img_spec, gain=1.0, is_normalize=False, filter_band=None):

        h, w, c = img_spec.shape

        img_spec = img_spec.reshape((-1, c));

        fact = None

        if self.is_ignore_ca:
            fact = self.cal_fact
        else:
            fact = inv(self.ma).dot(np.diag(self.ma.dot(self.d65) / self.ma.dot(self.white_light_k))).dot(self.ma)
            fact = fact.dot(self.cal_fact.T).T

        op_ref_spec = None

        if filter_band is not None:

            filter_band_set = filter_band - 380

            mask = np.zeros((w * h, 401))

            mask[:, filter_band_set] = 1

            op_ref_spec = img_spec * mask * gain

        else:

            op_ref_spec = img_spec * gain

        if is_normalize:

            img_rep_xyz = op_ref_spec.dot(fact)

            min_v = img_rep_xyz.min()
            max_v = img_rep_xyz.max()

            img_rep_xyz = (img_rep_xyz - min_v) / (max_v - min_v) * 255.0

        else:

            img_rep_xyz = op_ref_spec.dot(fact) / 100.0 * 255.0

        img_rep_xyz = img_rep_xyz.reshape(h, w, 3).astype('uint8')

        img_rep_rgb = cv2.cvtColor(img_rep_xyz, cv2.COLOR_XYZ2RGB)

        return img_rep_rgb


def display_band_selected(filter_band):
    filter_band_set = filter_band - 380

    x = np.arange(380, 781, 1)

    select_mask = np.zeros((401))

    select_c = 'g'
    unselect_c = 'gray'

    select_mask = select_mask + 0.5
    select_mask[filter_band_set] = 1

    plt.figure(figsize=(15, 1))
    plt.title('Select band info')
    plt.xlim(380, 781)
    plt.ylim(0, 1.0)
    plt.xticks(np.arange(380, 781, 10))
    plt.yticks([])
    plt.grid(True)
    barlist = plt.bar(x, select_mask, width=1, color=unselect_c)

    for i in filter_band_set:
        barlist[i].set_color(select_c)

    plt.show()

transfer = SpectrumTransfer()
transfer.load("weight.npz")

reproducer = ColorReproducer()
reproducer.load('cr_weights')

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1111, 791)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        MainWindow.setFont(font)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.BTNStop = QtWidgets.QPushButton(self.centralwidget)
        self.BTNStop.setGeometry(QtCore.QRect(350, 520, 160, 72))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.BTNStop.setFont(font)
        self.BTNStop.setObjectName("BTNStop")
        self.LLInfo = QtWidgets.QLabel(self.centralwidget)
        self.LLInfo.setGeometry(QtCore.QRect(10, 600, 511, 31))
        self.LLInfo.setAlignment(QtCore.Qt.AlignCenter)
        self.LLInfo.setObjectName("LLInfo")
        self.BTNStart = QtWidgets.QPushButton(self.centralwidget)
        self.BTNStart.setGeometry(QtCore.QRect(10, 520, 160, 72))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.BTNStart.setFont(font)
        self.BTNStart.setStyleSheet("QPushButton {\n"
"background-color: #C5C6C7;\n"
"\n"
"}")
        self.BTNStart.setObjectName("BTNStart")
        self.LLImage = QtWidgets.QLabel(self.centralwidget)
        self.LLImage.setGeometry(QtCore.QRect(10, 180, 521, 321))
        self.LLImage.setStyleSheet("QLabel {\n"
"border: 2px solid;\n"
"border-color: rgb(255, 255, 255);\n"
"}")
        self.LLImage.setText("")
        self.LLImage.setObjectName("LLImage")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(600, 420, 221, 31))
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_4.setFont(font)
        self.label_4.setStyleSheet("font-size:15pt;")
        self.label_4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_4.setObjectName("label_4")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(600, 310, 241, 31))
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_3.setFont(font)
        self.label_3.setStyleSheet("font-size:15pt;")
        self.label_3.setObjectName("label_3")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(600, 200, 241, 31))
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_2.setFont(font)
        self.label_2.setStyleSheet("font-size:15pt;")
        self.label_2.setObjectName("label_2")
        self.password = QtWidgets.QLineEdit(self.centralwidget)
        self.password.setGeometry(QtCore.QRect(850, 300, 241, 51))
        self.password.setStyleSheet("font-size:14pt;")
        self.password.setText("")
        self.password.setObjectName("password")
        self.password.setText("510")
        self.email = QtWidgets.QLineEdit(self.centralwidget)
        self.email.setGeometry(QtCore.QRect(850, 190, 241, 51))
        self.email.setStyleSheet("font-size:14pt;")
        self.email.setObjectName("email")
        self.email.setText("500")
        self.gain = QtWidgets.QLineEdit(self.centralwidget)
        self.gain.setGeometry(QtCore.QRect(850, 410, 241, 51))
        self.gain.setStyleSheet("font-size:14pt;")
        self.gain.setText("15")
        self.gain.setObjectName("gain")
        self.BTNCapture = QtWidgets.QPushButton(self.centralwidget)
        self.BTNCapture.setGeometry(QtCore.QRect(180, 520, 160, 72))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.BTNCapture.setFont(font)
        self.BTNCapture.setObjectName("BTNCapture")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(240, 30, 631, 81))
        font = QtGui.QFont()
        font.setFamily("Algerian")
        font.setPointSize(36)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(0, 620, 1111, 111))
        font = QtGui.QFont()
        font.setFamily("Imprint MT Shadow")
        font.setPointSize(32)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.label_5.setFont(font)
        self.label_5.setStyleSheet("font: 32pt;")
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setObjectName("label_5")
        self.loginbutton = QtWidgets.QPushButton(self.centralwidget)
        self.loginbutton.setGeometry(QtCore.QRect(690, 510, 160, 72))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.loginbutton.setFont(font)
        self.loginbutton.setObjectName("loginbutton")
        self.BTNStop_3 = QtWidgets.QPushButton(self.centralwidget)
        self.BTNStop_3.setGeometry(QtCore.QRect(880, 510, 160, 72))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.BTNStop_3.setFont(font)
        self.BTNStop_3.setObjectName("BTNStop_3")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1111, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.loginbutton.clicked.connect(self.loginfunction)
        self.BTNStop_3.clicked.connect(self.Analysefunction)
        self.BTNCapture.clicked.connect(self.capturefunction)

    def loginfunction(self):
        email=self.email.text()
        password=self.password.text()
        gain=self.gain.text()
        print("Upper Limit: ", email, "Lower Limit:", password, "and gain:", gain)
        global x
        global y
        global z
        x= int(email)
        y = int(password)
        z = int(gain)

    def capturefunction(self):
        global m_now_image
        cv2.imwrite('Capture.png', m_now_image)

    def Analysefunction(self):
        global m_now_image


        nbi_file = 'nbi.bmp'
        gain = int(z)

        is_normalize = False
        filter_band = np.arange(int(x), int(y), 1)
        img = m_now_image

        spec = transfer.transfer(img);

        nbi = reproducer.reproduce(spec, gain, is_normalize, filter_band)
        nbi_bgr = cv2.cvtColor(nbi, cv2.COLOR_RGB2BGR)

        cv2.imwrite(nbi_file, nbi_bgr)

        img_rgb = 'nbi.bmp'

        img1 = cv2.imread(img_rgb)
        img_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        template = cv2.imread('Template.png', 0)

        w, h = template.shape
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        _, _, _, maxLoc = cv2.minMaxLoc(res)
        cv2.rectangle(img1, maxLoc, (maxLoc[0] + h, maxLoc[1] + w), (0, 255, 255), 2)
        crop_img = img1[maxLoc[1]:maxLoc[1] + w, maxLoc[0]:maxLoc[0] + h, :]
        print(np.mean(crop_img))
        cv2.imwrite('cropped.png', crop_img)

        nm = int(x)


        if nm == 400 and np.mean(crop_img) > 69.5:

            self.label_5.setText("The Hologram is Original")

        elif nm == 450 and np.mean(crop_img) > 61:
            self.label_5.setText("The Hologram is Original")


        elif nm == 500 and np.mean(crop_img) > 65.5:
            self.label_5.setText("The Hologram is Original")

        elif nm == 550 and np.mean(crop_img) > 20:
            self.label_5.setText("The Hologram is Original")

        elif nm == 600 and np.mean(crop_img) > 59:
            self.label_5.setText("The Hologram is Original")

        elif nm == 650 and np.mean(crop_img) > 66.5:
            self.label_5.setText("The Hologram is Original")

        elif nm == 700 and np.mean(crop_img) > 70.5:
            self.label_5.setText("The Hologram is Original")
        else:
            self.label_5.setText("The Hologram is Counterfeit")

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Fake Currency Detector"))
        self.BTNStop.setText(_translate("MainWindow", "Stop"))
        self.LLInfo.setText(_translate("MainWindow", "Info..."))
        self.BTNStart.setText(_translate("MainWindow", "Start"))
        self.label_4.setText(_translate("MainWindow", "Gain"))
        self.label_3.setText(_translate("MainWindow", "Upper Wavelength Value"))
        self.label_2.setText(_translate("MainWindow", "Lower Wavelength Value"))
        self.BTNCapture.setText(_translate("MainWindow", "Capture"))
        self.label.setText(_translate("MainWindow", "Fake Hologram Detector"))
        self.label_5.setText(_translate("MainWindow", "AWAITING RESULTS"))
        self.loginbutton.setText(_translate("MainWindow", "Ok"))
        self.BTNStop_3.setText(_translate("MainWindow", "Analyse"))


def BTNStart_clicked(click):
    global m_is_live
    global m_now_frame_count

    m_now_frame_count = 0
    m_is_live = True

    m_ui.BTNStart.setEnabled(False)
    m_ui.BTNStop.setEnabled(True)
    m_ui.LLInfo.setText("Living...");
  
def BTNStop_clicked(click):
    global m_is_live

    m_is_live = False

    m_ui.BTNStart.setEnabled(True)
    m_ui.BTNStop.setEnabled(False)
    m_ui.LLInfo.setText("Stopped!");



def ProcessLive():

    global m_cap
    global m_is_stop
    global m_is_live
    global m_now_image
    global m_now_frame_count

    global m_buffer_time
    global m_average_frame_sec

    m_average_frame_sec = 0.0;

    while m_cap.isOpened():

        if m_is_stop:
            break

        if not m_is_live:
            time.sleep(0.5)
            m_buffer_time = time.time()
            continue

        ret, frame = m_cap.read()

        # if frame is read correctly ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        # keep last image
        m_now_image = frame;
 
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # update image
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        q_pixmap = QPixmap.fromImage(q_img)
    
        m_ui.LLImage.setPixmap(q_pixmap)

        m_now_frame_count+=1

        now_time = time.time()
        cost_time = now_time - m_buffer_time
        m_buffer_time = now_time

        m_average_frame_sec = (m_average_frame_sec * 4.0 + cost_time) / 5.0;

        fps = 1.0 / m_average_frame_sec
        time.sleep(0.00000030)
        msg = "fps {0:.2f}, frame {1}".format(fps, m_now_frame_count)
        m_ui.LLInfo.setText(msg);

    m_cap.release()

if __name__ == '__main__':

    global m_is_stop
    global m_is_live
    global m_cam_id
    global m_cap
    global m_now_frame_count
    global m_now_image

    global m_buffer_time
    global m_average_frame_sec

    print("Starting web CAM...")

    print("Connecting Camera...")

    # initial camera
    m_cam_id = 'http://192.168.50.224/html/cam_pic_new.php'
    m_cap = cv2.VideoCapture(m_cam_id)

    print("Camera connected!")

    # initial form
    m_app = QtWidgets.QApplication(sys.argv)
    m_main_win = QtWidgets.QMainWindow()
    m_ui = Ui_MainWindow()
    m_ui.setupUi(m_main_win) 

    # link event
    m_ui.BTNStart.clicked.connect(BTNStart_clicked)
    m_ui.BTNStop.clicked.connect(BTNStop_clicked)

    m_ui.BTNStart.setEnabled(True)
    m_ui.BTNStop.setEnabled(False)

    # show form
    m_main_win.show()

    # start live thread
    m_is_stop = False
    m_is_live = False
    thd_proc_live = threading.Thread(target=ProcessLive)
    thd_proc_live.start()

    m_app.exec_()

    print("Destroy...")

    m_is_stop = True
    m_is_live = False


