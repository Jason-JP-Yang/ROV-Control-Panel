from typing import Union
from qfluentwidgets import (SegmentedWidget, SimpleCardWidget,
                            OptionsSettingCard, HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, CustomColorSettingCard,
                            setTheme, setThemeColor, PushButton, InfoBarPosition)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QDesktopServices, QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QStackedWidget, QHBoxLayout, QSizePolicy

from ..components.custom_ssh_setting_card import CustomSSHSettingCard
from ..components.custom_cam_setting_card import CustomCameraSettingCard

from ..common.config import cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR, RELEASE_URL, isWin11
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..common.icon import Icon as AppIcon, get_IconLabel

import requests, time

class VideoStreamWorker(QObject):
    new_frame = pyqtSignal(QImage, float, float, float)  # 图像数据，延迟，即时FPS，平均FPS
    finished = pyqtSignal()

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.running = True

    def parse_headers(self, header_block: bytes):
        headers = {}
        for line in header_block.split(b'\r\n'):
            if line:
                parts = line.split(b': ', 1)
                if len(parts) == 2:
                    key = parts[0].decode().strip().lower()
                    value = parts[1].decode().strip()
                    headers[key] = value
        return headers

    def run(self):
        try:
            response = requests.get(self.url, stream=True, timeout=5)
            content_type = response.headers.get('Content-Type', '')
            boundary = content_type.split('boundary=')[-1].strip().strip('"')
            boundary_marker = b'--' + boundary.encode()

            # 统计变量
            start_time = time.time()
            last_frame_time = None
            total_processing_time = 0.0
            frame_count = 0

            buffer = b''
            state = '寻找边界'
            remaining_bytes = 0
            image_data = b''

            for chunk in response.iter_content(chunk_size=4096):
                if not self.running:
                    break
                
                if chunk:
                    buffer += chunk
                
                while self.running:
                    if state == '寻找边界':
                        boundary_pos = buffer.find(boundary_marker)
                        if boundary_pos == -1:
                            break
                        
                        if boundary_pos == 0 or (boundary_pos >= 2 and buffer[boundary_pos-2:boundary_pos] == b'\r\n'):
                            buffer = buffer[boundary_pos + len(boundary_marker):]
                            state = '读取头部'
                        else:
                            buffer = buffer[boundary_pos + 1:]
                    
                    elif state == '读取头部':
                        header_end = buffer.find(b'\r\n\r\n')
                        if header_end == -1:
                            break
                        
                        header_block = buffer[:header_end]
                        buffer = buffer[header_end + 4:]
                        headers = self.parse_headers(header_block)
                        
                        content_length = int(headers.get('content-length', 0))
                        if content_length <= 0:
                            state = '寻找边界'
                            continue
                        
                        remaining_bytes = content_length
                        image_data = b''
                        state = '读取数据'
                        frame_start = time.time()
                    
                    elif state == '读取数据':
                        if len(buffer) >= remaining_bytes:
                            image_data += buffer[:remaining_bytes]
                            buffer = buffer[remaining_bytes:]
                            
                            # 计算统计信息
                            current_time = time.time()
                            processing_delay = current_time - frame_start
                            total_processing_time += processing_delay
                            
                            # 帧率计算
                            instant_fps = 0.0
                            avg_fps = 0.0
                            if last_frame_time is not None:
                                instant_fps = 1 / max(current_time - last_frame_time, 0.01)
                            if (current_time - start_time) > 0:
                                avg_fps = frame_count / max(current_time - start_time, 0.01)
                            
                            last_frame_time = current_time
                            
                            # 转换为QImage
                            img = QImage()
                            img.loadFromData(image_data)
                            if not img.isNull():
                                self.new_frame.emit(
                                    img,
                                    processing_delay,
                                    instant_fps,
                                    avg_fps
                                )
                            
                            frame_count += 1
                            state = '寻找边界'
                        else:
                            image_data += buffer
                            remaining_bytes -= len(buffer)
                            buffer = b''
                            break
                    else:
                        break
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            self.finished.emit()

    def stop(self):
        self.running = False

