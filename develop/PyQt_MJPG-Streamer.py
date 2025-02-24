import sys
import requests
import time
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

class VideoStreamWorker(QObject):
    new_frame = pyqtSignal(QImage, float, float, float)  # 图像数据，延迟，即时FPS，平均FPS
    finished = pyqtSignal()

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.running = True

    def parse_headers(self, header_block):
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

class MainWindow(QMainWindow):
    def __init__(self, stream_url):
        super().__init__()
        self.setWindowTitle("MJPEG 流媒体播放器")
        self.setGeometry(100, 100, 800, 600)

        # 创建UI组件
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        
        self.stats_label = QLabel("统计信息加载中...")
        self.stats_label.setAlignment(Qt.AlignLeft)

        # 布局设置
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.stats_label)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 初始化视频流线程
        self.worker = VideoStreamWorker(stream_url)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        
        # 连接信号
        self.worker.new_frame.connect(self.update_frame)
        self.worker.finished.connect(self.thread.quit)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.worker.deleteLater)
        
        # 启动线程
        self.thread.start()

    def update_frame(self, img, delay, instant_fps, avg_fps):
        # 更新视频帧
        pixmap = QPixmap.fromImage(img)
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

        # 更新统计信息
        stats_text = f"""
        当前帧延迟: {delay*1000:.1f} ms
        即时帧率: {instant_fps:.2f} FPS
        平均帧率: {avg_fps:.2f} FPS
        """
        self.stats_label.setText(stats_text)

    def closeEvent(self, event):
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stream_url = "http://192.168.137.102:8080/?action=stream_0"  # 替换为实际URL
    w1 = MainWindow(stream_url)
    w1.show()

    stream_url_2 = "http://192.168.137.102:8080/?action=stream_1"
    w2 = MainWindow(stream_url_2)
    w2.show()
    sys.exit(app.exec_())