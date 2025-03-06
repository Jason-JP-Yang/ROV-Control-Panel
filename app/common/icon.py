# coding: utf-8
from enum import Enum

from qfluentwidgets import (FluentIconBase, getIconColor, Theme, IconWidget, drawIcon)
from PyQt5.QtGui import QPainter, QIcon

from .config import cfg, qconfig

class SettingIconWidget(IconWidget):

    def paintEvent(self, e):
        painter = QPainter(self)

        if not self.isEnabled():
            painter.setOpacity(0.36)

        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        drawIcon(self._icon, painter, self.rect())

def get_IconLabel(icon: str | QIcon | FluentIconBase, size: tuple[int, int] = (16, 16)):
    icon = SettingIconWidget(icon)
    icon.setFixedSize(size[0], size[1])
    return icon

class Icon(FluentIconBase, Enum):

    CAMERA = "camera"
    ETHERNET = "ethernet"
    WEB_CAMERA = "camera-web"
    CONNECT = "connect"
    SETTING = "setting"
    SENSOR = "sensor"
    ROUTER = "router"
    TERMINAL = "terminal"
    HOME = "home"
    DHARMACHAKRA = "dharmachakra"
    JOYSTICK = "joystick"

    def path(self, theme=Theme.AUTO):
        IconStyle = qconfig.get(cfg.IconStyle)
        if IconStyle == "Classic Solid": IconStyle = "solid"
        elif IconStyle == "Classic Regular": IconStyle = "regular"
        elif IconStyle == "Sharp Solid": IconStyle = "s-solid"
        elif IconStyle == "Sharp Regular": IconStyle = "s-regular"

        return f":icons/icons/{self.value}/{IconStyle}_{getIconColor(theme)}.svg"