class CamInfoBar(SimpleCardWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mainLayout = QHBoxLayout(self)
        
        self.connect_icon = get_IconLabel(AppIcon.CONNECT, (18, 16))
        self.label = QLabel(self.tr("[INFO]: Collecting information for camera statistic..."), self)
        self.label.setObjectName("CamInfoLabel")

        self.setLayout(self.mainLayout)
        self.setContentsMargins(10, 0, 0, 0)
        self.mainLayout.addWidget(self.connect_icon, 0, Qt.AlignLeft)
        self.mainLayout.addWidget(self.label, 0, Qt.AlignLeft)
        self.mainLayout.addStretch()

        self.setFixedHeight(50)

class StreamArea(SimpleCardWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mainLayout = QVBoxLayout(self)

        self.cam_icon = get_IconLabel(AppIcon.CAMERA, (32, 32))
        self.errLabel = QLabel(self.tr("Error: Lost Connection With Camera!"), self)
        self.videoLabel = QLabel(self)
        self.videoLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.videoLabel.setScaledContents(True)

        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.cam_icon, 0, Qt.AlignCenter)
        self.mainLayout.addWidget(self.videoLabel, 1, Qt.AlignCenter)

        self.cam_icon.hide()
        self.__initStream()
    
    def __initStream(self):
        self.worker = VideoStreamWorker("http://192.168.137.102:8080/?action=stream_0")
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        
        # 连接信号
        self.worker.new_frame.connect(self.update_frame)
        self.worker.finished.connect(self.thread.quit)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.worker.deleteLater)
        
        # 启动线程
        self.thread.start()
    
    def resizeEvent(self, a0):
        self.videoLabel.setFixedSize(self.size())
        return super().resizeEvent(a0)
    
    def update_frame(self, img, delay, instant_fps, avg_fps):
        # 更新视频帧
        pixmap = QPixmap.fromImage(img)
        self.videoLabel.setPixmap(pixmap.scaled(
            self.videoLabel.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

class CamStreamerInterface(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mainLayout = QVBoxLayout(self)
        
        self.camInfoBar = CamInfoBar(self)
        self.videoLabel = StreamArea(self)
        
        self.lowerLayout = QHBoxLayout(self)

        self.__initWidget()
    
    def __initWidget(self):
        
        self.__initLayout()
    
    def __initLayout(self):
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.camInfoBar)

        self.lowerLayout.setContentsMargins(0, 0, 0, 0)
        self.lowerLayout.addWidget(self.videoLabel)
        self.mainLayout.addLayout(self.lowerLayout)

class CameraInterface(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mainLayout = QVBoxLayout(self)

        self.cameraLabel = QLabel(self.tr("UVC Camera 01 -Interface"), self)

        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        # self.streamInterface = QLabel('Stream Camera Interface', self)
        self.streamInterface = CamStreamerInterface(self)
        self.albumInterface = QLabel('Album Interface', self)
        self.artistInterface = QLabel('Artist Interface', self)

        self.addSubInterface(self.streamInterface, 'streamInterface', 'Stream Camera', AppIcon.CAMERA)
        self.addSubInterface(self.albumInterface, 'albumInterface', 'Album')
        self.addSubInterface(self.artistInterface, 'artistInterface', 'Artist')

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(36, 10, 36, 10)

        self.stackedWidget.setCurrentWidget(self.streamInterface)
        self.pivot.setCurrentItem(self.streamInterface.objectName())
        self.pivot.currentItemChanged.connect(
            lambda k:  self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k)))

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setObjectName('cameraInterface')

        self.cameraLabel.setObjectName('cameraLabel')
        StyleSheet.CAMERA_INTERFACE.apply(self)

        self.__initLayout()
    
    def __initLayout(self):
        self.setLayout(self.mainLayout)
        self.setContentsMargins(30, 30, 30, 10)

        self.mainLayout.addWidget(self.cameraLabel)

        self.mainLayout.addWidget(self.pivot)
        self.mainLayout.addWidget(self.stackedWidget)

    def addSubInterface(self, widget: QLabel, objectName, text, icon: AppIcon = None):
        widget.setObjectName(objectName)
        # widget.setAlignment(Qt.AlignCenter)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text, icon=icon)

        