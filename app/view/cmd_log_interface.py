from typing import Union
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard,
                            OptionsSettingCard, HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, CustomColorSettingCard,
                            setTheme, setThemeColor, PushButton, TitleLabel)
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

class CmdLoggerInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cmdInterface = QWidget()
        self.cmdLoggerLabel = TitleLabel(self.tr("Settings"), self)
        
        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.cmdInterface)
        self.setWidgetResizable(True)

        self.cmdLoggerLabel.setObjectName('cmdLabel')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.__initLayout()

    def __initLayout(self):
        pass