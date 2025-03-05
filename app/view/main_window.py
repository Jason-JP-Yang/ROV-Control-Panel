# coding: utf-8
from PyQt5.QtCore import QUrl, QSize, QTimer, QEventLoop
from PyQt5.QtGui import QIcon, QDesktopServices, QColor
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import (NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,
                            SplashScreen, SystemThemeListener, isDarkTheme)
from qfluentwidgets import FluentIcon as FIF

# from .gallery_interface import GalleryInterface
from .home_interface import HomeInterface
from .setting_interface import SettingInterface
from ..components.page_frame import Widget as PageFrame

from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..common.translator import Translator
from ..common import resource
from ..common.icon import Icon as AppIcon

class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()

        # create system theme listener
        self.themeListener = SystemThemeListener(self)

        # create sub interface
        self.homeInterface = HomeInterface(self)
        self.settingInterface = SettingInterface(self)
        
        self.driverWindow = PageFrame("Pilot - Driver Interface")
        self.operatorWindow = PageFrame("Pilot - Operator Interface")

        self.sshInterface = PageFrame("SSH Control Panel - ROV Connection")
        self.cmdInterface = PageFrame("Command Line Config Interface")

        self.InIOInterface = PageFrame("Input Signal Panel - Controller")
        self.armInterface = PageFrame("Machine Arm Control Panel")
        self.sensorsInterface = PageFrame("ROV Sensors Control Panel")
        
        self.camerasInterface = PageFrame("Cameras Interface - Summarize")
        self.cam00Interface = PageFrame("Cameras Interface - UVC_CAM_01")
        self.cam01Interface = PageFrame("Cameras Interface - UVC_CAM_02")
        self.cam02Interface = PageFrame("Cameras Interface - UVC_CAM_03")
        self.cam03Interface = PageFrame("Cameras Interface - UVC_CAM_04")
        self.cam04Interface = PageFrame("Cameras Interface - UVC_CAM_05")

        # enable acrylic effect
        self.navigationInterface.setAcrylicEnabled(True)

        self.connectSignalToSlot()

        # add items to navigation interface
        self.initNavigation()
        self.splashScreen.finish()

        # start theme listener
        self.themeListener.start()

    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        # signalBus.switchToSampleCard.connect(self.switchToSample)
        # signalBus.supportSignal.connect(self.onSupport)

    def initNavigation(self):
        # add navigation items
        # t = Translator()
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('Home'))
        self.addSubInterface(self.driverWindow, FIF.ALBUM, self.tr("ROV Driver Interface"))
        self.addSubInterface(self.operatorWindow, FIF.ALBUM, self.tr("ROV Operator Interface"))
        # self.addSubInterface(self.iconInterface, Icon.EMOJI_TAB_SYMBOLS, t.icons)
        self.navigationInterface.addSeparator()
        
        pos = NavigationItemPosition.SCROLL
        self.addSubInterface(self.sshInterface, FIF.ALBUM, self.tr("SSH Connect Interface"), pos)
        self.addSubInterface(self.cmdInterface, FIF.ALBUM, self.tr("Command Logs Interface"), pos)
        self.addSubInterface(self.InIOInterface, FIF.ALBUM, self.tr("Input Signals Panel"), pos)
        
        self.addSubInterface(self.camerasInterface, AppIcon.CAMERA, self.tr("Cameras Interface"), pos)
        self.addSubInterface(self.cam00Interface, AppIcon.CAMERA, self.tr("UVC Camera 01"), pos, self.camerasInterface)
        self.addSubInterface(self.cam01Interface, AppIcon.CAMERA, self.tr("UVC Camera 02"), pos, self.camerasInterface)
        self.addSubInterface(self.cam02Interface, AppIcon.CAMERA, self.tr("UVC Camera 03"), pos, self.camerasInterface)
        self.addSubInterface(self.cam03Interface, AppIcon.CAMERA, self.tr("UVC Camera 04"), pos, self.camerasInterface)
        self.addSubInterface(self.cam04Interface, AppIcon.CAMERA, self.tr("UVC Camera 05"), pos, self.camerasInterface)
        
        # self.addSubInterface(self.basicInputInterface, FIF.CHECKBOX,t.basicInput, pos)
        # self.addSubInterface(self.dateTimeInterface, FIF.DATE_TIME, t.dateTime, pos)
        # self.addSubInterface(self.dialogInterface, FIF.MESSAGE, t.dialogs, pos)
        # self.addSubInterface(self.layoutInterface, FIF.LAYOUT, t.layout, pos)
        # self.addSubInterface(self.materialInterface, FIF.PALETTE, t.material, pos)
        # self.addSubInterface(self.menuInterface, Icon.MENU, t.menus, pos)
        # self.addSubInterface(self.navigationViewInterface, FIF.MENU, t.navigation, pos)
        # self.addSubInterface(self.scrollInterface, FIF.SCROLL, t.scroll, pos)
        # self.addSubInterface(self.statusInfoInterface, FIF.CHAT, t.statusInfo, pos)
        # self.addSubInterface(self.textInterface, Icon.TEXT, t.text, pos)
        # self.addSubInterface(self.viewInterface, Icon.GRID, t.view, pos)

        # add custom widget to bottom
        # self.navigationInterface.addItem(
        #     routeKey='price',
        #     icon=Icon.PRICE,
        #     text=t.price,
        #     onClick=self.onSupport,
        #     selectable=False,
        #     tooltip=t.price,
        #     position=NavigationItemPosition.BOTTOM
        # )
        self.addSubInterface(
            self.settingInterface, AppIcon.SETTING, self.tr('Settings'), NavigationItemPosition.BOTTOM)

    def initWindow(self):
        self.resize(960, 780)
        self.setMinimumWidth(960)
        self.setMinimumHeight(780)
        self.setWindowIcon(QIcon(':/gallery/images/logo.png'))
        self.setWindowTitle('ROV Control Panel')

        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())

    def closeEvent(self, e):
        self.themeListener.terminate()
        self.themeListener.deleteLater()
        super().closeEvent(e)

    def _onThemeChangedFinished(self):
        super()._onThemeChangedFinished()

        # retry
        if self.isMicaEffectEnabled():
            QTimer.singleShot(100, lambda: self.windowEffect.setMicaEffect(self.winId(), isDarkTheme()))

    # def switchToSample(self, routeKey, index):
    #     """ switch to sample """
    #     interfaces = self.findChildren(GalleryInterface)
    #     for w in interfaces:
    #         if w.objectName() == routeKey:
    #             self.stackedWidget.setCurrentWidget(w, False)
    #             w.scrollToCard(index)
