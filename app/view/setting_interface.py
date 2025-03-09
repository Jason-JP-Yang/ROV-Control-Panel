# coding:utf-8
from typing import Union
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard,
                            OptionsSettingCard, HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, CustomColorSettingCard,
                            setTheme, setThemeColor, PushButton, InfoBarPosition)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget, QLabel

from ..components.custom_ssh_setting_card import CustomSSHSettingCard
from ..components.custom_cam_setting_card import CustomCameraSettingCard

from ..common.config import cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR, RELEASE_URL, isWin11
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..common.icon import Icon as AppIcon

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
            AppIcon.ETHERNET,
            self.tr("ROV Ethernet SSH Connection"),
            self.tr("Configure the connection between ROV and computer using SSH Protocol"), 
            self.rovConnectGroup
        )
        self.camconfig = CustomCameraSettingCard(
            cfg,
            AppIcon.CAMERA,
            self.tr("ROV Cameras Connnection"),
            self.tr("Modify settings and test connection for the 5 cameras on the ROV using HTTP Stream Protocol"),
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
        self.iconstyleCard = ComboBoxSettingCard(
            cfg.IconStyle,
            FIF.EMOJI_TAB_SYMBOLS,
            self.tr("Application Icon Style"),
            self.tr("Change the style of the application icons"),
            texts=["Classic Solid", "Classic Regular", "Sharp Solid", "Sharp Regular"],
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

        self.sshconfig.card.iconLabel.setFixedSize(20, 20)
        self.camconfig.card.iconLabel.setFixedSize(20, 20)
        self.micaCard.iconLabel.setFixedSize(20, 20)
        self.themeCard.card.iconLabel.setFixedSize(20, 20)
        self.themeColorCard.card.iconLabel.setFixedSize(20, 20)
        self.zoomCard.card.iconLabel.setFixedSize(20, 20)
        self.languageCard.iconLabel.setFixedSize(20, 20)
        self.iconstyleCard.iconLabel.setFixedSize(20, 20)
        self.helpCard.iconLabel.setFixedSize(20, 20)
        self.feedbackCard.iconLabel.setFixedSize(20, 20)
        self.aboutCard.iconLabel.setFixedSize(20, 20)

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.iconstyleCard.comboBox.setFixedWidth(160)

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
        self.personalGroup.addSettingCard(self.iconstyleCard)

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
            position=InfoBarPosition.BOTTOM_LEFT,
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
        self.sshconfig.sshUpdated.connect(self.__ssh_pop_infoBar)
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
