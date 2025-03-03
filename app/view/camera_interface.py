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

class CameraInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)