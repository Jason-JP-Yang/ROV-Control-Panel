# coding:utf-8
from typing import Union
from qfluentwidgets import (FluentIconBase, LineEdit, qconfig, PrimaryPushButton, PushButton,
                            IndeterminateProgressBar, MessageBoxBase, TextBrowser, ExpandGroupSettingCard,
                            SubtitleLabel, SwitchButton, ComboBox, SingleDirectionScrollArea,
                            BodyLabel)
from PyQt5.QtCore import Qt, QEventLoop, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout

from ..common.config import Config
from ..common.icon import Icon as AppIcon, get_IconLabel
from ..common.threading_func import threaded_func

import time, json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import requests

class CustomCameraSettingCard(ExpandGroupSettingCard):
    def __init__(self, configItems: Config, icon: Union[str, QIcon, FluentIconBase], title: str,
                 content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.configItems = configItems
        self.uvcAddress_items = ["/?action=stream", "/?action=stream_0", "/?action=stream_1",
                                 "/?action=stream_2", "/?action=stream_3", "/?action=stream_4"]
        self.connectionStatus = True
        self.resultCam00 = {"connectionStatus": "None"}
        self.resultCam01 = {"connectionStatus": "None"}
        self.resultCam02 = {"connectionStatus": "None"}
        self.resultCam03 = {"connectionStatus": "None"}
        self.resultCam04 = {"connectionStatus": "None"}

        self.mjpgStreamer = QWidget(self)
        self.mjpgStreamer_Layout = QHBoxLayout(self.mjpgStreamer)
        self.mjpgStreamer_Label = QLabel(self.tr("MJPG-Streamer Server HTTP Address: "), self.mjpgStreamer)
        self.mjpgStreamer_Address = LineEdit(self.mjpgStreamer)
        self.editButton = PushButton(
            self.tr('Advance Settings'), self.mjpgStreamer)

        self.uvc_cam00 = QWidget(self)
        self.uvcCam00_Layout = QHBoxLayout(self.uvc_cam00)
        self.uvcCam00_vLayout = QVBoxLayout(self.uvc_cam00)
        self.uvcCam00_Label = QLabel(self.tr("UVC Camera 01: Left Machine Arm"), self.uvc_cam00)
        self.uvcCam00_Content = QLabel(self.tr("140 degree of field of view, used for close-up view of the left machine arm."), self.uvc_cam00)
        self.uvcCam00_Enabled = SwitchButton(self.uvc_cam00)
        self.uvcCam00_Address = ComboBox(self.uvc_cam00)

        self.uvc_cam01 = QWidget(self)
        self.uvcCam01_Layout = QHBoxLayout(self.uvc_cam01)
        self.uvcCam01_vLayout = QVBoxLayout(self.uvc_cam01)
        self.uvcCam01_Label = QLabel(self.tr("UVC Camera 02: Right Machine Arm"), self.uvc_cam01)
        self.uvcCam01_Content = QLabel(self.tr("140 degree of field of view, used for close-up view of the right machine arm."), self.uvc_cam01)
        self.uvcCam01_Enabled = SwitchButton(self.uvc_cam01)
        self.uvcCam01_Address = ComboBox(self.uvc_cam01)

        self.uvc_cam02 = QWidget(self)
        self.uvcCam02_Layout = QHBoxLayout(self.uvc_cam02)
        self.uvcCam02_vLayout = QVBoxLayout(self.uvc_cam02)
        self.uvcCam02_Label = QLabel(self.tr("UVC Camera 03: Left Forward Viewing Eye"), self.uvc_cam02)
        self.uvcCam02_Content = QLabel(self.tr("120 degree of field of view, used for measurement in stereo vision (LEFT)."), self.uvc_cam02)
        self.uvcCam02_Enabled = SwitchButton(self.uvc_cam02)
        self.uvcCam02_Address = ComboBox(self.uvc_cam02)

        self.uvc_cam03 = QWidget(self)
        self.uvcCam03_Layout = QHBoxLayout(self.uvc_cam03)
        self.uvcCam03_vLayout = QVBoxLayout(self.uvc_cam03)
        self.uvcCam03_Label = QLabel(self.tr("UVC Camera 04: Right Forward Viewing Eye"), self.uvc_cam03)
        self.uvcCam03_Content = QLabel(self.tr("120 degree of field of view, used for measurement in stereo vision (RIGHT)."), self.uvc_cam03)
        self.uvcCam03_Enabled = SwitchButton(self.uvc_cam03)
        self.uvcCam03_Address = ComboBox(self.uvc_cam03)

        self.uvc_cam04 = QWidget(self)
        self.uvcCam04_Layout = QHBoxLayout(self.uvc_cam04)
        self.uvcCam04_vLayout = QVBoxLayout(self.uvc_cam04)
        self.uvcCam04_Label = QLabel(self.tr("UVC Camera 05: Backward Viewing Eye"),self.uvc_cam04)
        self.uvcCam04_Content = QLabel(self.tr("165 degree lagre field of view, monitoring the whole ROV for pilot."), self.uvc_cam04)
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
        self.uvcCam00_Content.setObjectName('contentLabel')
        self.uvcCam01_Label.setObjectName("titleLabel")
        self.uvcCam01_Content.setObjectName('contentLabel')
        self.uvcCam02_Label.setObjectName("titleLabel")
        self.uvcCam02_Content.setObjectName('contentLabel')
        self.uvcCam03_Label.setObjectName("titleLabel")
        self.uvcCam03_Content.setObjectName('contentLabel')
        self.uvcCam04_Label.setObjectName("titleLabel")
        self.uvcCam04_Content.setObjectName('contentLabel')
        self.checkLabel.setObjectName("titleLabel")

        self.uvcCam00_Address.addItems(self.uvcAddress_items)
        self.uvcCam01_Address.addItems(self.uvcAddress_items)
        self.uvcCam02_Address.addItems(self.uvcAddress_items)
        self.uvcCam03_Address.addItems(self.uvcAddress_items)
        self.uvcCam04_Address.addItems(self.uvcAddress_items)

        self.__updateItems()
        self.updateStatus()

        self.mjpgStreamer_Address.editingFinished.connect(lambda: self.changeConfig("mjpgStreamerAddress"))
        self.uvcCam00_Enabled.checkedChanged.connect(lambda: self.changeConfig("Cam00CheckEnable"))
        self.uvcCam00_Address.currentIndexChanged.connect(lambda: self.changeConfig("Cam00AddressChange"))
        
        self.uvcCam01_Enabled.checkedChanged.connect(lambda: self.changeConfig("Cam01CheckEnable"))
        self.uvcCam01_Address.currentIndexChanged.connect(lambda: self.changeConfig("Cam01AddressChange"))
        
        self.uvcCam02_Enabled.checkedChanged.connect(lambda: self.changeConfig("Cam02CheckEnable"))
        self.uvcCam02_Address.currentIndexChanged.connect(lambda: self.changeConfig("Cam02AddressChange"))
        
        self.uvcCam03_Enabled.checkedChanged.connect(lambda: self.changeConfig("Cam03CheckEnable"))
        self.uvcCam03_Address.currentIndexChanged.connect(lambda: self.changeConfig("Cam03AddressChange"))
        
        self.uvcCam04_Enabled.checkedChanged.connect(lambda: self.changeConfig("Cam04CheckEnable"))
        self.uvcCam04_Address.currentIndexChanged.connect(lambda: self.changeConfig("Cam04AddressChange"))

        self.checkButton.clicked.connect(self.updateStatus)
        self.detailButton.clicked.connect(self.__viewConDetail)

    def checkCamConnection(self, url):
        try:
            # 使用流式请求，避免一次性下载所有数据
            with requests.get(url, stream=True, timeout=5) as response:
                # 检查响应状态
                if response.status_code == 200:
                    success = True
                    self.connectionStatus &= True
                else:
                    success = False
                    self.connectionStatus &= False

                # 提取常规 HTTP 信息
                request_information = {
                    "requestURL": response.request.url,
                    "requestMethod": response.request.method,
                    "statusCode": response.status_code,
                    "referrerPolicy": "no-referrer"  # 假设没有引用站点策略
                }

                # 提取请求标头中的特定内容
                request_headers = {
                    "Accept": response.request.headers.get("Accept", "Not Specified"),
                    "UserAgent": response.request.headers.get("User-Agent", "Not Specified")
                }

                # 提取响应标头中的特定内容
                response_headers = {
                    "cache-control": response.headers.get("Cache-Control", "Not Specified"),
                    "content-type": response.headers.get("Content-Type", "Not Specified"),
                    "server": response.headers.get("Server", "Not Specified")
                }

                # 记录当前时间
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                return {
                    "connectionStatus": success,
                    "requestInformation": request_information,
                    "requestHeaders": request_headers,
                    "responseHeaders": response_headers,
                    "datetime": timestamp
                }
        except requests.exceptions.Timeout:
            self.connectionStatus &= False
            return {
                "connectionStatus": False,
                "errorMessage": "Connection timed out"
            }
        except requests.exceptions.RequestException as e:
            self.connectionStatus &= False
            return {
                "connectionStatus": False,
                "errorMessage": f"Request failed: {str(e)}"
            }

    @pyqtSlot()
    def changeConfig(self, terms):
        if terms == "mjpgStreamerAddress":
            print(self.mjpgStreamer_Address.text())
            qconfig.set(self.configItems.mjpgServerAddress, self.mjpgStreamer_Address.text())
        
        elif terms == "Cam00CheckEnable":
            print(self.uvcCam00_Enabled.isChecked())
            qconfig.set(self.configItems.uvcCam00_Enabled, self.uvcCam00_Enabled.isChecked())
            self.uvcCam00_Address.setEnabled(self.uvcCam00_Enabled.isChecked())
        elif terms == "Cam00AddressChange":
            print(self.uvcCam00_Address.currentIndex())
            qconfig.set(self.configItems.uvcCam00_Address, 
                        self.uvcAddress_items[self.uvcCam00_Address.currentIndex()])
            
        elif terms == "Cam01CheckEnable":
            print(self.uvcCam01_Enabled.isChecked())
            qconfig.set(self.configItems.uvcCam01_Enabled, self.uvcCam01_Enabled.isChecked())
            self.uvcCam01_Address.setEnabled(self.uvcCam01_Enabled.isChecked())
        elif terms == "Cam01AddressChange":
            print(self.uvcCam01_Address.currentIndex())
            qconfig.set(self.configItems.uvcCam01_Address, 
                        self.uvcAddress_items[self.uvcCam01_Address.currentIndex()])
            
        elif terms == "Cam02CheckEnable":
            print(self.uvcCam02_Enabled.isChecked())
            qconfig.set(self.configItems.uvcCam02_Enabled, self.uvcCam02_Enabled.isChecked())
            self.uvcCam02_Address.setEnabled(self.uvcCam02_Enabled.isChecked())
        elif terms == "Cam02AddressChange":
            print(self.uvcCam02_Address.currentIndex())
            qconfig.set(self.configItems.uvcCam02_Address, 
                        self.uvcAddress_items[self.uvcCam02_Address.currentIndex()])
            
        elif terms == "Cam03CheckEnable":
            print(self.uvcCam03_Enabled.isChecked())
            qconfig.set(self.configItems.uvcCam03_Enabled, self.uvcCam03_Enabled.isChecked())
            self.uvcCam03_Address.setEnabled(self.uvcCam03_Enabled.isChecked())
        elif terms == "Cam03AddressChange":
            print(self.uvcCam03_Address.currentIndex())
            qconfig.set(self.configItems.uvcCam03_Address, 
                        self.uvcAddress_items[self.uvcCam03_Address.currentIndex()])
            
        elif terms == "Cam04CheckEnable":
            print(self.uvcCam04_Enabled.isChecked())
            qconfig.set(self.configItems.uvcCam04_Enabled, self.uvcCam04_Enabled.isChecked())
            self.uvcCam04_Address.setEnabled(self.uvcCam04_Enabled.isChecked())
        elif terms == "Cam04AddressChange":
            print(self.uvcCam04_Address.currentIndex())
            qconfig.set(self.configItems.uvcCam04_Address, 
                        self.uvcAddress_items[self.uvcCam04_Address.currentIndex()])

    @pyqtSlot()
    @threaded_func
    def updateStatus(self):
        self.checkButton.setEnabled(False)
        self.detailButton.setEnabled(False)
        self.checkLabel.setText(self.tr("Checking Connection: "))
        self.checkLabel.adjustSize()
        self.checkingBar.show()

        start_time = time.time()
        self.connectionStatus = True
        with ThreadPoolExecutor(max_workers=5) as pool:
            if qconfig.get(self.configItems.uvcCam00_Enabled):
                self.resultCam00 = pool.submit(self.checkCamConnection,
                    qconfig.get(self.configItems.mjpgServerAddress) + 
                    qconfig.get(self.configItems.uvcCam00_Address)).result()
            else: self.resultCam00 = {"connectionStatus": "None"}

            if qconfig.get(self.configItems.uvcCam01_Enabled):
                self.resultCam01 = pool.submit(self.checkCamConnection,
                    qconfig.get(self.configItems.mjpgServerAddress) + 
                    qconfig.get(self.configItems.uvcCam01_Address)).result()
            else: self.resultCam01 = {"connectionStatus": "None"}

            if qconfig.get(self.configItems.uvcCam02_Enabled):
                self.resultCam02 = pool.submit(self.checkCamConnection,
                    qconfig.get(self.configItems.mjpgServerAddress) + 
                    qconfig.get(self.configItems.uvcCam02_Address)).result()
            else: self.resultCam02 = {"connectionStatus": "None"}

            if qconfig.get(self.configItems.uvcCam03_Enabled):
                self.resultCam03 = pool.submit(self.checkCamConnection,
                    qconfig.get(self.configItems.mjpgServerAddress) + 
                    qconfig.get(self.configItems.uvcCam03_Address)).result()
            else: self.resultCam03 = {"connectionStatus": "None"}

            if qconfig.get(self.configItems.uvcCam04_Enabled):
                self.resultCam04 = pool.submit(self.checkCamConnection,
                    qconfig.get(self.configItems.mjpgServerAddress) + 
                    qconfig.get(self.configItems.uvcCam04_Address)).result()
            else: self.resultCam04 = {"connectionStatus": "None"}
        loop = QEventLoop()
        QTimer.singleShot(int(max((1 - time.time() + start_time) * 1000, 0)), loop.quit)
        loop.exec_()

        print(self.connectionStatus)
        self.checkingBar.hide()
        if self.connectionStatus:
            self.checkLabel.setText(self.tr("Connection Status: Success!"))
        else: 
            self.checkLabel.setText(self.tr("Connection Status: Failed! "))
        
        self.checkButton.setEnabled(True)
        self.detailButton.setEnabled(True)
        self.checkLabel.adjustSize()
        self._adjustViewSize()

    def __viewConDetail(self):
        w = cameraConDetailBox(
            [self.resultCam00, self.resultCam01, self.resultCam02, 
             self.resultCam03, self.resultCam04],
            self.window())
        w.show()
        w.autoResize_TextBrowser(w.uvcCam00_Text)
        w.autoResize_TextBrowser(w.uvcCam01_Text)
        w.autoResize_TextBrowser(w.uvcCam02_Text)
        w.autoResize_TextBrowser(w.uvcCam03_Text)
        w.autoResize_TextBrowser(w.uvcCam04_Text)

    def __updateItems(self):
        self.mjpgStreamer_Address.setText(qconfig.get(self.configItems.mjpgServerAddress))
        self.mjpgStreamer_Address.setPlaceholderText(qconfig.get(self.configItems.mjpgServerAddress))
        self.mjpgStreamer_Address.setClearButtonEnabled(True)

        self.uvcCam00_Enabled.setChecked(qconfig.get(self.configItems.uvcCam00_Enabled))
        self.uvcCam01_Enabled.setChecked(qconfig.get(self.configItems.uvcCam01_Enabled))
        self.uvcCam02_Enabled.setChecked(qconfig.get(self.configItems.uvcCam02_Enabled))
        self.uvcCam03_Enabled.setChecked(qconfig.get(self.configItems.uvcCam03_Enabled))
        self.uvcCam04_Enabled.setChecked(qconfig.get(self.configItems.uvcCam04_Enabled))

        self.uvcCam00_Address.setEnabled(qconfig.get(self.configItems.uvcCam00_Enabled))
        self.uvcCam01_Address.setEnabled(qconfig.get(self.configItems.uvcCam01_Enabled))
        self.uvcCam02_Address.setEnabled(qconfig.get(self.configItems.uvcCam02_Enabled))
        self.uvcCam03_Address.setEnabled(qconfig.get(self.configItems.uvcCam03_Enabled))
        self.uvcCam04_Address.setEnabled(qconfig.get(self.configItems.uvcCam04_Enabled))

        self.uvcCam00_Address.setCurrentIndex(
            self.uvcAddress_items.index(qconfig.get(self.configItems.uvcCam00_Address)))
        self.uvcCam01_Address.setCurrentIndex(
            self.uvcAddress_items.index(qconfig.get(self.configItems.uvcCam01_Address)))
        self.uvcCam02_Address.setCurrentIndex(
            self.uvcAddress_items.index(qconfig.get(self.configItems.uvcCam02_Address)))
        self.uvcCam03_Address.setCurrentIndex(
            self.uvcAddress_items.index(qconfig.get(self.configItems.uvcCam03_Address)))
        self.uvcCam04_Address.setCurrentIndex(
            self.uvcAddress_items.index(qconfig.get(self.configItems.uvcCam04_Address)))

    def __initLayout(self):
        self.mjpgStreamer_Layout.setContentsMargins(48, 18, 44, 18)
        self.mjpgStreamer_Layout.addWidget(self.mjpgStreamer_Label, 0, Qt.AlignLeft)
        self.mjpgStreamer_Layout.addSpacing(50)
        self.mjpgStreamer_Layout.addWidget(self.mjpgStreamer_Address, 1)
        self.mjpgStreamer_Layout.addSpacing(15)
        self.mjpgStreamer_Layout.addWidget(self.editButton, 0, Qt.AlignRight)

        self.uvcCam00_Layout.setContentsMargins(48, 18, 44, 18)
        self.uvcCam00_Layout.addWidget(get_IconLabel(AppIcon.WEB_CAMERA, (20, 22)), 0, Qt.AlignLeft)
        self.uvcCam00_Layout.addSpacing(8)
        self.uvcCam00_vLayout.setSpacing(0)
        self.uvcCam00_vLayout.addWidget(self.uvcCam00_Label, 0, Qt.AlignLeft)
        self.uvcCam00_vLayout.addWidget(self.uvcCam00_Content, 0, Qt.AlignLeft)
        self.uvcCam00_Layout.addLayout(self.uvcCam00_vLayout)
        self.uvcCam00_Layout.addStretch()
        self.uvcCam00_Layout.addWidget(self.uvcCam00_Enabled, 0, Qt.AlignRight)
        self.uvcCam00_Layout.addSpacing(15)
        self.uvcCam00_Address.setFixedWidth(180)
        self.uvcCam00_Layout.addWidget(self.uvcCam00_Address, 0, Qt.AlignRight)

        self.uvcCam01_Layout.setContentsMargins(48, 18, 44, 18)
        self.uvcCam01_Layout.addWidget(get_IconLabel(AppIcon.WEB_CAMERA, (20, 22)), 0, Qt.AlignLeft)
        self.uvcCam01_Layout.addSpacing(8)
        self.uvcCam01_vLayout.setSpacing(0)
        self.uvcCam01_vLayout.addWidget(self.uvcCam01_Label, 0, Qt.AlignLeft)
        self.uvcCam01_vLayout.addWidget(self.uvcCam01_Content, 0, Qt.AlignLeft)
        self.uvcCam01_Layout.addLayout(self.uvcCam01_vLayout)
        self.uvcCam01_Layout.addStretch()
        self.uvcCam01_Layout.addWidget(self.uvcCam01_Enabled, 0, Qt.AlignRight)
        self.uvcCam01_Layout.addSpacing(15)
        self.uvcCam01_Address.setFixedWidth(180)
        self.uvcCam01_Layout.addWidget(self.uvcCam01_Address, 0, Qt.AlignRight)

        self.uvcCam02_Layout.setContentsMargins(48, 18, 44, 18)
        self.uvcCam02_Layout.addWidget(get_IconLabel(AppIcon.WEB_CAMERA, (20, 22)), 0, Qt.AlignLeft)
        self.uvcCam02_Layout.addSpacing(8)
        self.uvcCam02_vLayout.setSpacing(0)
        self.uvcCam02_vLayout.addWidget(self.uvcCam02_Label, 0, Qt.AlignLeft)
        self.uvcCam02_vLayout.addWidget(self.uvcCam02_Content, 0, Qt.AlignLeft)
        self.uvcCam02_Layout.addLayout(self.uvcCam02_vLayout)
        self.uvcCam02_Layout.addStretch()
        self.uvcCam02_Layout.addWidget(self.uvcCam02_Enabled, 0, Qt.AlignRight)
        self.uvcCam02_Layout.addSpacing(15)
        self.uvcCam02_Address.setFixedWidth(180)
        self.uvcCam02_Layout.addWidget(self.uvcCam02_Address, 0, Qt.AlignRight)

        self.uvcCam03_Layout.setContentsMargins(48, 18, 44, 18)
        self.uvcCam03_Layout.addWidget(get_IconLabel(AppIcon.WEB_CAMERA, (20, 22)), 0, Qt.AlignLeft)
        self.uvcCam03_Layout.addSpacing(8)
        self.uvcCam03_vLayout.setSpacing(0)
        self.uvcCam03_vLayout.addWidget(self.uvcCam03_Label, 0, Qt.AlignLeft)
        self.uvcCam03_vLayout.addWidget(self.uvcCam03_Content, 0, Qt.AlignLeft)
        self.uvcCam03_Layout.addLayout(self.uvcCam03_vLayout)
        self.uvcCam03_Layout.addStretch()
        self.uvcCam03_Layout.addWidget(self.uvcCam03_Enabled, 0, Qt.AlignRight)
        self.uvcCam03_Layout.addSpacing(15)
        self.uvcCam03_Address.setFixedWidth(180)
        self.uvcCam03_Layout.addWidget(self.uvcCam03_Address, 0, Qt.AlignRight)

        self.uvcCam04_Layout.setContentsMargins(48, 18, 44, 18)
        self.uvcCam04_Layout.addWidget(get_IconLabel(AppIcon.WEB_CAMERA, (20, 22)), 0, Qt.AlignLeft)
        self.uvcCam04_Layout.addSpacing(8)
        self.uvcCam04_vLayout.setSpacing(0)
        self.uvcCam04_vLayout.addWidget(self.uvcCam04_Label, 0, Qt.AlignLeft)
        self.uvcCam04_vLayout.addWidget(self.uvcCam04_Content, 0, Qt.AlignLeft)
        self.uvcCam04_Layout.addLayout(self.uvcCam04_vLayout)
        self.uvcCam04_Layout.addStretch()
        self.uvcCam04_Layout.addWidget(self.uvcCam04_Enabled, 0, Qt.AlignRight)
        self.uvcCam04_Layout.addSpacing(15)
        self.uvcCam04_Address.setFixedWidth(180)
        self.uvcCam04_Layout.addWidget(self.uvcCam04_Address, 0, Qt.AlignRight)

        self.checkLayout.setContentsMargins(48, 18, 44, 18)
        self.checkLayout.addWidget(get_IconLabel(AppIcon.CONNECT, (24, 20)), 0, Qt.AlignLeft)
        self.checkLayout.addSpacing(4)
        self.checkLayout.addWidget(self.checkLabel, 0, Qt.AlignLeft | Qt.AlignCenter)
        self.checkLayout.addWidget(self.checkingBar, 0, Qt.AlignLeft | Qt.AlignCenter)
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
    
    def toggleExpand(self):
        """ toggle expand status """
        self.setExpand(not self.isExpand)
        self._adjustViewSize()

class cameraConDetailBox(MessageBoxBase):
    def __init__(self, resultCam: list, parent=None):
        super().__init__(parent)
        
        self.titleLabel = SubtitleLabel(self.tr('Cameras Connection Details'), self)
        
        self.scrollArea = SingleDirectionScrollArea(self, orient=Qt.Vertical)
        self.scrollArea.setWidgetResizable(True)
        
        self.InfoWidget = QWidget(self)
        self.InfoLayout = QVBoxLayout(self.InfoWidget)

        self.uvcCam00 = BodyLabel(self.tr("Connection Status for UVC Camera 01"))
        self.uvcCam00_Text = TextBrowser()
        self.uvcCam00_Text.setText(json.dumps(resultCam[0], indent=4, ensure_ascii=False))
        # self.uvcCam00_Text.setMarkdown(json.dumps(resultCam00, indent=4, ensure_ascii=False))

        self.uvcCam01 = BodyLabel(self.tr("Connection Status for UVC Camera 02"))
        self.uvcCam01_Text = TextBrowser()
        self.uvcCam01_Text.setText(json.dumps(resultCam[1], indent=4, ensure_ascii=False))

        self.uvcCam02 = BodyLabel(self.tr("Connection Status for UVC Camera 03"))
        self.uvcCam02_Text = TextBrowser()
        self.uvcCam02_Text.setText(json.dumps(resultCam[2], indent=4, ensure_ascii=False))

        self.uvcCam03 = BodyLabel(self.tr("Connection Status for UVC Camera 04"))
        self.uvcCam03_Text = TextBrowser()
        self.uvcCam03_Text.setText(json.dumps(resultCam[3], indent=4, ensure_ascii=False))

        self.uvcCam04 = BodyLabel(self.tr("Connection Status for UVC Camera 05"))
        self.uvcCam04_Text = TextBrowser()
        self.uvcCam04_Text.setText(json.dumps(resultCam[4], indent=4, ensure_ascii=False))
        
        self.viewLayout.addWidget(self.titleLabel)
        
        self.InfoLayout.addWidget(self.uvcCam00)
        self.InfoLayout.addWidget(self.uvcCam00_Text)
        self.InfoLayout.addWidget(self.uvcCam01)
        self.InfoLayout.addWidget(self.uvcCam01_Text)
        self.InfoLayout.addWidget(self.uvcCam02)
        self.InfoLayout.addWidget(self.uvcCam02_Text)
        self.InfoLayout.addWidget(self.uvcCam03)
        self.InfoLayout.addWidget(self.uvcCam03_Text)
        self.InfoLayout.addWidget(self.uvcCam04)
        self.InfoLayout.addWidget(self.uvcCam04_Text)

        self.scrollArea.setWidget(self.InfoWidget)
        self.scrollArea.enableTransparentBackground()
        self.viewLayout.addWidget(self.scrollArea)
        
        self.widget.setMinimumWidth(450)

    @staticmethod
    def autoResize_TextBrowser(text_browser: TextBrowser):
        # Calculate the height based on document content
        doc = text_browser.document()
        margins = text_browser.contentsMargins()
        total_height = doc.size().height() + margins.top() + margins.bottom()
        text_browser.setFixedHeight(int(total_height + 0.5))  # Round to nearest integer
