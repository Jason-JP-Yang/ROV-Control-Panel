import sys
import requests
import time
import cv2
import torch
import numpy as np
import matplotlib
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QHBoxLayout, QVBoxLayout, QWidget

from depth_anything_v2.dpt import DepthAnythingV2

# 深度计算模型初始化
class DepthProcessor:
    def __init__(self, encoder='vits', input_size=518):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.input_size = input_size
        
        model_configs = {
            'vits': {'encoder': 'vits', 'features': 64, 'out_channels': [48, 96, 192, 384]},
            'vitb': {'encoder': 'vitb', 'features': 128, 'out_channels': [96, 192, 384, 768]},
            'vitl': {'encoder': 'vitl', 'features': 256, 'out_channels': [256, 512, 1024, 1024]},
            'vitg': {'encoder': 'vitg', 'features': 384, 'out_channels': [1536, 1536, 1536, 1536]}
        }
        
        self.model = DepthAnythingV2(**model_configs[encoder])
        self.model.load_state_dict(
            torch.load(f'checkpoints/depth_anything_v2_{encoder}.pth', map_location='cpu')
        )
        self.model = self.model.to(self.device).eval()
        self.cmap = matplotlib.colormaps.get_cmap('Spectral_r')

    def process_frame(self, frame):
        # 转换图像格式
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # 执行深度预测
        with torch.no_grad():
            depth = self.model.infer_image(frame, self.input_size)
        
        # 后处理
        depth = (depth - depth.min()) / (depth.max() - depth.min()) * 255.0
        depth = depth.astype(np.uint8)
        depth_color = (self.cmap(depth)[:, :, :3] * 255)[:, :, ::-1].astype(np.uint8)
        return depth_color

class VideoStreamWorker(QObject):
    new_frame = pyqtSignal(np.ndarray, float, float, float)
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
        response = requests.get(self.url, stream=True)
        content_type = response.headers.get('Content-Type', '')
        boundary = content_type.split('boundary=')[-1].strip().strip('"')
        boundary_marker = b'--' + boundary.encode()

        start_time = time.time()
        last_frame_time = None
        total_processing_time = 0.0
        frame_count = 0

        buffer = b''
        state = '寻找边界'
        remaining_bytes = 0
        image_data = b''

        try:
            for chunk in response.iter_content(chunk_size=16384):
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

                            # 转换为OpenCV格式
                            frame = cv2.imdecode(
                                np.frombuffer(image_data, dtype=np.uint8), 
                                cv2.IMREAD_COLOR
                            )

                            # 计算统计信息
                            current_time = time.time()
                            processing_delay = current_time - frame_start
                            total_processing_time += processing_delay

                            instant_fps = 0.0
                            avg_fps = 0.0
                            if last_frame_time is not None:
                                instant_fps = 1 / max((current_time - last_frame_time), 0.01)
                            if (current_time - start_time) > 0:
                                avg_fps = frame_count / max((current_time - start_time), 0.01)

                            last_frame_time = current_time

                            # 发射信号
                            if frame is not None:
                                self.new_frame.emit(
                                    frame,
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

class DepthWorker(QThread):
    depth_ready = pyqtSignal(np.ndarray)

    def __init__(self, processor):
        super().__init__()
        self.processor = processor
        self.queue = []
        self.running = True

    def run(self):
        while self.running:
            if len(self.queue) > 0:
                frame = self.queue.pop(0)
                depth = self.processor.process_frame(frame)
                self.depth_ready.emit(depth)

    def add_frame(self, frame):
        if len(self.queue) < 3:  # 限制队列长度防止堆积
            self.queue.append(frame)

    def stop(self):
        self.running = False

class MainWindow(QMainWindow):
    def __init__(self, stream_url):
        super().__init__()
        self.setWindowTitle("实时深度流媒体分析")
        self.setGeometry(100, 100, 1600, 600)

        # 初始化深度处理器
        self.depth_processor = DepthProcessor()
        
        # 创建UI组件
        self.video_label = QLabel(self)
        self.depth_label = QLabel(self)
        self.stats_label = QLabel("统计信息加载中...")
        
        # 布局设置
        video_layout = QHBoxLayout()
        video_layout.addWidget(self.video_label)
        video_layout.addWidget(self.depth_label)

        main_layout = QVBoxLayout()
        main_layout.addLayout(video_layout)
        main_layout.addWidget(self.stats_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 视频流线程
        self.video_worker = VideoStreamWorker(stream_url)
        self.video_thread = QThread()
        self.video_worker.moveToThread(self.video_thread)
        
        # 深度计算线程
        self.depth_worker = DepthWorker(self.depth_processor)
        self.depth_thread = QThread()
        self.depth_worker.moveToThread(self.depth_thread)

        # 信号连接
        self.video_worker.new_frame.connect(self.process_video_frame)
        self.depth_worker.depth_ready.connect(self.update_depth_frame)
        self.video_thread.started.connect(self.video_worker.run)
        self.video_thread.finished.connect(self.video_worker.deleteLater)
        self.depth_thread.started.connect(self.depth_worker.run)

        # 启动线程
        self.video_thread.start()
        self.depth_thread.start()

    def process_video_frame(self, frame, delay, instant_fps, avg_fps):
        # 更新原始视频帧
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        q_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

        # 提交深度计算
        self.depth_worker.add_frame(frame.copy())

        # 更新统计信息
        stats_text = f"""
        当前帧延迟: {delay*1000:.1f} ms | 即时帧率: {instant_fps:.2f} FPS
        平均帧率: {avg_fps:.2f} FPS | 计算队列: {len(self.depth_worker.queue)}
        """
        self.stats_label.setText(stats_text)

    def update_depth_frame(self, depth_frame):
        # 更新深度图显示
        rgb_depth = cv2.cvtColor(depth_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_depth.shape
        q_img = QImage(rgb_depth.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.depth_label.setPixmap(pixmap.scaled(
            self.depth_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    def closeEvent(self, event):
        self.video_worker.stop()
        self.depth_worker.stop()
        self.video_thread.quit()
        self.depth_thread.quit()
        self.video_thread.wait()
        self.depth_thread.wait()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stream_url = "http://192.168.137.102:8080/?action=stream_0"  # 替换实际URL
    w1 = MainWindow(stream_url)
    w1.show()

    # w2 = MainWindow(stream_url)
    # w2.show()
    sys.exit(app.exec_())