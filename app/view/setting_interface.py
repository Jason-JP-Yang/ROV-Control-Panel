# coding:utf-8
from typing import Union
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard, SettingCard, ExpandGroupSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, TitleLabel, CustomColorSettingCard,
                            setTheme, setThemeColor, MessageBox, isDarkTheme, 
                            FluentIconBase, LineEdit, qconfig, PrimaryPushButton, PushButton,
                            IndeterminateProgressBar, MessageBoxBase, InfoBarPosition,
                            SubtitleLabel, CaptionLabel, BodyLabel, SpinBox, PasswordLineEdit,
                            CheckBox, SwitchButton, ComboBox)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QPoint, QEventLoop, QTimer, pyqtSlot
from PyQt5.QtGui import QDesktopServices, QIcon, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QFileDialog, QHBoxLayout, QPushButton, QVBoxLayout, QSizePolicy

from ..common.config import Config, cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR, RELEASE_URL, isWin11
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet

import paramiko, socket, time
from datetime import datetime
from paramiko import SSHException, AuthenticationException

import threading
import functools

def threaded_func(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread  # 如果需要返回线程对象，可以返回它，否则可以选择不返回
    return wrapper


class CustomSSHSettingCard(ExpandGroupSettingCard):
    sshUpdated = pyqtSignal(bool)
    
    def __init__(self, configItems: Config, icon: Union[str, QIcon, FluentIconBase], title: str,
                 content=None, parent=None):
        super().__init__(icon, title, content, parent=parent)
        self.configItems = configItems
        self.configSsh = configItems.sshAddress
        self.configPort = configItems.sshPort
        self.configUsername = configItems.sshUser
        self.configPassword = configItems.sshPassword
        self.connectionStatus = "Unknown"
        self.sshMessage = "NONE"

        self.Widget = QWidget(self.view)
        self.Layout = QHBoxLayout(self.Widget)
        self.leftLayout = QVBoxLayout(self.Widget)
        self.rightLayout = QVBoxLayout(self.Widget)

        self.editButton = PushButton(
            self.tr('Edit Settings'), self.Widget)
        self.sshLinkLabel = QLabel(self.Widget)
        self.sshPort = QLabel(self.Widget)
        self.sshUserLabel = QLabel(self.Widget)
        self.passwordLabel = QLabel(self.Widget)
        self.editButton.clicked.connect(self.showSSHSettingsBox)

        self.checkWidget = QWidget(self.view)
        self.checkLayout = QHBoxLayout(self.checkWidget)
        self.checkingBar = IndeterminateProgressBar(self.checkWidget)
        self.checkLabel = QLabel(self.checkWidget)
        self.detailButton = PushButton(
            self.tr('View Details'), self.checkWidget)
        self.checkButton = PrimaryPushButton(
            self.tr("Check SSH Connection"), self.checkWidget)
        self.checkButton.clicked.connect(self.updateSSHStatus)
        self.detailButton.clicked.connect(self.showSSHDetail)

        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()
        
        self.sshLinkLabel.setObjectName("titleLabel")
        self.sshPort.setObjectName("titleLabel")
        self.sshUserLabel.setObjectName("titleLabel")
        self.passwordLabel.setObjectName("titleLabel")
        self.checkLabel.setObjectName("titleLabel")
        self.__updateLabel()

        self.updateSSHStatus(init=True)
    
    def __initLayout(self):
        self.Layout.setAlignment(Qt.AlignTop)
        self.Layout.setContentsMargins(48, 18, 44, 18)
        
        self.leftLayout.addWidget(self.sshLinkLabel, 0, Qt.AlignLeft)
        self.leftLayout.addWidget(self.sshPort, 0, Qt.AlignLeft)
        self.leftLayout.addWidget(self.sshUserLabel, 0, Qt.AlignLeft)
        self.leftLayout.addWidget(self.passwordLabel, 0, Qt.AlignLeft)

        self.rightLayout.addWidget(self.editButton, 0, Qt.AlignRight | Qt.AlignTop)
        
        self.Layout.addLayout(self.leftLayout, 0)
        self.Layout.addLayout(self.rightLayout, 0)
        self.Layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.checkLayout.setContentsMargins(48, 18, 44, 18)
        self.checkLayout.addWidget(self.checkLabel, 0, Qt.AlignLeft)
        self.checkLayout.addWidget(self.checkingBar, 0, Qt.AlignLeft)
        self.checkLayout.addStretch()
        self.checkLayout.addWidget(self.detailButton, 0, Qt.AlignRight)
        self.checkLayout.addWidget(self.checkButton, 0, Qt.AlignRight)
        self.checkLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.Widget)
        self.addGroupWidget(self.checkWidget)
    
    def __updateLabel(self):
        self.sshLinkLabel.setText(self.tr("SSH Connection Link: ") + qconfig.get(self.configSsh))
        self.sshPort.setText(self.tr("SSH Connection Port: ") + str(qconfig.get(self.configPort)))
        self.sshUserLabel.setText(self.tr("SSH Username: ") + qconfig.get(self.configUsername))
        self.passwordLabel.setText(self.tr("SSH Password: ") + qconfig.get(self.configPassword))
        
        self.sshLinkLabel.adjustSize()
        self.sshPort.adjustSize()
        self.sshUserLabel.adjustSize()
        self.passwordLabel.adjustSize()

    def __checkSSHConnection(self):
        """
        测试 SSH 连接

        :param hostname: SSH 服务器的主机名或 IP 地址
        :param port: SSH 端口号，默认为 22
        :param username: SSH 用户名
        :param password: SSH 密码
        :return: (success, message) 其中 success 是布尔值，表示连接是否成功；message 是状态信息
        """
        client = paramiko.SSHClient()
        # 自动添加未知的主机密钥，避免提示
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        config = " \nConfig: [SSH Address: {0}, SSH Port: {1}, Username: {2}, Passowrd: {3}]".format(
            qconfig.get(self.configSsh), qconfig.get(self.configPort),
            qconfig.get(self.configUsername), qconfig.get(self.configPassword))
        utctime = datetime.now()
        utctimeconfig = " \nCheck Connection at {0}; {1}".format(
            utctime, utctime.timestamp())
        try:
            # 尝试连接 SSH 服务器
            client.connect(
                qconfig.get(self.configSsh), port=qconfig.get(self.configPort), 
                username=qconfig.get(self.configUsername), password=qconfig.get(self.configPassword), timeout=5)
            # 如果连接成功，返回成功信息
            return "Success", self.tr("SSH Connection Status: Success!") + config + utctimeconfig
                
        except AuthenticationException:
            # 认证失败
            return "Failed", self.tr("SSH Connection Failed: Authentication Failed, Asscess Denied") +\
                   config + utctimeconfig
        except SSHException as e:
            # 其他 SSH 错误
            return "Failed", self.tr("SSH Connection Failed: ") + e + config + utctimeconfig
        except socket.error as e:
            # 网络错误
            return "Failed", self.tr("Network Connection Failed: Please check your Internet ") \
                + f"({e})" + config + utctimeconfig
        finally:
            # 确保连接关闭
            client.close()

    @pyqtSlot()
    @threaded_func
    def updateSSHStatus(self, init: bool = False):
        if self.connectionStatus == "Checking": 
            self.sshUpdated.emit(init)
            return
        
        start_time = time.time()
        self.connectionStatus = "Checking"
        self.checkButton.setEnabled(False)
        self.detailButton.setEnabled(False)
        self.checkLabel.setText(self.tr("Checking Connection: "))
        self.checkLabel.adjustSize()
        self.checkingBar.show()

        self.connectionStatus, self.sshMessage = self.__checkSSHConnection()
        print(self.connectionStatus, self.sshMessage)
        
        # 延时
        loop = QEventLoop()
        QTimer.singleShot(int(max((1 - time.time() + start_time) * 1000, 0)), loop.quit)
        loop.exec_()

        self.checkingBar.hide()
        self.checkLabel.setText(self.tr("Connection Status: ") + self.connectionStatus)
        # self.checkLabel.setText(message)
        self.checkButton.setEnabled(True)
        self.detailButton.setEnabled(True)
        self._adjustViewSize()

        self.sshUpdated.emit(init)
    
    def showSSHDetail(self):
        w = MessageBox(self.tr("SSH Connection Status: ") + self.connectionStatus, 
                       self.sshMessage, self.window())
        w.show()

    def showSSHSettingsBox(self):
        w = sshSettingBox(self.configItems, self.window())
        w.show()
        if w.exec():
            print(w.sshAddressEdit.text(), w.sshPortEdit.text(), w.sshUserEdit.text(), w.sshPasswordEdit.text(), w.autoCheckPicker.isChecked())
            qconfig.set(self.configSsh, w.sshAddressEdit.text())
            qconfig.set(self.configPort, w.sshPortEdit.text())
            qconfig.set(self.configUsername, w.sshUserEdit.text())
            qconfig.set(self.configPassword, w.sshPasswordEdit.text())

            self.__updateLabel()

            if w.autoCheckPicker.isChecked():
                self.updateSSHStatus()

    def toggleExpand(self):
        """ toggle expand status """
        self.setExpand(not self.isExpand)
        self._adjustViewSize()

