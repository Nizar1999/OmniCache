from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QMainWindow, QMessageBox, QLabel, QInputDialog, QFileDialog
import sys
from PyQt5.QtCore import QTimer
from pathlib import Path
import threading
from p2p_C import Node
from blockchain_C import bcNode
import subprocess
from gui import Ui_JoinNetwork, Ui_homepage,Ui_splashscreen, Ui_settings, Ui_loadingpage, Ui_Loginpage

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    #-----------------------------------------------------------------------
    def __init__(self, icon, parent=None):
    #-----------------------------------------------------------------------
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.setToolTip(f'OmniCache')
        menu = QtWidgets.QMenu(parent)  #Create a Qt widget with tray icon parent

        open_app = menu.addAction("Open OmniCache")  #Adding Open OmniCache in tray menu
        open_app.triggered.connect(self.open_omnicache)

        exit_ = menu.addAction("Exit")
        exit_.triggered.connect(lambda: sys.exit())  #Adding Exit in tray menu

        #Created an instance of Join Network UI and Homepage UI
        self.Homepage_UI = None

        menu.addSeparator()
        self.setContextMenu(menu)
        self.activated.connect(self.onTrayIconActivated)

    #-----------------------------------------------------------------------
    def onTrayIconActivated(self, reason):
    #-----------------------------------------------------------------------
        """
        This function will trigger function on click or double click
        :param reason:
        :return:
        """
        if reason == self.DoubleClick:
            self.open_omnicache()

    #On click open OmniCache in Tray
    #-----------------------------------------------------------------------
    def open_omnicache(self):
    #-----------------------------------------------------------------------

        #Opening Application
        self.Homepage_UI.show()

OmniCacheApp = QApplication(sys.argv)   #Create Qt Application
OmniCacheApp.setWindowIcon(QtGui.QIcon('./Images/taskbar_icon.png'))    #Setting Icon for top bar
QtGui.QFontDatabase.addApplicationFont("./Fonts/ProximaNova-Regular.otf")      #Adding fonts
QtGui.QFontDatabase.addApplicationFont("./Fonts/Aquire-BW0ox.otf")

SplashscreenUI = Ui_splashscreen()      #Create an instance of Splash screen UI

Join_Network_UI = Ui_JoinNetwork()      #Create an instance of Join Network UI
Settings_UI = None             #Create an instance of Settings UI
Loadingpage_UI = None
Homepage_UI = None


#Giving the system tray an icon and show()
tray_icon = SystemTrayIcon(QtGui.QIcon("./Images/currency_logo.png"), Homepage_UI)

#Enabling splash screen function to show
Ui_splashscreen.flashSplash(SplashscreenUI)

#Initializing Bc Node
bNode = bcNode("172.29.133.188")

#Initializing P2P Node
node = Node("172.29.133.188",4444,bNode, npeer=10)

#Onclick Listeners
Join_Network_UI.join_network_btn.clicked.connect(lambda: Join_Network_UI.join_network_btn_onclick(initNode()))   #Triggering Join network button
Join_Network_UI.ipaddress_input.returnPressed.connect(lambda: Join_Network_UI.join_network_btn_onclick(initNode()))    #Triggering Join network button (Enter pressed)

Loginpage_UI = Ui_Loginpage()

#If user never signed in on the machine
if not bNode.dataDirsExist():

    #Showing Join Network UI after 3s until splash screen is done
    QTimer.singleShot(2000, lambda: Loginpage_UI.showMaximized())
    Loginpage_UI.create_account_btn.clicked.connect(lambda: Loginpage_UI.showJoinNetwork(initPassPhrase(1)))    #Triggering create account button
    Loginpage_UI.import_account_btn.clicked.connect(lambda: Loginpage_UI.showJoinNetwork(initPassPhrase(2)))    #Triggering import account button

#If user is already signed in on the machine
else:
    if node.loadData():
        #Showing Join Network UI after 3s until splash screen is done
        QTimer.singleShot(2000, lambda: Join_Network_UI.showMaximized())


