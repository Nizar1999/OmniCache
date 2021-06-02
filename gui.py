import sys
import threading
import datetime
from pathlib import Path
import time
import subprocess
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QMainWindow, QMessageBox, QLabel, QFileDialog, QDesktopWidget, QInputDialog
from PyQt5.QtWidgets import QDialog, QPushButton, QVBoxLayout, QApplication, QSplashScreen, QGraphicsColorizeEffect,QListWidgetItem
import ntpath
import shutil
from p2p_C import Node
from blockchain_C import bcNode
import sys
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import QPoint, QTimer


#=========================================Threads===================================

#Fetch Files Task
class FetchFilesTasks(QtCore.QThread):

    #Task thread finished event
    finished = pyqtSignal(object)
    progress = pyqtSignal(object)

    #-----------------------------------------------------------------------
    def __init__(self, node, listwidget):
    #-----------------------------------------------------------------------
        QtCore.QThread.__init__(self)
        self.node = node
        self.listwidget = listwidget    #List instance from homepage in order to clear list.

    #When task thread starts
    #-----------------------------------------------------------------------
    def run(self):
    #-----------------------------------------------------------------------
        self.listwidget.clear()
        allFiles = self.node.bNode.filterByAddress()   #Dictionnary of files containing details
        for item in allFiles:
            
            self.progress.emit((item["fileName"], item["linkToOGF"], item["totalSize"]))

        #self.finished.emit()

#Download Task
class DownloadTask(QtCore.QThread):

    #Task thread finished event
    finished = pyqtSignal(object)

    #-----------------------------------------------------------------------
    def __init__(self, node, filename, linktoogf):
    #-----------------------------------------------------------------------
        QtCore.QThread.__init__(self)
        self.node = node
        self.filename = filename
        self.linktoogf = linktoogf

    #When task thread starts
    #-----------------------------------------------------------------------
    def run(self):
    #-----------------------------------------------------------------------
        self.node.downloadFile(self.filename, self.linktoogf)
        self.finished.emit(self.filename)

#Delete Task
class DeleteTask(QtCore.QThread):

    #Task thread finished event
    finished = pyqtSignal(object)

    #-----------------------------------------------------------------------
    def __init__(self, node, linktoogf):
    #-----------------------------------------------------------------------
        QtCore.QThread.__init__(self)
        self.node = node
        self.linktoogf = linktoogf

    #When task thread starts
    #-----------------------------------------------------------------------
    def run(self):
    #-----------------------------------------------------------------------
        self.node.bNode.logDeletion(self.linktoogf)
        self.finished.emit(None)


#Upload Task
class UploadTask(QtCore.QThread):

    #Task thread finished event
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    #-----------------------------------------------------------------------
    def __init__(self, node, filepath, progressbar):
    #-----------------------------------------------------------------------
        QtCore.QThread.__init__(self)
        self.node = node
        self.filepath = filepath
        self.progressbar = progressbar

    #When task thread starts
    #-----------------------------------------------------------------------
    def run(self):
    #-----------------------------------------------------------------------

        filename , linktoogf = self.node.sendChunks(self.filepath, self.progressbar)
        self.finished.emit()


#Node ready task
class NodeReady(QtCore.QThread):

    #Task thread finished event
    finished = pyqtSignal()

    #-----------------------------------------------------------------------
    def __init__(self, loadingUI, node, omniesLabel, hosting_value_label):
    #-----------------------------------------------------------------------
        QtCore.QThread.__init__(self)
        self.node = node
        self.omniesLabel = omniesLabel
        self.hostingLabel = hosting_value_label
        self.loadingUI = loadingUI

    #When task thread starts
    #-----------------------------------------------------------------------
    def run(self):
    #-----------------------------------------------------------------------
        while(not self.node.ready):    #Keep on checking node is ready to fetch files.
            time.sleep(1)
        self.node.bNode.postRunInit()
        while not self.node.bNode.validatePass():
            self.node.bNode.passPhrase = input("Incorrect KeyPhrase! Try again: ")
            
        tosend='-'.join([self.node.bNode.pubKey,self.node.bNode.enode])
        self.node.broadcast("adbn",tosend,-1)
        self.node.save()
        self.node.bNode.checkSyncStatus()
        self.node.bNode.enroll()
        self.node.startCleaning(self.omniesLabel, self.hostingLabel)
        self.finished.emit()


#=========================================GUIs===================================


#Splashscreen UI
class Ui_splashscreen(QDialog):
    #-----------------------------------------------------------------------
    def __init__(self, parent=None):
    #-----------------------------------------------------------------------
        super(Ui_splashscreen, self).__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

    #-----------------------------------------------------------------------
    def flashSplash(self):
    #-----------------------------------------------------------------------
        self.splash = QSplashScreen(QPixmap('./Images/joinnetwork_logo.png'))

        #By default, SplashScreen will be in the center of the screen.
        self.splash.show()

        #Close SplashScreen after 2 seconds (2000 ms)
        QTimer.singleShot(2000, self.splash.close)

#============================================================================