class sshSettingBox(MessageBoxBase):
    def __init__(self, configItems: Config, parent=None):
        super().__init__(parent)
        self.configSsh = configItems.sshAddress
        self.configPort = configItems.sshPort
        self.configUsername = configItems.sshUser
        self.configPassword = configItems.sshPassword
        
        self.titleLabel = SubtitleLabel(self.tr('SSH Connection Settings'), self)
        
        self.sshAddressLabel = BodyLabel(self.tr("SSH Connection Address (Ipv4)"), self)
        self.sshAddressEdit = LineEdit(self)

        self.sshPortLabel = BodyLabel(self.tr("SSH Connection Port (Port number)"), self)
        self.sshPortEdit = SpinBox(self)

        self.sshUserLabel = BodyLabel(self.tr("SSH Connection Username"), self)
        self.sshUserEdit = LineEdit(self)

        self.sshPasswordLabel = BodyLabel(self.tr("SSH Connection Password"), self)
        self.sshPasswordEdit = PasswordLineEdit(self)

        self.autoCheckLayout = QHBoxLayout(self)
        self.autoCheckLabel = BodyLabel(self.tr("Check the connection after save"), self)
        # self.autoCheckPicker = CheckBox(parent=self)
        self.autoCheckPicker = SwitchButton()

        self.sshUserEdit.setText(qconfig.get(self.configUsername))
        self.sshAddressEdit.setText(qconfig.get(self.configSsh))
        self.sshAddressEdit.setPlaceholderText(qconfig.get(self.configSsh))
        self.sshAddressEdit.setClearButtonEnabled(True)

        self.sshPortEdit.setRange(1, 65535)
        self.sshPortEdit.setValue(int(qconfig.get(self.configPort)))

        self.sshUserEdit.setText(qconfig.get(self.configUsername))
        self.sshUserEdit.setPlaceholderText(qconfig.get(self.configUsername))
        self.sshUserEdit.setClearButtonEnabled(True)

        self.sshPasswordEdit.setViewPasswordButtonVisible(True)
        self.sshPasswordEdit.setClearButtonEnabled(True)
        self.sshPasswordEdit.setText(qconfig.get(self.configPassword))
        self.sshPasswordEdit.setPlaceholderText(qconfig.get(self.configPassword))

        self.autoCheckPicker.setChecked(True)

        # add widget to view layout
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.sshAddressLabel)
        self.viewLayout.addWidget(self.sshAddressEdit)
        self.viewLayout.addWidget(self.sshPortLabel)
        self.viewLayout.addWidget(self.sshPortEdit)
        self.viewLayout.addWidget(self.sshUserLabel)
        self.viewLayout.addWidget(self.sshUserEdit)
        self.viewLayout.addWidget(self.sshPasswordLabel)
        self.viewLayout.addWidget(self.sshPasswordEdit)

        self.autoCheckLayout.setContentsMargins(0, 0, 0, 0)
        self.autoCheckLayout.addWidget(self.autoCheckLabel, 0, Qt.AlignLeft)
        self.autoCheckLayout.addWidget(self.autoCheckPicker, 0, Qt.AlignRight)
        self.viewLayout.addLayout(self.autoCheckLayout)

        # change the text of button
        self.yesButton.setText(self.tr("OK"))
        self.cancelButton.setText(self.tr("Cancel"))

        self.widget.setMinimumWidth(450)