#Login page process
#-----------------------------------------------------------------------
def initPassPhrase(loginType):
#-----------------------------------------------------------------------
    global Loginpage_UI
    global Join_Network_UI
    global node
    global bNode

    #Create an account
    if loginType == 1:
        
        #passkey = QInputDialog.getText(Loginpage_UI, 'Pass Phrase', 'Enter your passphrase:')    #user password
        node.bNode.passPhrase = Loginpage_UI.keypass_input.text()
        if Loginpage_UI.keypass_input.text() != "":

            bNode.createAccount()
            return Join_Network_UI
        else:
            #Insert a message dialog
            return Loginpage_UI
    
    #Import an account
    elif loginType == 2:

        browseFile = QFileDialog()   # creating a File Dialog
        keyFilePath, _ = browseFile.getOpenFileName(Loginpage_UI,"Select File","",)   #Receiving a string from the file dialog

        #If user clicks open
        if keyFilePath != "":
            Loginpage_UI.file_path_lbl.setText(keyFilePath)
            passkey, ok = QInputDialog.getText(Loginpage_UI, 'Pass Phrase', 'Enter your KeyPhrase:', QtWidgets.QLineEdit.Password)   #user password
            
            if ok:      #if passkey dialog is ok
                node.bNode.passPhrase = passkey
                bNode.importAccount(Path(keyFilePath))

                return Join_Network_UI

            else:       #if passkey dialog is canceled
                Loginpage_UI.file_path_lbl.setText("")
                return Loginpage_UI

        #If user clicks cancel (Stay on login page)
        else:
            return Loginpage_UI
    

#Initiliazing node on Join network click
#-----------------------------------------------------------------------
def initNode():
#-----------------------------------------------------------------------
    global Loadingpage_UI
    global Homepage_UI
    global Settings_UI
    global node
    global bNode

    if  not node.bNode.exists:

        ip = Join_Network_UI.ipaddress_input.text()
        port = 4444
        thread=threading.Thread(target = node.connectionSpawner, args = [], daemon = True)
        thread.start()
        tosend='-'.join(["172.29.133.188",str(port)])
        node.connectAndSend(ip, port,'join', tosend, waitReply=False)
        Homepage_UI = Ui_homepage(node)    #Creating Homepage UI with node as arg
        Loadingpage_UI = Ui_loadingpage(node, Homepage_UI)
        Settings_UI = Ui_settings(node)
        
        tray_icon.show()
        HomepageListeners()

        return Loadingpage_UI

    else:

        if node.loadData():

            passkey = QInputDialog.getText(Loginpage_UI, 'Pass Phrase', 'Enter your KeyPhrase:', QtWidgets.QLineEdit.Password)
            node.bNode.passPhrase = passkey[0]

            ip = Join_Network_UI.ipaddress_input.text()
            port = 4444
            thread=threading.Thread(target = node.connectionSpawner, args = [], daemon = True)
            thread.start()
            tosend='-'.join([str(node.guid),"172.29.133.188",str(port)])
            node.connectAndSend(ip, port,'rjon', tosend, waitReply=False)
            Homepage_UI = Ui_homepage(node)    #Creating Homepage UI with node as arg
            Loadingpage_UI = Ui_loadingpage(node, Homepage_UI)
            Settings_UI = Ui_settings(node)

            tray_icon.show()
            HomepageListeners()

            return Loadingpage_UI

#Homepage on click listeners
#-----------------------------------------------------------------------
def HomepageListeners():
#-----------------------------------------------------------------------
    global Homepage_UI

    Homepage_UI.upload_btn.clicked.connect(lambda: Homepage_UI.upload_onclick())                             #Triggering Upload File button in Homepage
    Homepage_UI.settings_btn.clicked.connect(lambda: Homepage_UI.settings_onclick(Settings_UI,Homepage_UI))           #Triggering Settings button and passing Settings UI & Homepage UI as arg
    Homepage_UI.search_input.textChanged.connect(lambda: Homepage_UI.on_searchTextChanged(Homepage_UI.search_input.text()))            #On text changed in search input
    tray_icon.Homepage_UI = Homepage_UI

OmniCacheApp.exec_() #Executing app