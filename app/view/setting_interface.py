# coding:utf-8
from typing import Union
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard, SettingCard, ExpandGroupSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, RangeSettingCard, isDarkTheme, 
                            FluentIconBase, LineEdit, qconfig, PrimaryPushButton)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QStandardPaths
from PyQt5.QtGui import QDesktopServices, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QFileDialog, QHBoxLayout, QPushButton, QVBoxLayout

from ..common.config import Config, cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR, RELEASE_URL, isWin11
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet

import paramiko
import socket
from paramiko import SSHException, AuthenticationException

class CustomSSHSettingCard(ExpandGroupSettingCard):
    def __init__(self, configItems: list, icon: Union[str, QIcon, FluentIconBase], title: str,
                 content=None, parent=None):
        super().__init__(icon, title, content, parent=parent)
        self.configSsh = configItems[0]
        self.configPort = configItems[1]
        self.configUsername = configItems[2]
        self.configPassword = configItems[3]
        self.connectionStatus = "Unknown"

        self.Widget = QWidget(self.view)
        self.Layout = QVBoxLayout(self.Widget)
        self.line1Layout = QHBoxLayout(self.Widget)

        self.editButton = QPushButton(
            self.tr('Edit Settings'), self.Widget)
        self.sshLinkLabel = QLabel(self.Widget)
        self.passwordLabel = QLabel(self.Widget)

        self.checkWidget = QWidget(self.view)
        self.checkLayout = QHBoxLayout(self.checkWidget)
        self.checkLabel = QLabel(self.checkWidget)
        self.checkButton = PrimaryPushButton(
            self.tr("Check SSH Connection"), self.checkWidget)

        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()
        
        self.sshLinkLabel.setText(self.tr("SSH Connection Link: ") + qconfig.get(self.configSsh))
        self.sshLinkLabel.setObjectName("titleLabel")
        self.sshLinkLabel.adjustSize()

        self.passwordLabel.setText(self.tr("SSH Password: ") + qconfig.get(self.configPassword))
        self.passwordLabel.setObjectName("titleLabel")
        self.passwordLabel.adjustSize()

        self.checkLabel.setText(self.tr("SSH Connection Status: ") + self.connectionStatus)
        self.checkLabel.setObjectName("titleLabel")
        self.checkLabel.adjustSize()
    
    def __initLayout(self):
        self.Layout.setAlignment(Qt.AlignTop)
        self.Layout.setContentsMargins(48, 18, 44, 18)
        
        self.line1Layout.addWidget(self.sshLinkLabel, 0, Qt.AlignLeft)
        self.line1Layout.addWidget(self.editButton, 0, Qt.AlignRight | Qt.AlignTop)
        
        self.Layout.addLayout(self.line1Layout, 0)
        self.Layout.addWidget(self.passwordLabel, 0, Qt.AlignLeft)
        self.Layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.checkLayout.setContentsMargins(48, 18, 44, 18)
        self.checkLayout.addWidget(self.checkLabel, 0, Qt.AlignLeft)
        self.checkLayout.addWidget(self.checkButton, 0, Qt.AlignRight)
        self.checkLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.addGroupWidget(self.Widget)
        self.addGroupWidget(self.checkWidget)
    
    def checkSSHConnection(self):
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

        try:
            # 尝试连接 SSH 服务器
            client.connect(
                self.configSsh, port=self.configPort, 
                username=self.configUsername, password=self.configPassword, timeout=5)
            # 如果连接成功，返回成功信息
            success, message = True, self.tr("SSH Connection Success!")
        except AuthenticationException:
            # 认证失败
            success, message = False, self.tr("SSH Connection Failed: Authentication Failed, Asscess Denied")
        except SSHException as e:
            # 其他 SSH 错误
            success, message = False, self.tr("SSH Connection Failed: ") + e
        except socket.error as e:
            # 网络错误
            success, message = False, self.tr("Network Connection Failed: Check your Internet") + f"({e})"
        finally:
            # 确保连接关闭
            client.close()

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
            [cfg.sshAddress, cfg.sshPort, cfg.sshUser, cfg.sshPassword],
            FIF.CERTIFICATE,
            self.tr("ROV SSH Connection"),
            self.tr("TEST"), 
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
