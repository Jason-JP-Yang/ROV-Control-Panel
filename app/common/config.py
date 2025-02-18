# coding:utf-8
import sys
from enum import Enum

from PyQt5.QtCore import QLocale
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderListValidator, Theme, FolderValidator, ConfigSerializer, __version__)

# ROV Deafult Connection Configuration 
SSH_ADDRESS = "127.0.0.1" 
SSH_PORT = 22
SSH_USERNAME = "jasonyang"
SSH_PASSWORD = "Yangr?gdrPM4>"

# Basic Configuration
YEAR = "2024-2025"
AUTHOR = "NPL ROV TEAM, Jason Yang, Mark Chan"
VERSION = "Alpha 0.1"
HELP_URL = "https://github.com/Jason-JP-Yang/ROV-Control-Panel/wiki"
REPO_URL = "https://github.com/Jason-JP-Yang/ROV-Control-Panel"
EXAMPLE_URL = "https://github.com/zhiyiYo/PyQt-Fluent-Widgets/tree/master/examples"
FEEDBACK_URL = "https://github.com/Jason-JP-Yang/ROV-Control-Panel/issues"
RELEASE_URL = "https://github.com/Jason-JP-Yang/ROV-Control-Panel/releases/latest"


class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Chinese, QLocale.HongKong)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000

class Ipv4AddressValidator():
    """ Ipv4 Address Validator """

    def __init__(self, default="0.0.0.0"):
        super().__init__()
        if not self.validate(default):
            raise ValueError(f"Invalid default IPv4 address: {default}")
        self.default = default

    def validate(self, value):
        if not isinstance(value, str):
            return False
        parts = value.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False
            if len(part) > 1 and part.startswith('0'):
                return False
        return True

    def correct(self, value):
        return value if self.validate(value) else self.default

class Config(QConfig):
    """ Config of application """
    # ROV Connection
    sshAddress = OptionsConfigItem(
        "ROV_Connection", "sshAddress", SSH_ADDRESS, Ipv4AddressValidator(SSH_ADDRESS))
    sshPort = OptionsConfigItem(
        "ROV_Connection", "sshUsername", SSH_PORT)
    sshUser = OptionsConfigItem(
        "ROV_Connection", "sshUsername", SSH_USERNAME)
    sshPassword = OptionsConfigItem(
        "ROV_Connection", "sshPassword", SSH_PASSWORD)

    # folders
    # musicFolders = ConfigItem(
    #     "Folders", "LocalMusic", [], FolderListValidator())
    # downloadFolder = ConfigItem(
    #     "Folders", "Download", "app/download", FolderValidator())

    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # Material
    # blurRadius  = RangeConfigItem("Material", "AcrylicBlurRadius", 15, RangeValidator(0, 40))

    # software update
    # checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", True, BoolValidator())

cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load('app/config/config.json', cfg)