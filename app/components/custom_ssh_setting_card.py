# coding:utf-8
from typing import Union
from qfluentwidgets import (MessageBox, SwitchButton, ExpandGroupSettingCard,
                            FluentIconBase, LineEdit, qconfig, PrimaryPushButton, PushButton,
                            IndeterminateProgressBar, MessageBoxBase,
                            SubtitleLabel, BodyLabel, SpinBox, PasswordLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QEventLoop, QTimer, pyqtSlot, QThread
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout

from ..common.config import Config
from ..common.threading_func import threaded_func
from ..common.icon import get_IconLabel, Icon as AppIcon
from ..common.signal_bus import signalBus

import paramiko, socket, time
from datetime import datetime
from paramiko import SSHException, AuthenticationException

class checkSSHConnection(QThread):
    result = pyqtSignal(str, str, bool)

    def __init__(self, configItems: Config, init: bool = False, parent=None):
        super().__init__(parent)
        self.init = init
        self.configItems = configItems
        self.configSsh = configItems.sshAddress
        self.configPort = configItems.sshPort
        self.configUsername = configItems.sshUser
        self.configPassword = configItems.sshPassword

        signalBus.CurrentWidgetSwitch.connect(self.terminate)
    
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

    def run(self):
        start_time = time.time()
        connectionStatus, sshMessage = self.__checkSSHConnection()
        print(connectionStatus, sshMessage)
        
        loop = QEventLoop()
        QTimer.singleShot(int(max((1 - time.time() + start_time) * 1000, 0)), loop.quit)
        loop.exec_()

        self.result.emit(connectionStatus, sshMessage, self.init)
    
    def terminate(self, index: int):
        if not index == 12: self.quit()

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
        self.checkButton.clicked.connect(lambda: self.checkSSHStatus(init=False))
        self.detailButton.clicked.connect(self.showSSHDetail)

        # Connect Signal to Slot
        signalBus.CurrentWidgetSwitch.connect(self.widgetEnabledTrigger)

        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()
        
        self.sshLinkLabel.setObjectName("titleLabel")
        self.sshPort.setObjectName("titleLabel")
        self.sshUserLabel.setObjectName("titleLabel")
        self.passwordLabel.setObjectName("titleLabel")
        self.checkLabel.setObjectName("titleLabel")
        self.__updateLabel()

        # self.checkSSHStatus(init=True)
    
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
        self.checkLayout.addWidget(get_IconLabel(AppIcon.CONNECT, (24, 20)), 0, Qt.AlignLeft)
        self.checkLayout.addSpacing(4)
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

    def checkSSHStatus(self, init: bool = False):
        if self.connectionStatus == "Checking": 
            self.sshUpdated.emit(init)
            return
        self.connectionStatus = "Checking"
        self.checkButton.setEnabled(False)
        self.detailButton.setEnabled(False)
        self.checkLabel.setText(self.tr("Checking Connection: "))
        self.checkLabel.adjustSize()
        self.checkingBar.show()

        self.threads = checkSSHConnection(self.configItems, init=init)
        self.threads.result.connect(self.updateSSHStatus)
        self.threads.start()
        # self.threads.finished.connect(lambda: self.threads.deleteLater())
    
    def updateSSHStatus(self, connectionStatus, sshMessage, init: bool = False):
        self.connectionStatus = connectionStatus
        self.sshMessage = sshMessage

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
                self.checkSSHStatus(init=False)

    def widgetEnabledTrigger(self, index: int):
        if index == 12: self.checkSSHStatus(init=True)

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
