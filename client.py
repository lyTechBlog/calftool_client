import asyncio
import websockets
import json
import os
import sys
import argparse
from datetime import datetime
from tools.screen_shoot import screen_shot
from tools.image_tool import image_2_base64
from PyQt6.QtWidgets import (
    QApplication, QInputDialog, QMessageBox, QWidget,
    QVBoxLayout, QLabel, QLineEdit, QDialog, QPushButton
)
from PyQt6.QtCore import QEvent, Qt

PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
sys.path.append(f"{PROJECT_DIR}/src")
from tools.log_module import log

def parse_arguments():
    parser = argparse.ArgumentParser(description="WebSocket client script")
    parser.add_argument('--debug', action='store_true', help="Run in debug mode")
    args = parser.parse_args()
    
    # Set domain based on debug mode
    domain = "localhost:15010" if args.debug else "thefreeai.cn"
    uri = f"ws://{domain}/calftoolws"
    log.info(f"Using URI: {uri}")
    
    return args, uri


async def send_data(user_id="test", uri=None, window=None):
    log.info(f"Starting send_data function for user_id: {user_id}")
    while True:
        try:
            log.info(f"Attempting to connect to server at {uri}")
            async with websockets.connect(uri) as websocket:
                log.info(f"User {user_id} successfully connected to server")
                window.showMessage("Success", "Connected to server")
                
                # Send a text message
                text_data = {
                    "user_id": user_id,
                    "type": "text",
                    "content": "Hello, WebSocket!"
                }
                log.info(f"Sending initial hello message for user {user_id}")
                await websocket.send(json.dumps(text_data))
                log.info(f"Hello message sent successfully: {text_data}")
                
                # Listen for messages
                while True:
                    log.info(f"Waiting for server message for user {user_id}")
                    message = await websocket.recv()
                    log.info(f"Received raw message: {message}")
                    data = json.loads(message)
                    
                    if data["type"] == "screen_shoot":
                        log.info(f"Processing screen_shoot request for user {user_id}")
                        
                        try:
                            image_path = screen_shot(image_dir=user_id)
                            log.info(f"Screenshot taken, saved to: {image_path}")
                            
                            image_base64_data = image_2_base64(image_path)
                            log.info(f"Image converted to base64, size: {len(image_base64_data)}")
                            
                            current_time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                            screen_shot_message = {
                                "user_id": user_id,
                                "type": "image",
                                "content": image_base64_data,
                                "file_name": f"{current_time}.png",
                            }
                            log.info(f"Sending screenshot for user {user_id}, filename: {current_time}.png")
                            await websocket.send(json.dumps(screen_shot_message))
                            log.info(f"Screenshot sent successfully, size: {len(image_base64_data)} bytes")
                            
                        except Exception as e:
                            log.error(f"Error processing screenshot: {str(e)}")
                            raise
                    else:
                        log.warning(f"Received unknown message type '{data.get('type')}' from server: {data}")
        
        except (websockets.exceptions.ConnectionClosed, 
                ConnectionRefusedError, 
                OSError) as e:
            log.error(f"Connection error for user {user_id}: {str(e)}")
            log.info(f"Connection error details: {type(e).__name__}: {str(e)}")
            window.showMessage("Error", f"Connection failed: {str(e)}")
            log.info(f"Attempting to reconnect in 3 seconds...")
            await asyncio.sleep(3)
            continue
        except Exception as e:
            log.error(f"Critical error for user {user_id}: {str(e)}")
            log.exception("Full exception details:")
            window.showMessage("Error", f"Unexpected error: {str(e)}")
            while dialog.isVisible():
                await asyncio.sleep(0.1)
            log.info("Dialog closed, exiting application")
            await asyncio.sleep(3)

# Replace the event-based classes with a simple window class
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebSocket Client")
        # Update window flags to completely hide from dock/taskbar
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, False)  # For macOS
        self.status_label = None
        self.dialog = None
        self.hide()
        
    def showMessage(self, title, message):
        if self.dialog:
            if title == "Success":
                self.dialog.status.setText("Status: 链接成功")
                self.dialog.status.setStyleSheet("color: red")
                self.dialog.error_label.setText("")
                self.dialog.updateButtonState(False)
                self.dialog.status.repaint()
            elif title == "Error":
                self.dialog.status.setText("Status: 链接失败")
                self.dialog.status.setStyleSheet("color: red")
                self.dialog.error_label.setText(message)
                self.dialog.updateButtonState(True)
                self.dialog.status.repaint()
            elif title == "Connecting":
                self.dialog.status.setText("Status: 链接中...")
                self.dialog.status.setStyleSheet("color: red")
                self.dialog.error_label.setText("")
                self.dialog.updateButtonState(False)
                self.dialog.status.repaint()

class CustomInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Input")
        layout = QVBoxLayout()
        
        # 添加提示标签
        label = QLabel("Please enter your user ID:")
        layout.addWidget(label)
        
        # 添加输入框
        self.input = QLineEdit("test")
        layout.addWidget(self.input)
        
        # 添加状态标签
        self.status = QLabel("Status: Waiting for connection...")
        layout.addWidget(self.status)
        
        # Add error message label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red")
        layout.addWidget(self.error_label)
        
        # Add permission request button before the OK button
        self.permission_button = QPushButton("同意截屏权限")
        self.permission_button.clicked.connect(self.request_permission)
        layout.addWidget(self.permission_button)
        
        # Add permission status label
        self.permission_status = QLabel("截屏权限: 未授权")
        self.permission_status.setStyleSheet("color: orange")
        layout.addWidget(self.permission_status)
        
        # Move OK button after permission elements
        self.button = QPushButton("开始链接")
        self.button.clicked.connect(self.start_connection)
        self.button.setEnabled(False)  # Disable until permission granted
        layout.addWidget(self.button)
        
        self.setLayout(layout)
        
        # Update status label initial text
        self.status.setStyleSheet("color: black")
        
        # 添加关闭事件处理
        self.closeEvent = self.handleClose
    
    def handleClose(self, event):
        if hasattr(self, 'user_id'):  # 如果已经连接成功
            event.accept()  # 允许关闭
            # 在关闭后将应用程序设置为后台模式
            if sys.platform == 'darwin':
                import AppKit
                AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyProhibited)
        else:
            # 如果还未连接，阻止关闭
            event.ignore()
    
    def start_connection(self):
        self.user_id = self.input.text() or "test"
        self.updateButtonState(False)
        self.status.setText("Status: Connecting to server...")
    
    def updateButtonState(self, enabled):
        """Update the state of input and button"""
        self.input.setEnabled(enabled)
        self.button.setEnabled(enabled)
    
    def showError(self, message):
        self.error_label.setText(message)
    
    def request_permission(self):
        try:
            if sys.platform == 'darwin':
                # macOS specific permission request
                import Quartz
                # This will trigger the permission prompt
                Quartz.CGWindowListCreateImage(
                    Quartz.CGRectInfinite,
                    Quartz.kCGWindowListOptionOnScreenOnly,
                    Quartz.kCGNullWindowID,
                    Quartz.kCGWindowImageDefault
                )
            else:
                # For Windows/Linux, take a test screenshot
                screen_shot(image_dir="test")
            
            self.permission_status.setText("Screenshot Permission: Granted")
            self.permission_status.setStyleSheet("color: green")
            self.button.setEnabled(True)
            self.permission_button.setEnabled(False)
            
        except Exception as e:
            self.permission_status.setText(f"Permission Error: {str(e)}")
            self.permission_status.setStyleSheet("color: red")
            self.button.setEnabled(False)

if __name__ == "__main__":
    args, uri = parse_arguments()
    log.info(f"Application starting with URI: {uri}")
    
    try:
        app = QApplication(sys.argv)
        # 初始时设置为常规模式以显示对话框
        if sys.platform == 'darwin':
            import AppKit
            AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
        
        log.info("QApplication initialized")
        window = MainWindow()
        dialog = CustomInputDialog()
        window.dialog = dialog
        log.info("GUI components initialized")
        
        dialog.show()
        log.info("Input dialog displayed")
        
        # 修改异步任务以处理对话框关闭后的状态
        async def main():
            while not hasattr(dialog, 'user_id'):
                await asyncio.sleep(0.1)
                app.processEvents()
            
            # 连接成功后继续运行
            await send_data(user_id=dialog.user_id, uri=uri, window=window)
        
        # 使用 asyncio.run() 替代 run_until_complete
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 启动异步任务
            future = asyncio.ensure_future(main())
            
            # 同时运行 Qt 事件循环和 asyncio 事件循环
            while not future.done():
                app.processEvents()
                loop.run_until_complete(asyncio.sleep(0.1))
                
        except KeyboardInterrupt:
            print("\nShutting down client...")
        except Exception as e:
            log.error(f"Main loop error: {str(e)}")
            window.showMessage("Error", f"Connection error: {str(e)}")
            sys.exit(1)
    except Exception as e:
        log.critical(f"Fatal error during application startup: {str(e)}")
        log.exception("Full exception details:")
        sys.exit(1)