class CustomCameraSettingCard(ExpandGroupSettingCard):
    def __init__(self, configItems: Config, icon: Union[str, QIcon, FluentIconBase], title: str,
                 content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.configItems = configItems
        self.uvcAddress_items = ["/?action=stream", "/?action=stream_0", "/?action=stream_1",
                                 "/?action=stream_2", "/?action=stream_3", "/?action=stream_4"]

        self.mjpgStreamer = QWidget(self)
        self.mjpgStreamer_Layout = QHBoxLayout(self.mjpgStreamer)
        self.mjpgStreamer_Label = QLabel(self.tr("MJPG-Streamer Server HTTP Address: "), self.mjpgStreamer)
        self.mjpgStreamer_Address = LineEdit(self.mjpgStreamer)
        self.editButton = PushButton(
            self.tr('Advance Settings'), self.mjpgStreamer)

        self.uvc_cam00 = QWidget(self)
        self.uvcCam00_Layout = QHBoxLayout(self.uvc_cam00)
        self.uvcCam00_Label = QLabel(self.tr("UVC Camera 01: Left Machine Arm"), self.uvc_cam00)
        self.uvcCam00_Enabled = SwitchButton(self.uvc_cam00)
        self.uvcCam00_Address = ComboBox(self.uvc_cam00)

        self.uvc_cam01 = QWidget(self)
        self.uvcCam01_Layout = QHBoxLayout(self.uvc_cam01)
        self.uvcCam01_Label = QLabel(self.tr("UVC Camera 02: Right Machine Arm"), self.uvc_cam01)
        self.uvcCam01_Enabled = SwitchButton(self.uvc_cam01)
        self.uvcCam01_Address = ComboBox(self.uvc_cam01)

        self.uvc_cam02 = QWidget(self)
        self.uvcCam02_Layout = QHBoxLayout(self.uvc_cam02)
        self.uvcCam02_Label = QLabel(self.tr("UVC Camera 03: Left Forward Viewing Eye"), self.uvc_cam02)
        self.uvcCam02_Enabled = SwitchButton(self.uvc_cam02)
        self.uvcCam02_Address = ComboBox(self.uvc_cam02)

        self.uvc_cam03 = QWidget(self)
        self.uvcCam03_Layout = QHBoxLayout(self.uvc_cam03)
        self.uvcCam03_Label = QLabel(self.tr("UVC Camera 04: Right Forward Viewing Eye"), self.uvc_cam03)
        self.uvcCam03_Enabled = SwitchButton(self.uvc_cam03)
        self.uvcCam03_Address = ComboBox(self.uvc_cam03)

        self.uvc_cam04 = QWidget(self)
        self.uvcCam04_Layout = QHBoxLayout(self.uvc_cam04)
        self.uvcCam04_Label = QLabel(self.tr("UVC Camera 05: Backward Viewing Eye"),self.uvc_cam04)
        self.uvcCam04_Enabled = SwitchButton(self.uvc_cam04)
        self.uvcCam04_Address = ComboBox(self.uvc_cam04)

        self.checkWidget = QWidget(self.view)
        self.checkLayout = QHBoxLayout(self.checkWidget)
        self.checkingBar = IndeterminateProgressBar(self.checkWidget)
        self.checkLabel = QLabel(self.checkWidget)
        self.detailButton = PushButton(
            self.tr('View Details'), self.checkWidget)
        self.checkButton = PrimaryPushButton(
            self.tr("Check Cameras Connection"), self.checkWidget)

        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()

        self.mjpgStreamer_Label.setObjectName("titleLabel")
        self.uvcCam00_Label.setObjectName("titleLabel")
        self.uvcCam01_Label.setObjectName("titleLabel")
        self.uvcCam02_Label.setObjectName("titleLabel")
        self.uvcCam03_Label.setObjectName("titleLabel")
        self.uvcCam04_Label.setObjectName("titleLabel")
        self.checkLabel.setObjectName("titleLabel")

        self.uvcCam00_Address.addItems(self.uvcAddress_items)
        self.uvcCam01_Address.addItems(self.uvcAddress_items)
        self.uvcCam02_Address.addItems(self.uvcAddress_items)
        self.uvcCam03_Address.addItems(self.uvcAddress_items)
        self.uvcCam04_Address.addItems(self.uvcAddress_items)

        # self.__updateItems()

    def __updateItems(self):
        self.mjpgStreamer_Address.setText(qconfig.get(self.configItems.mjpgServerAddress))
        self.mjpgStreamer_Address.setPlaceholderText(qconfig.get(self.configItems.mjpgServerAddress))
        self.mjpgStreamer_Address.setClearButtonEnabled(True)

    def __initLayout(self):
        self.mjpgStreamer_Layout.setContentsMargins(48, 18, 44, 18)
        self.mjpgStreamer_Layout.addWidget(self.mjpgStreamer_Label, 0, Qt.AlignLeft)
        self.mjpgStreamer_Layout.addSpacing(50)
        self.mjpgStreamer_Layout.addWidget(self.mjpgStreamer_Address, 1)
        self.mjpgStreamer_Layout.addSpacing(15)
        self.mjpgStreamer_Layout.addWidget(self.editButton, 0, Qt.AlignRight)

        self.uvcCam00_Layout.setContentsMargins(48, 18, 44, 18)
        self.uvcCam00_Layout.addWidget(self.uvcCam00_Label, 0, Qt.AlignLeft)
        self.uvcCam00_Layout.addStretch()
        self.uvcCam00_Layout.addWidget(self.uvcCam00_Enabled, 0, Qt.AlignRight)
        self.uvcCam00_Layout.addSpacing(15)
        self.uvcCam00_Address.setFixedWidth(180)
        self.uvcCam00_Layout.addWidget(self.uvcCam00_Address, 0, Qt.AlignRight)

        self.uvcCam01_Layout.setContentsMargins(48, 18, 44, 18)
        self.uvcCam01_Layout.addWidget(self.uvcCam01_Label, 0, Qt.AlignLeft)
        self.uvcCam01_Layout.addStretch()
        self.uvcCam01_Layout.addWidget(self.uvcCam01_Enabled, 0, Qt.AlignRight)
        self.uvcCam01_Layout.addSpacing(15)
        self.uvcCam01_Address.setFixedWidth(180)
        self.uvcCam01_Layout.addWidget(self.uvcCam01_Address, 0, Qt.AlignRight)

        self.uvcCam02_Layout.setContentsMargins(48, 18, 44, 18)
        self.uvcCam02_Layout.addWidget(self.uvcCam02_Label, 0, Qt.AlignLeft)
        self.uvcCam02_Layout.addStretch()
        self.uvcCam02_Layout.addWidget(self.uvcCam02_Enabled, 0, Qt.AlignRight)
        self.uvcCam02_Layout.addSpacing(15)
        self.uvcCam02_Address.setFixedWidth(180)
        self.uvcCam02_Layout.addWidget(self.uvcCam02_Address, 0, Qt.AlignRight)

        self.uvcCam03_Layout.setContentsMargins(48, 18, 44, 18)
        self.uvcCam03_Layout.addWidget(self.uvcCam03_Label, 0, Qt.AlignLeft)
        self.uvcCam03_Layout.addStretch()
        self.uvcCam03_Layout.addWidget(self.uvcCam03_Enabled, 0, Qt.AlignRight)
        self.uvcCam03_Layout.addSpacing(15)
        self.uvcCam03_Address.setFixedWidth(180)
        self.uvcCam03_Layout.addWidget(self.uvcCam03_Address, 0, Qt.AlignRight)

        self.uvcCam04_Layout.setContentsMargins(48, 18, 44, 18)
        self.uvcCam04_Layout.addWidget(self.uvcCam04_Label, 0, Qt.AlignLeft)
        self.uvcCam04_Layout.addStretch()
        self.uvcCam04_Layout.addWidget(self.uvcCam04_Enabled, 0, Qt.AlignRight)
        self.uvcCam04_Layout.addSpacing(15)
        self.uvcCam04_Address.setFixedWidth(180)
        self.uvcCam04_Layout.addWidget(self.uvcCam04_Address, 0, Qt.AlignRight)

        self.checkLayout.setContentsMargins(48, 18, 44, 18)
        self.checkLayout.addWidget(self.checkLabel, 0, Qt.AlignLeft)
        self.checkLayout.addWidget(self.checkingBar, 0, Qt.AlignLeft)
        self.checkLayout.addStretch()
        self.checkLayout.addWidget(self.detailButton, 0, Qt.AlignRight)
        self.checkLayout.addWidget(self.checkButton, 0, Qt.AlignRight)
        self.checkLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.addGroupWidget(self.mjpgStreamer)
        self.addGroupWidget(self.uvc_cam00)
        self.addGroupWidget(self.uvc_cam01)
        self.addGroupWidget(self.uvc_cam02)
        self.addGroupWidget(self.uvc_cam03)
        self.addGroupWidget(self.uvc_cam04)
        self.addGroupWidget(self.checkWidget)

class SettingInterface(ScrollArea):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)

        # music folders
        # self.musicInThisPCGroup = SettingCardGroup(
        #     self.tr("Music on this PC"), self.scrollWidget)
        # self.musicFolderCard = FolderListSettingCard(
        #     cfg.musicFolders,
        #     self.tr("Local music library"),
        #     directory=QStandardPaths.writableLocation(
        #         QStandardPaths.MusicLocation),
        #     parent=self.musicInThisPCGroup
        # )
        # self.downloadFolderCard = PushSettingCard(
        #     self.tr('Choose folder'),
        #     FIF.DOWNLOAD,
        #     self.tr("Download directory"),
        #     cfg.get(cfg.downloadFolder),
        #     self.musicInThisPCGroup
        # )

        # ROV Connection
        self.rovConnectGroup = SettingCardGroup(
            self.tr('ROV Connection'), self.scrollWidget)
        self.sshconfig = CustomSSHSettingCard(
            cfg,
            FIF.CERTIFICATE,
            self.tr("ROV SSH Connection"),
            self.tr("Configure the connection between ROV and computer using SSH Protocol"), 
            self.rovConnectGroup
        )
        self.sshconfig.sshUpdated.connect(self.__ssh_pop_infoBar)
        self.camconfig = CustomCameraSettingCard(
            cfg,
            FIF.CAMERA,
            self.tr("ROV Cameras Connnection"),
            self.tr("Modify and test for the 5 cameras on the ROV using HTTP Stream Protocol"),
            self.rovConnectGroup
        )

        # personalization
        self.personalGroup = SettingCardGroup(
            self.tr('Personalization'), self.scrollWidget)
        self.micaCard = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('Mica effect'),
            self.tr('Apply semi transparent to windows and surfaces'),
            cfg.micaEnabled,
            self.personalGroup
        )
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr('Application theme'),
            self.tr("Change the appearance of your application"),
            texts=[
                self.tr('Light'), self.tr('Dark'),
                self.tr('Use system setting')
            ],
            parent=self.personalGroup
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            self.tr('Theme color'),
            self.tr('Change the theme color of you application'),
            self.personalGroup
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("Interface zoom"),
            self.tr("Change the size of widgets and fonts"),
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                self.tr("Use system setting")
            ],
            parent=self.personalGroup
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr('Language'),
            self.tr('Set your preferred language for UI'),
            texts=['简体中文', '繁體中文', 'English', self.tr('Use system setting')],
            parent=self.personalGroup
        )

        # material
        # self.materialGroup = SettingCardGroup(
        #     self.tr('Material'), self.scrollWidget)
        # self.blurRadiusCard = RangeSettingCard(
        #     cfg.blurRadius,
        #     FIF.ALBUM,
        #     self.tr('Acrylic blur radius'),
        #     self.tr('The greater the radius, the more blurred the image'),
        #     self.materialGroup
        # )

        # update software
        # self.updateSoftwareGroup = SettingCardGroup(
        #     self.tr("Software update"), self.scrollWidget)
        # self.updateOnStartUpCard = SwitchSettingCard(
        #     FIF.UPDATE,
        #     self.tr('Check for updates when the application starts'),
        #     self.tr('The new version will be more stable and have more features'),
        #     configItem=cfg.checkUpdateAtStartUp,
        #     parent=self.updateSoftwareGroup
        # )

        # application
        self.aboutGroup = SettingCardGroup(self.tr('About'), self.scrollWidget)
        self.helpCard = HyperlinkCard(
            HELP_URL,
            self.tr('Open help page'),
            FIF.HELP,
            self.tr('Help'),
            self.tr(
                'Discover new features and learn useful tips about ROV -Control Panel'),
            self.aboutGroup
        )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr('Provide feedback'),
            FIF.FEEDBACK,
            self.tr('Provide feedback'),
            self.tr('Help us improve ROV -Control Panel by providing feedback'),
            self.aboutGroup
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr('Check update'),
            FIF.INFO,
            self.tr('About'),
            '© ' + self.tr('Copyright') + f" {YEAR}, {AUTHOR}. " +
            self.tr('Version') + " " + VERSION,
            self.aboutGroup
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.micaCard.setEnabled(isWin11())

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # add cards to group
        # self.musicInThisPCGroup.addSettingCard(self.musicFolderCard)
        # self.musicInThisPCGroup.addSettingCard(self.downloadFolderCard)

        self.rovConnectGroup.addSettingCard(self.sshconfig)
        self.rovConnectGroup.addSettingCard(self.camconfig)

        self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)

        # self.materialGroup.addSettingCard(self.blurRadiusCard)

        # self.updateSoftwareGroup.addSettingCard(self.updateOnStartUpCard)

        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        # self.expandLayout.addWidget(self.musicInThisPCGroup)
        self.expandLayout.addWidget(self.rovConnectGroup)
        self.expandLayout.addWidget(self.personalGroup)
        # self.expandLayout.addWidget(self.materialGroup)
        # self.expandLayout.addWidget(self.updateSoftwareGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            self.tr('Updated successfully'),
            self.tr('Configuration takes effect after restart'),
            duration=3000,
            parent=self
        )

    def __ssh_pop_infoBar(self, init: bool):
        if init: return
        if self.sshconfig.connectionStatus == "Checking":
            w = InfoBar.warning(
                title=self.tr("SSH Connection:"),
                content=self.tr("SSH Connection Check is performing, please try again later."),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_LEFT,
                duration=2000,    # won't disappear automatically
                parent=self
            )
            w.show()
        elif self.sshconfig.connectionStatus == "Success":
            w = InfoBar.success(
                title=self.tr("SSH Connection:"),
                content=self.tr("Success!  "),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_LEFT,
                duration=2000,    # won't disappear automatically
                parent=self
            )
            wbtn = PushButton(self.tr('View Details'), self)
            wbtn.clicked.connect(self.sshconfig.showSSHDetail)
            w.addWidget(wbtn, 0)
            w.show()
        elif self.sshconfig.connectionStatus == "Failed":
            w = InfoBar.error(
                title=self.tr("SSH Connection: "),
                content=self.tr("Failed!  "),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_LEFT,
                duration=5000,    # won't disappear automatically
                parent=self
            )
            wbtn = PushButton(self.tr('View Details'), self)
            wbtn.clicked.connect(self.sshconfig.showSSHDetail)
            w.addWidget(wbtn, 0)
            w.show()

    # def __onDownloadFolderCardClicked(self):
    #     """ download folder card clicked slot """
    #     folder = QFileDialog.getExistingDirectory(
    #         self, self.tr("Choose folder"), "./")
    #     if not folder or cfg.get(cfg.downloadFolder) == folder:
    #         return

    #     cfg.set(cfg.downloadFolder, folder)
    #     self.downloadFolderCard.setContent(folder)

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # music in the pc
        # self.downloadFolderCard.clicked.connect(
        #     self.__onDownloadFolderCardClicked)

        # personalization
        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)

        # about
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
        self.aboutCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(RELEASE_URL)))