class Ui_Loginpage(QMainWindow):
    #-----------------------------------------------------------------------
    def __init__(self, parent=None):
    #-----------------------------------------------------------------------
        super().__init__(parent)
        self.setupUi(self)
    
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1377, 870)
        MainWindow.setStyleSheet("#centralwidget{background-image: url(./Images/joinnetwork_background.jpg)}\n"
                                 "QPushButton{background-color: rgb(0, 168, 243);}"
                                 "QPushButton::hover{background-color: rgb(30,144,255);}"
                                 )
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.omnicache_logo = QtWidgets.QLabel(self.centralwidget)
        self.omnicache_logo.setText("")
        self.omnicache_logo.setPixmap(QtGui.QPixmap("./Images/joinnetwork_logo.png"))
        self.omnicache_logo.setObjectName("omnicache_logo")
        self.horizontalLayout.addWidget(self.omnicache_logo, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalline_separator = QtWidgets.QFrame(self.centralwidget)
        self.verticalline_separator.setFrameShape(QtWidgets.QFrame.VLine)
        self.verticalline_separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.verticalline_separator.setObjectName("verticalline_separator")
        self.horizontalLayout.addWidget(self.verticalline_separator)
        spacerItem2 = QtWidgets.QSpacerItem(100, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.keypass_lbl = QtWidgets.QLabel(self.centralwidget)
        self.keypass_lbl.setStyleSheet("font: 14pt Proxima Nova;\n"
                                        "color: rgb(255, 255, 255);")
        self.keypass_lbl.setObjectName("keypass_lbl")
        self.horizontalLayout_2.addWidget(self.keypass_lbl, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.keypass_input = QtWidgets.QLineEdit(self.centralwidget)
        self.keypass_input.setStyleSheet("font: 10pt Proxima Nova;\n"
                                        "color: rgb(0, 0, 0);\n"
                                        "border: 0.5px solid grey;\n"
                                        "border-radius: 6px;")
        self.keypass_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.keypass_input.setFixedWidth(300)
        self.keypass_input.setObjectName("keypass_input")
        self.horizontalLayout_2.addWidget(self.keypass_input, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.create_account_btn = QtWidgets.QPushButton(self.centralwidget)
        self.create_account_btn.setStyleSheet("font: 10pt Proxima Nova;\n"
                                                "color: rgb(255, 255, 255);\n"
                                                "border-radius: 6px;\n"
                                                "padding: 10px;")
        self.create_account_btn.setObjectName("create_account_btn")
        self.horizontalLayout_2.addWidget(self.create_account_btn, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        spacerItem4 = QtWidgets.QSpacerItem(20, 80, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem4)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem5)
        self.path_lbl = QtWidgets.QLabel(self.centralwidget)
        self.path_lbl.setStyleSheet("font: 14pt Proxima Nova;\n"
                                        "color: rgb(255, 255, 255);")
        self.path_lbl.setObjectName("path_lbl")
        self.horizontalLayout_4.addWidget(self.path_lbl, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.file_path_lbl = QtWidgets.QLineEdit(self.centralwidget)
        self.file_path_lbl.setStyleSheet("font: 10pt Proxima Nova;\n"
                                        "color: rgb(0, 0, 0);\n"
                                        "border: 0.5px solid grey;\n"
                                        "border-radius: 6px;")
        self.file_path_lbl.setFixedWidth(300)
        self.file_path_lbl.setReadOnly(True)
        self.file_path_lbl.setObjectName("file_path_lbl")
        self.horizontalLayout_4.addWidget(self.file_path_lbl, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.import_account_btn = QtWidgets.QPushButton(self.centralwidget)
        self.import_account_btn.setStyleSheet("font: 10pt Proxima Nova;\n"
                                                "color: rgb(255, 255, 255);\n"
                                                "border-radius: 6px;\n"
                                                "padding: 10px;")
        self.import_account_btn.setObjectName("import_account_btn")
        self.horizontalLayout_4.addWidget(self.import_account_btn, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        spacerItem6 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem6)
        self.horizontalLayout.addLayout(self.verticalLayout)
        spacerItem7 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem7)
        self.horizontalLayout_3.addLayout(self.horizontalLayout)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    
    #Show Join netowrk after logging in
    #-----------------------------------------------------------------------
    def showJoinNetwork(self, ui):
    #-----------------------------------------------------------------------

        UI_Choice = isinstance(ui, Ui_JoinNetwork)   #checking type of UI

        #if user sent a file path with passkey
        if UI_Choice:
            ui.showMaximized()
            self.hide()
        #if user cancelled filedDialog, return login page again
        else:
            ui.showMaximized()
            
        
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "OmniCache"))
        self.keypass_lbl.setText(_translate("MainWindow", "Enter KeyPhrase:"))
        self.create_account_btn.setText(_translate("MainWindow", "Create Account"))
        self.path_lbl.setText(_translate("MainWindow", "KeyFile Path:"))
        self.import_account_btn.setText(_translate("MainWindow", "Import Account"))

#============================================================================


#Join Network UI
class Ui_JoinNetwork(QMainWindow):

    #Setup UI for the initial function
    #-----------------------------------------------------------------------
    def __init__(self, parent=None):
    #-----------------------------------------------------------------------
        super().__init__(parent)
        self.setupUi(self)

    #UI Design
    #-----------------------------------------------------------------------
    def setupUi(self, MainWindow):
    #-----------------------------------------------------------------------
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1128, 792)
        MainWindow.setStyleSheet("#centralwidget{background-image: url(./Images/joinnetwork_background.jpg)}\n"
                                 "QLineEdit{background-color: rgb(12,12,12);}"
                                 "QPushButton{background-color: rgb(0, 168, 243);}"
                                 "QPushButton::hover{background-color: rgb(30,144,255);}"
                                 )
        MainWindow.setAnimated(True)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("")
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        spacerItem = QtWidgets.QSpacerItem(20, 200, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout_4.addItem(spacerItem)
        self.logo_label = QtWidgets.QLabel(self.centralwidget)
        self.logo_label.setText("")
        self.logo_label.setPixmap(QtGui.QPixmap("./Images/joinnetwork_logo.png"))
        self.logo_label.setObjectName("logo_label")
        self.verticalLayout_4.addWidget(self.logo_label, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.horizontalLayout_1 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_1.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout_1.setSpacing(6)
        self.horizontalLayout_1.setObjectName("horizontalLayout_1")
        self.ipaddress_label = QtWidgets.QLabel(self.centralwidget)
        self.ipaddress_label.setStyleSheet("font: 14pt \"Proxima Nova\";\n"
                                           "color: rgb(255, 255, 255);")
        self.ipaddress_label.setObjectName("ipaddress_label")
        self.horizontalLayout_1.addWidget(self.ipaddress_label, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignBottom)
        self.ipaddress_input = QtWidgets.QLineEdit(self.centralwidget)
        self.ipaddress_input.setStyleSheet("font: 10pt \"Proxima Nova\";\n"
                                           "color: rgb(255, 255, 255);\n"
                                           "border: 0.5px solid grey;\n"
                                           "border-radius: 6px;\n"
                                           )
        self.ipaddress_input.setText("")
        self.ipaddress_input.setObjectName("ipaddress_input")

        #IP regex Validator
        IpAddressRegex = QtCore.QRegExp("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
        IPvalidator = QtGui.QRegExpValidator(IpAddressRegex)
        self.ipaddress_input.setValidator(IPvalidator)

        self.horizontalLayout_1.addWidget(self.ipaddress_input, 0, QtCore.Qt.AlignLeft|QtCore.Qt.AlignBottom)
        self.verticalLayout_4.addLayout(self.horizontalLayout_1)
        self.horizontalLayout_25 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_25.setObjectName("horizontalLayout_25")
        spacerItem1 = QtWidgets.QSpacerItem(20, 60, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.horizontalLayout_25.addItem(spacerItem1)
        self.verticalLayout_4.addLayout(self.horizontalLayout_25)
        self.join_network_btn = QtWidgets.QPushButton(self.centralwidget)
        self.join_network_btn.setStyleSheet("font: 10pt \"Proxima Nova\";\n"
                                            "color: rgb(255, 255, 255);\n"
                                            "border-radius: 6px;\n"
                                            "padding: 10px")
        self.join_network_btn.setObjectName("join_network_btn")
        self.verticalLayout_4.addWidget(self.join_network_btn, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        spacerItem2 = QtWidgets.QSpacerItem(20, 200, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout_4.addItem(spacerItem2)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)


    #On Click Join Network Button and passing UI in args
    #-----------------------------------------------------------------------
    def join_network_btn_onclick(self, loadingui):
    #-----------------------------------------------------------------------
        #To-do on clicking Join Network Button
        loadingui.showMaximized()
        self.hide()


    # Handling Close Window Button event
    #-----------------------------------------------------------------------
    def closeEvent(self, event):
    #-----------------------------------------------------------------------
        #Open dialog box asking to close the app
        close = QMessageBox.question(self,"Close application","Are you sure you want to close the application?", QMessageBox.Yes | QMessageBox.No)

        #If yes is clicked
        if close == QMessageBox.Yes:
            event.accept()   #App closed

        #If no is clicked
        else:
            event.ignore()   #App not closed


    #Renaming Labels, LineEdits, Buttons
    #-----------------------------------------------------------------------
    def retranslateUi(self, MainWindow):
    #-----------------------------------------------------------------------
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "OmniCache"))
        self.ipaddress_label.setText(_translate("MainWindow", "IP Address:"))
        self.ipaddress_input.setPlaceholderText(_translate("MainWindow", "Enter IP..."))
        self.join_network_btn.setText(_translate("MainWindow", "Join Network"))

#============================================================================

#Loading page UI
class Ui_loadingpage(QMainWindow):

    def __init__(self, node, Homepage_UI, parent=None):
    #-----------------------------------------------------------------------
        super().__init__(parent)
        self.setupUi(self)
        self.node = node
        self.Homepage_UI = Homepage_UI
        self.Loadingpage_UI = self
        self.threads = []
        self.readyup()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1042, 794)
        MainWindow.setStyleSheet("#centralwidget{background-image: url(./Images/joinnetwork_background.jpg)}")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.logo_animation = QtWidgets.QLabel(self.centralwidget)
        self.logo_animation.setText("")
        self.logo_animation.setObjectName("logo_animation")
        self.verticalLayout.addWidget(self.logo_animation, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        spacerItem1 = QtWidgets.QSpacerItem(20, 60, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem1)
        self.node_ready_lbl = QtWidgets.QLabel(self.centralwidget)
        self.node_ready_lbl.setStyleSheet("font: 32pt Proxima Nova;\n"
                                          "color: rgb(255, 255, 255);")
        self.node_ready_lbl.setObjectName("node_ready_lbl")
        self.verticalLayout.addWidget(self.node_ready_lbl, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
        MainWindow.setCentralWidget(self.centralwidget)

        self.gif = QMovie("./Images/loading_animation.gif")
        self.logo_animation.setMovie(self.gif)
        self.gif.start()

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "OmniCache"))
        self.node_ready_lbl.setText(_translate("MainWindow", "Initializing Subsystems.."))


    def readyup(self):

        nodeready = NodeReady(self.Loadingpage_UI, self.node, self.Homepage_UI.wallet_label, self.Homepage_UI.hosting_value_label)    #Creating a thread
        nodeready.finished.connect(self.showHomepage)    #After thread is finished
        self.threads.append(nodeready)
        nodeready.start()
    
    def showHomepage(self):
        self.Homepage_UI.showMaximized()
        self.Homepage_UI.fetchAllFiles()
        self.Homepage_UI.wallet_label.setText(str(self.node.bNode.getOmnies()))
        self.hide()


#============================================================================
        

#Item widget for list in homepage
class Ui_file_item(QWidget):

    #-----------------------------------------------------------------------
    def __init__(self, node, linktoogf, totalSize, task):
    #-----------------------------------------------------------------------
        QWidget.__init__(self)
        self.isEnabled = True
        self.node = node
        self.linktoogf = linktoogf
        self.totalSize = totalSize
        self.threads = []      #list of threads for item in list
        self.task = task
        self.setupUi(self)
 

    #-----------------------------------------------------------------------
    def setupUi(self, file_item):
    #-----------------------------------------------------------------------
        file_item.setObjectName("file_item")
        file_item.resize(232, 48)
        self.horizontalLayout = QtWidgets.QHBoxLayout(file_item)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(file_item)
        self.label.setObjectName("label")
        self.label.setStyleSheet("font: 14pt \"Proxima Nova\";\n"
                                 "color: rgb(255, 255, 255);")
        self.horizontalLayout.addWidget(self.label, 0, QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.download_btn = QtWidgets.QPushButton(file_item)
        self.download_btn.setStyleSheet("border: 0")
        self.download_btn.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./Images/download_button.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.download_btn.setIcon(icon)
        self.download_btn.setObjectName("download_btn")
        self.horizontalLayout.addWidget(self.download_btn, 0, QtCore.Qt.AlignLeft)
        self.delete_btn = QtWidgets.QPushButton(file_item)
        self.delete_btn.setStyleSheet("border:0")
        self.delete_btn.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("./Images/trash_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.delete_btn.setIcon(icon1)
        self.delete_btn.setObjectName("Delete Button")
        self.horizontalLayout.addWidget(self.delete_btn, 0, QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)

        self.retranslateUi(file_item)
        QtCore.QMetaObject.connectSlotsByName(file_item)

        self.download_btn.clicked.connect(lambda: self.download_btn_onClick(self.node, self.linktoogf))
        self.delete_btn.clicked.connect(lambda: self.delete_btn_onClick(self.linktoogf))

    #File download button on-click
    #-----------------------------------------------------------------------
    def download_btn_onClick(self, node, linktoogf):
    #-----------------------------------------------------------------------  
        downloadtask = DownloadTask(node, self.label.text(), linktoogf)    #Creating a thread
        downloadtask.finished.connect(self.showdialog)    #After thread is finished
        self.threads.append(downloadtask)
        downloadtask.start()      #Start thread

    #Show Dialog Information
    #-----------------------------------------------------------------------
    def showdialog(self, filename):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText(filename + " downloaded successfully.")
        msg.setWindowTitle("Information")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()


    #File delete button on-click
    #-----------------------------------------------------------------------
    def delete_btn_onClick(self, linktoogf):
    #-----------------------------------------------------------------------  
        deletetask = DeleteTask(self.node, linktoogf)    #Creating a thread
        deletetask.finished.connect(self.runfetchtask)    #After delete thread is finished, running fetching files task
        self.threads.append(deletetask)
        deletetask.start()       #Start thread


    #Fetching files and adding to list
    #-----------------------------------------------------------------------
    def runfetchtask(self):
    #-----------------------------------------------------------------------
        self.threads.append(self.task)
        self.task.start()


    #-----------------------------------------------------------------------
    def retranslateUi(self, file_item):
    #-----------------------------------------------------------------------
        _translate = QtCore.QCoreApplication.translate
        file_item.setWindowTitle(_translate("file_item", "Form"))
        self.label.setText(_translate("file_item", "Text Label"))


#============================================================================

#============================================================================
        

#Item widget for list in homepage
class Ui_file_item_disabled(QWidget):

    #-----------------------------------------------------------------------
    def __init__(self):
    #-----------------------------------------------------------------------
        QWidget.__init__(self)
        self.setupUi(self)
         

    #-----------------------------------------------------------------------
    def setupUi(self, file_item):
    #-----------------------------------------------------------------------
        file_item.setObjectName("file_item")
        file_item.resize(232, 48)
        self.horizontalLayout = QtWidgets.QHBoxLayout(file_item)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(file_item)
        self.label.setObjectName("label")
        self.label.setStyleSheet("font: 14pt \"Proxima Nova\";\n"
                                 "color: rgb(0, 168, 243);")
        self.horizontalLayout.addWidget(self.label, 0, QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.download_btn = QtWidgets.QPushButton(file_item)
        self.download_btn.setStyleSheet("border: 0")
        self.download_btn.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./Images/download_button.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.download_btn.setIcon(icon)
        self.download_btn.setObjectName("download_btn")
        self.horizontalLayout.addWidget(self.download_btn, 0, QtCore.Qt.AlignLeft)
        self.delete_btn = QtWidgets.QPushButton(file_item)
        self.delete_btn.setStyleSheet("border:0")
        self.delete_btn.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("./Images/trash_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.delete_btn.setIcon(icon1)
        self.delete_btn.setObjectName("Delete Button")
        self.horizontalLayout.addWidget(self.delete_btn, 0, QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)

        self.retranslateUi(file_item)
        QtCore.QMetaObject.connectSlotsByName(file_item)

    #-----------------------------------------------------------------------
    def retranslateUi(self, file_item):
    #-----------------------------------------------------------------------
        _translate = QtCore.QCoreApplication.translate
        file_item.setWindowTitle(_translate("file_item", "Form"))
        self.label.setText(_translate("file_item", "Text Label"))


#============================================================================


#Homepage UI
class Ui_homepage(QMainWindow):

    #Setup UI for the initial function
    #-----------------------------------------------------------------------
    def __init__(self, node, parent=None):
    #-----------------------------------------------------------------------
        super(Ui_homepage, self).__init__(parent)
        self.setupUi(self)
        self.threads = []
        self.node = node
        self.customWidgetList = []

        #Thread for fetching files on startup
        """ nodeready = NodeReady(self.node)    #Creating a thread
        nodeready.finished.connect(self.fetchAllFiles)    #After thread is finished
        self.threads.append(nodeready)
        nodeready.start() """


    #UI Design
    #-----------------------------------------------------------------------
    def setupUi(self, MainWindow):
    #-----------------------------------------------------------------------
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1188, 886)
        MainWindow.setStyleSheet("#centralwidget{background-color: rgb(12, 12, 12);}\n"
                                 "QLineEdit{background-color: rgb(12,12,12);}"
                                 "QListWidget{background-color: rgb(12,12,12);}"
                                 "QPushButton#upload_btn{background-color: rgb(0, 168, 243);}\n"
                                 "QPushButton#upload_btn:hover{background-color: rgb(30,144,255);}"
                                 )
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.hp_logo = QtWidgets.QLabel(self.centralwidget)
        self.hp_logo.setText("")
        self.hp_logo.setPixmap(QtGui.QPixmap("./Images/homepage_logo.png"))
        self.hp_logo.setObjectName("hp_logo")
        self.horizontalLayout.addWidget(self.hp_logo, 0, QtCore.Qt.AlignVCenter)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.settings_btn = QtWidgets.QPushButton(self.centralwidget)
        self.settings_btn.setStyleSheet("border: 0")
        self.settings_btn.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./Images/settings_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.settings_btn.setIcon(icon)
        self.settings_btn.setIconSize(QtCore.QSize(25, 25))
        self.settings_btn.setObjectName("settings_btn")
        self.verticalLayout_2.addWidget(self.settings_btn, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignBottom)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setContentsMargins(-1, -1, 0, -1)
        self.horizontalLayout_9.setSpacing(0)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem)
        self.wallet_label = QtWidgets.QLabel(self.centralwidget)
        self.wallet_label.setStyleSheet("font: 14pt \"Proxima Nova\";\n"
                                        "color: rgb(255, 255, 255);\n"
                                        "margin-right:0 px;")
        self.wallet_label.setObjectName("wallet_label")
        self.horizontalLayout_9.addWidget(self.wallet_label, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignBottom)
        self.wallet_logo = QtWidgets.QLabel(self.centralwidget)
        self.wallet_logo.setText("")
        self.wallet_logo.setPixmap(QtGui.QPixmap("./Images/currency_logo.png"))
        self.wallet_logo.setObjectName("wallet_logo")
        self.horizontalLayout_9.addWidget(self.wallet_logo)
        self.verticalLayout_2.addLayout(self.horizontalLayout_9)
        self.hosting_value_label = QtWidgets.QLabel(self.centralwidget)
        self.hosting_value_label.setStyleSheet("font: 14pt \"Proxima Nova\";\n"
                                                "color: rgb(255, 255, 255);")
        self.hosting_value_label.setObjectName("hosting_value_label")
        self.verticalLayout_2.addWidget(self.hosting_value_label, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignTop)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setStyleSheet("background-color: rgb(0, 168, 243);")
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.mystash_icon = QtWidgets.QLabel(self.centralwidget)
        self.mystash_icon.setStyleSheet("")
        self.mystash_icon.setText("")
        self.mystash_icon.setPixmap(QtGui.QPixmap("./Images/mystash.png"))
        self.mystash_icon.setObjectName("mystash_icon")
        self.horizontalLayout_2.addWidget(self.mystash_icon, 0, QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.mystash_label = QtWidgets.QLabel(self.centralwidget)
        self.mystash_label.setStyleSheet("font: 14pt \"Aquire\";\n"
                                        "color: rgb(255, 255, 255);")
        self.mystash_label.setObjectName("mystash_label")
        self.horizontalLayout_2.addWidget(self.mystash_label, 0, QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.search_icon = QtWidgets.QLabel(self.centralwidget)
        self.search_icon.setText("")
        self.search_icon.setPixmap(QtGui.QPixmap("./Images/search_icon.png"))
        self.search_icon.setObjectName("search_icon")
        self.horizontalLayout_2.addWidget(self.search_icon, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.search_input = QtWidgets.QLineEdit(self.centralwidget)
        self.search_input.setStyleSheet("font: 10pt \"Proxima Nova\";\n"
                                        "color: rgb(255, 255, 255);\n"
                                        "border: 0.5px solid grey;\n"
                                        "border-radius: 6px;\n"
                                        "")
        self.search_input.setText("")
        self.search_input.setObjectName("search_input")
        self.horizontalLayout_2.addWidget(self.search_input, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        spacerItem2 = QtWidgets.QSpacerItem(30, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.upload_btn = QtWidgets.QPushButton(self.centralwidget)
        self.upload_btn.setStyleSheet("font: 10pt \"Proxima Nova\";\n"
                                        "background-color: rgb(0, 168, 243);\n"
                                        "color: rgb(255, 255, 255);\n"
                                        "border-radius: 6px;\n"
                                        "padding:3px;")
        self.upload_btn.setObjectName("upload_btn")
        self.horizontalLayout_2.addWidget(self.upload_btn, 0, QtCore.Qt.AlignRight)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.listWidget = QtWidgets.QListWidget(self.centralwidget)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)
        self.listWidget.verticalScrollBar().setStyleSheet("QScrollBar:vertical{background:#000000;}")
        self.filedetails_label = QtWidgets.QLabel(self.centralwidget)
        self.filedetails_label.setStyleSheet("font: 14pt \"Proxima Nova\";\n"
                                                "color: rgb(255, 255, 255);")
        self.filedetails_label.setObjectName("filedetails_label")
        self.verticalLayout.addWidget(self.filedetails_label)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.progress_label = QtWidgets.QLabel(self.centralwidget)
        self.progress_label.setMouseTracking(False)
        self.progress_label.setStyleSheet("font: 10pt \"Proxima Nova\";\n"
                                        "color: rgb(255, 255, 255);")
        self.progress_label.setObjectName("progress_label")
        self.horizontalLayout_8.addWidget(self.progress_label)
        self.progress_bar = QtWidgets.QProgressBar(self.centralwidget)
        self.progress_bar.setStyleSheet("font: 10pt \"Proxima Nova\";\n"
                                        "color: rgb(255, 255, 255);")
        self.progress_bar.setProperty("value", 0)
        self.progress_bar.setOrientation(QtCore.Qt.Horizontal)
        self.progress_bar.setObjectName("progress_bar")
        self.horizontalLayout_8.addWidget(self.progress_bar)
        self.verticalLayout.addLayout(self.horizontalLayout_8)
        spacerItem3 = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem3)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.fd_name_label = QtWidgets.QLabel(self.centralwidget)
        self.fd_name_label.setMouseTracking(False)
        self.fd_name_label.setStyleSheet("font: 12pt \"Proxima Nova\";\n"
                                        "color: rgb(255, 255, 255);")
        self.fd_name_label.setObjectName("fd_name_label")
        self.horizontalLayout_3.addWidget(self.fd_name_label)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.fd_size_label = QtWidgets.QLabel(self.centralwidget)
        self.fd_size_label.setMouseTracking(False)
        self.fd_size_label.setStyleSheet("font: 12pt \"Proxima Nova\";\n"
                                        "color: rgb(255, 255, 255);")
        self.fd_size_label.setObjectName("fd_size_label")
        self.horizontalLayout_6.addWidget(self.fd_size_label)
        self.verticalLayout.addLayout(self.horizontalLayout_6)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1188, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.listWidget.itemSelectionChanged.connect(lambda: self.on_item_selection_changed())
        

    def on_item_selection_changed(self):

        selection = self.listWidget.currentIndex()
        widgetType = isinstance(self.customWidgetList[selection.row()], Ui_file_item)
        if widgetType:
            file_name = self.customWidgetList[selection.row()].label.text()
            totalSize = self.customWidgetList[selection.row()].totalSize

            #File unit converter
            postFixList = ["KB", "MB", "GB", "TB"]
            postFix = "B"
            count = 0
            while(totalSize >= 1024):
                postFix = postFixList[count]
                count += 1
                totalSize /= 1024

            self.fd_name_label.setText("Name: " + file_name)
            self.fd_size_label.setText("Size: " + "{:.3f}".format(totalSize) + " " + postFix)

    
    #Search query for listview
    #-----------------------------------------------------------------------
    def on_searchTextChanged(self, search_query):
    #-----------------------------------------------------------------------
        for row in range(self.listWidget.count()):
            item = self.listWidget.item(row)
            widget = self.listWidget.itemWidget(item)

            if search_query:
                item.setHidden(not self.filter(search_query, widget.label.text()))
            else:
                item.setHidden(True)

        if self.search_input.text() == "":
            for row in range(self.listWidget.count()):
                item = self.listWidget.item(row)
                item.setHidden(False)


    def filter(self, text, keywords):
        
        return text in keywords

    #On-Click Settings Button
    #-----------------------------------------------------------------------
    def settings_onclick(self,ui,ui1):
    #-----------------------------------------------------------------------
        ui.show()    #Showing Settings UI
        ui1.setWindowOpacity(0.9)    #Homepage UI on 0.9 opacity in the background


    #Fetching files and adding to list
    #-----------------------------------------------------------------------
    def fetchAllFiles(self):
    #-----------------------------------------------------------------------
        self.listWidget.clear()
        self.customWidgetList.clear()
        fetchfilestask = FetchFilesTasks(self.node, self.listWidget)
        fetchfilestask.progress.connect(self.addItemtoList)
        self.threads.append(fetchfilestask)
        fetchfilestask.start()
   

    #On-Click Upload Button
    #-----------------------------------------------------------------------
    def upload_onclick(self):
    #-----------------------------------------------------------------------
        #To-do on clicking Upload Button
        
        #Open file dialog
        filename = ""
        browseFile = QFileDialog()   # creating a File Dialog
        filename = browseFile.getOpenFileName(self,"Select File","",)   #Receiving a string from the file dialog
        ntpath.basename("a/b/c")  
        head, tail = ntpath.split(filename[0])

        #if cancel is clicked
        if filename[0] == "":

            pass

        else:

            #Adding a dummy file item in list just while uploading
            myQCustomQWidget = Ui_file_item_disabled()
            myQCustomQWidget.label.setText(tail)
            self.customWidgetList.append(myQCustomQWidget)
            myQListWidgetItem = QListWidgetItem(self.listWidget)
            myQListWidgetItem.setSizeHint(myQCustomQWidget.sizeHint())
            self.listWidget.addItem(myQListWidgetItem)
            self.listWidget.setItemWidget(myQListWidgetItem, myQCustomQWidget)


            uploadtask = UploadTask(self.node, Path(filename[0]), self.progress_bar)    #Creating a thread
            uploadtask.finished.connect(self.fetchAllFiles)    #After thread is finished
            self.threads.append(uploadtask)
            uploadtask.start()

    #-----------------------------------------------------------------------    
    def addItemtoList(self, fileinfo):
    #-----------------------------------------------------------------------
        # If filedialog open is clicked
        if fileinfo[0] != "":
            #Adding an item to the QListWidget
            fetchfilestask = FetchFilesTasks(self.node, self.listWidget)    #Creating an instance of fetch files task and sending it to each item in the list
            fetchfilestask.progress.connect(self.addItemtoList)   #Adding item to list after fetching files task
            myQCustomQWidget = Ui_file_item(self.node, fileinfo[1], fileinfo[2], fetchfilestask)    #Creating a file item widget params(ogf,totalsize, fetchfiles task(after each item))
            myQCustomQWidget.label.setText(fileinfo[0])
            self.customWidgetList.append(myQCustomQWidget)
            myQListWidgetItem = QListWidgetItem(self.listWidget)
            myQListWidgetItem.setSizeHint(myQCustomQWidget.sizeHint())
            self.listWidget.addItem(myQListWidgetItem)
            self.listWidget.setItemWidget(myQListWidgetItem,myQCustomQWidget)

        self.wallet_label.setText(str(self.node.bNode.getOmnies()))

    #Handling Close Window Button event in Homepage
    #-----------------------------------------------------------------------
    def closeEvent(self, event):
    #-----------------------------------------------------------------------

        #Open dialog box asking to minimize tray or close app
        close = QMessageBox.question(self,"System Tray","Do you want the program to minimize to tray?", QMessageBox.Yes | QMessageBox.No)

        #If yes is clicked
        if close == QMessageBox.Yes:
            event.ignore()    #App not closed
            self.hide()    #UI hidden

        #If no is clicked
        else:
            
            event.accept() #App closed
            self.node.bNode.proc.kill()
            sys.exit()
    
    #If mouse is clicked on the Homepage UI window
    #-----------------------------------------------------------------------
    def enterEvent(self, event):
    #-----------------------------------------------------------------------
        self.setWindowOpacity(1)   # Return windows opacity to 1 after closing settings
        return super(Ui_homepage, self).enterEvent(event)


    #Renaming Labels, LineEdits, Buttons
    #-----------------------------------------------------------------------
    def retranslateUi(self, MainWindow):
    #-----------------------------------------------------------------------
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "OmniCache"))
        self.wallet_label.setText(_translate("MainWindow", "0"))
        self.hosting_value_label.setText(_translate("MainWindow", "Hosting: 0.000 B"))
        self.mystash_label.setText(_translate("MainWindow", "My Stash"))
        self.search_input.setPlaceholderText(_translate("MainWindow", "Search..."))
        self.upload_btn.setText(_translate("MainWindow", "Upload file"))
        self.filedetails_label.setText(_translate("MainWindow", "File Details:"))
        self.progress_label.setText(_translate("MainWindow", "Progress:"))
        self.progress_bar.setFormat(_translate("MainWindow", "%p%"))
        self.fd_name_label.setText(_translate("MainWindow", "Name:"))
        self.fd_size_label.setText(_translate("MainWindow", "Size:"))


#============================================================================

#Settins UI
class Ui_settings(QMainWindow):

    #Setup UI for the initial function
    #-----------------------------------------------------------------------
    def __init__(self, node, parent=None):
    #-----------------------------------------------------------------------
        super(Ui_settings, self).__init__(parent)
        self.node = node
        self.setupUi(self)
        
    #-----------------------------------------------------------------------
    def setupUi(self, MainWindow):
    #-----------------------------------------------------------------------
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(529, 544)
        MainWindow.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        MainWindow.setStyleSheet("QWidget#centralwidget{background-color: rgb(35,35,35); border: 1px solid black;}"
                                 "QPushButton{background-color: rgb(0, 168, 243);}"
                                 "QPushButton::hover{background-color: rgb(30,144,255);}")

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Popup)  #Set the window frameless and as a popup(clicking outside closes window)

        #Centering settings window on the screen
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("border-radius:40px;")
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setStyleSheet("font: 20pt \"Proxima Nova\";\n"
                                "color: rgb(255, 255, 255);\n"
                                "margin-top: 20px;")
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.replication_lbl = QtWidgets.QLabel(self.centralwidget)
        self.replication_lbl.setStyleSheet("font: 14pt Proxima Nova;\n"
                                            "color: rgb(255, 255, 255);")
        self.replication_lbl.setObjectName("replication_lbl")
        self.horizontalLayout.addWidget(self.replication_lbl, 0, QtCore.Qt.AlignRight)
        self.replication_dropdown = QtWidgets.QComboBox(self.centralwidget)
        self.replication_dropdown.setStyleSheet("font: 10pt Proxima Nova;\n"
                                                "border: 0.5px solid grey;\\n\"\n"
                                                "border-radius: 6px;"
                                                "width:15px;")
        """ self.replication_dropdown.setFixed(40) """
        self.replication_dropdown.addItems(["1","2","3"])
        self.replication_dropdown.setObjectName("comboBox")
        self.horizontalLayout.addWidget(self.replication_dropdown, 0, QtCore.Qt.AlignLeft)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.export_btn = QtWidgets.QPushButton(self.centralwidget)
        self.export_btn.setStyleSheet("font: 10pt \"Proxima Nova\";\n"
                                        "color: rgb(255, 255, 255);\n"
                                        "border-radius: 6px;\n"
                                        "padding: 10px;\n"
                                        "margin-top:10px;\n"
                                        "width:150px;")
        self.export_btn.setObjectName("export_btn")
        self.verticalLayout.addWidget(self.export_btn, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.pushButton_3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_3.setStyleSheet("font: 10pt \"Proxima Nova\";\n"
                                        "color: rgb(255, 255, 255);\n"
                                        "border-radius: 6px;\n"
                                        "padding: 10px;\n"
                                        "margin-top:10px;\n"
                                        "width:150px;")
        self.pushButton_3.setObjectName("pushButton_3")
        self.verticalLayout.addWidget(self.pushButton_3, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.pushButton_4 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_4.setStyleSheet("font: 10pt \"Proxima Nova\";\n"
                                        "color: rgb(255, 255, 255);\n"
                                        "border-radius: 6px;\n"
                                        "padding: 10px;\n"
                                        "margin-top:10px;\n"
                                        "width:150px;")
        self.pushButton_4.setObjectName("pushButton_4")
        self.verticalLayout.addWidget(self.pushButton_4, 0, QtCore.Qt.AlignHCenter)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem3)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.replication_dropdown.activated[str].connect(self.on_replication_changed)

        self.export_btn.clicked.connect(self.export_onclick)

    #On replication factor dropdown change
    #-----------------------------------------------------------------------
    def on_replication_changed(self, replicationText):
    #-----------------------------------------------------------------------

        if replicationText == "1":
            self.node.replicationFactor = 1
            print(self.node.replicationFactor)

        elif replicationText == "2":
            self.node.replicationFactor = 2
            print(self.node.replicationFactor)
        else:
            self.node.replicationFactor = 3
            print(self.node.replicationFactor)
    #On export click
    #-----------------------------------------------------------------------
    def export_onclick(self):
    #-----------------------------------------------------------------------

        source = r'./ETH/node/keystore'
        browseFile = QFileDialog()   # creating a File Dialog
        destination = browseFile.getExistingDirectory(self,"Select Destination","",)   #Receiving a string from the file dialog

        if destination == "":
            pass

        else:
            print(destination)
            shutil.copytree(source, destination, dirs_exist_ok=True)


    #Renaming Labels, LineEdits, Buttons
    #-----------------------------------------------------------------------
    def retranslateUi(self, MainWindow):
    #-----------------------------------------------------------------------
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "Settings"))
        self.replication_lbl.setText(_translate("MainWindow", "Replication Factor"))
        self.export_btn.setText(_translate("MainWindow", "Export Account"))
        self.pushButton_3.setText(_translate("MainWindow", "PushButton"))
        self.pushButton_4.setText(_translate("MainWindow", "PushButton"))