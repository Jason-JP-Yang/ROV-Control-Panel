# coding: utf-8
from enum import Enum

from qfluentwidgets import FluentIconBase, getIconColor, Theme

from .config import cfg, qconfig

class Icon(FluentIconBase, Enum):

    CAMERA = "camera"
    ETHERNET = "ethernet"

    def path(self, theme=Theme.AUTO):
        IconStyle = qconfig.get(cfg.IconStyle)
        if IconStyle == "Classic Solid": IconStyle = "solid"
        elif IconStyle == "Classic Regular": IconStyle = "regular"
        elif IconStyle == "Sharp Solid": IconStyle = "s-solid"
        elif IconStyle == "Sharp Regular": IconStyle = "s-regular"

        return f":icons/icons/{self.value}/{IconStyle}_{getIconColor(theme)}.svg"