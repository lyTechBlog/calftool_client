# -*- coding: utf-8 -*-
import asyncio
import websockets
import json
import os
import sys
import argparse
from datetime import datetime, timedelta
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

BETA_CODE_FILE = os.path.join(PROJECT_DIR, "beta_code")

def parse_arguments():
    parser = argparse.ArgumentParser(description="WebSocket client script")
    parser.add_argument('--debug', action='store_true', help="Run in debug mode")
    args = parser.parse_args()
    
    # Set domain based on debug mode
    domain = "localhost:15010" if args.debug else "thefreeai.cn"
    uri = f"ws://{domain}/calftoolws"
    log.info(f"Using URI: {uri}")
    
    return args, uri


async def send_data(user_id="", uri=None, window=None):
    log.info(f"Starting send_data function for user_id: {user_id}")
    reconnect_start_time = datetime.now()
    
    while True:
        try:
            if (datetime.now() - reconnect_start_time) > timedelta(hours=2):
                log.error("Reconnection attempts exceeded 2 hour limit")
                window.showMessage("Error", "连接尝试已超过2小时")
                window.dialog.updateButtonState(True)
                return "connection_timeout"

            log.info(f"Attempting to connect to server at {uri}")
            async with websockets.connect(uri) as websocket:
                reconnect_start_time = datetime.now()
                log.info(f"User {user_id} successfully connected to server")
                window.showMessage("Success", "成功连接到服务器")
                
                # Send a text message
                text_data = {
                    "user_id": user_id,
                    "type": "text",
                    "content": "你好，WebSocket！"
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
                    
                    # Add check for user verification failure
                    if data["type"] == "error" and "Invalid user_id" in data.get("message", ""):
                        log.error(f"User verification failed for user_id: {user_id}")
                        window.showMessage("Error", "用户ID无效")
                        window.dialog.updateButtonState(True)  # Re-enable the input
                        return "invalid_user_id"  # Exit completely without retrying
                    
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
            window.showMessage("Error", f"连接失败: {str(e)}")
            log.info("30秒后尝试重新连接...")
            await asyncio.sleep(30)
            continue
        except Exception as e:
            log.error(f"Critical error for user {user_id}: {str(e)}")
            log.exception("Full exception details:")
            window.showMessage("Error", f"发生意外错误: {str(e)}")
            while dialog.isVisible():
                await asyncio.sleep(0.1)
            log.info("对话框已关闭，正在退出应用程序")
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
                self.dialog.status.setText("状态: 连接成功")
                self.dialog.status.setStyleSheet("color: green")
                self.dialog.error_label.setText("")
                self.dialog.updateButtonState(False)
                self.dialog.status.repaint()
                self.dialog.exit_button.setEnabled(True)
            elif title == "Error":
                self.dialog.status.setText("状态: 连接失败")
                self.dialog.status.setStyleSheet("color: red")
                self.dialog.error_label.setText(message)
                self.dialog.updateButtonState(True)  # 重新启用输入
                self.dialog.status.repaint()
                self.dialog.exit_button.setEnabled(False)
            elif title == "Connecting":
                self.dialog.status.setText("状态: 连接中...")
                self.dialog.status.setStyleSheet("color: orange")
                self.dialog.error_label.setText("")
                self.dialog.updateButtonState(False)
                self.dialog.status.repaint()

class CustomInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("远程截图工具")
        layout = QVBoxLayout()
        
        # Define common button style
        button_style = """
            QPushButton {
                background-color: white;
                border: 1px solid gray;
                padding: 5px;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:enabled {
                color: blue;
            }
            QPushButton:disabled {
                color: gray;
            }
        """
        
        # Add first step label
        label = QLabel("第一步：")
        layout.addWidget(label)
        
        # Add input field - modified to always start empty
        self.input = QLineEdit("")
        self.input.setPlaceholderText("请输入内测码")
        self.input.setStyleSheet("QLineEdit::placeholder { color: gray; }")
        layout.addWidget(self.input)
        
        # Add "agree to screen capture permission" button and set style
        self.permission_button = QPushButton("同意截屏权限")
        self.permission_button.clicked.connect(self.request_permission)
        self.permission_button.setEnabled(False)
        self.permission_button.setStyleSheet(button_style)
        
        # Connect text change signal
        self.input.textChanged.connect(self.on_input_text_changed)
        
        # Add error message label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red")
        layout.addWidget(self.error_label)
        
        # Add second step label
        step_two_label = QLabel("第二步：")
        layout.addWidget(step_two_label)
        
        # Now add the "agree to screen capture permission" button to the layout
        layout.addWidget(self.permission_button)
        
        # Initialize permission status label
        self.permission_status = QLabel("截屏权限: 未授权")
        self.permission_status.setStyleSheet("color: orange")
        self.permission_status.hide()
        layout.addWidget(self.permission_status)
        
        # Add third step label
        step_three_label = QLabel("第三步：")
        layout.addWidget(step_three_label)
        
        # Add "connect" button and set style
        self.button = QPushButton("连接")
        self.button.clicked.connect(self.start_connection)
        self.button.setEnabled(False)
        self.button.setStyleSheet(button_style)
        layout.addWidget(self.button)
        
        # Status label
        self.status = QLabel("未连接...")
        self.status.setStyleSheet("color: black")
        layout.addWidget(self.status)
        self.status.hide()
        
        # Add fourth step label
        step_four_label = QLabel("第四步：")
        layout.addWidget(step_four_label)
        
        # Add "run in background" button and set style
        self.exit_button = QPushButton("后台无痕运行")
        self.exit_button.clicked.connect(self.close)
        self.exit_button.setEnabled(False)
        self.exit_button.setStyleSheet(button_style)
        layout.addWidget(self.exit_button)
        
        self.setLayout(layout)
        
        # Add close event handler
        self.closeEvent = self.handleClose
    
    def handleClose(self, event):
        if hasattr(self, 'user_id') and self.status.text() == "状态: 连接成功":
            # Show prompt before minimizing to background
            QMessageBox.information(
                self,
                '提示',
                '程序将在后台继续运行。\n',
                QMessageBox.StandardButton.Ok
            )
            event.accept()  # Allow closing
            # Set application to background mode
            if sys.platform == 'darwin':
                import AppKit
                AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyProhibited)
        else:
            # Show confirmation dialog before exiting
            reply = QMessageBox.question(
                self, 
                '确认退出', 
                '确定要退出程序吗？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
                sys.exit(0)
            else:
                event.ignore()
    
    def start_connection(self):
        self.user_id = self.input.text() or "test"
        self.updateButtonState(False)
        self.status.show()
        self.status.setText("链接服务中...")

        # Save the beta code to 'conf.txt' in the same directory as 'CalfTool'
        with open(BETA_CODE_FILE, 'w', encoding='utf-8') as f:
            f.write(self.user_id)
    
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
            
            self.permission_status.setText("截屏权限: 已授权")
            self.permission_status.setStyleSheet("color: green")
            self.permission_status.show()  # Show label
            self.button.setEnabled(True)
            self.permission_button.setEnabled(False)
            
        except Exception as e:
            self.permission_status.setText(f"截屏权限错误: {str(e)}")
            self.permission_status.setStyleSheet("color: red")
            self.permission_status.show()  # Show label
            self.button.setEnabled(False)
    
    def on_input_text_changed(self, text):
        if text.strip():
            self.permission_button.setEnabled(True)
        else:
            self.permission_button.setEnabled(False)

if __name__ == "__main__":
    args, uri = parse_arguments()
    log.info(f"应用程序启动，使用URI: {uri}")
    
    try:
        app = QApplication(sys.argv)
        # Set to regular mode initially to show dialog
        if sys.platform == 'darwin':
            import AppKit
            AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
        
        log.info("QApplication 已初始化")
        window = MainWindow()
        dialog = CustomInputDialog()
        window.dialog = dialog
        log.info("GUI 组件已初始化")
        
        dialog.show()
        log.info("第一步：输入对话框已显示")
        
        # Modify async task to handle state after dialog close
        async def main():
            while True:
                while not hasattr(dialog, 'user_id'):
                    await asyncio.sleep(0.1)
                    app.processEvents()
                
                result = await send_data(user_id=dialog.user_id, uri=uri, window=window)
                
                # Check result
                if result == "invalid_user_id":
                    dialog.showError("内测码无效，请重试。")
                    dialog.updateButtonState(True)
                    delattr(dialog, 'user_id')
                elif result == "connection_timeout":
                    dialog.showError("连接尝试已超过2小时，请重试。")
                    dialog.updateButtonState(True)
                    delattr(dialog, 'user_id')
        
        # Use asyncio to run task
        try:
            # Create new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Start async task
            future = asyncio.ensure_future(main())
            
            # Run Qt event loop and asyncio event loop concurrently
            while not future.done():
                app.processEvents()
                loop.run_until_complete(asyncio.sleep(0.1))
                
        except KeyboardInterrupt:
            print("\n正在关闭客户端...")
        except Exception as e:
            log.error(f"循环错误: {str(e)}")
            window.showMessage("Error", f"连接错误: {str(e)}")
            sys.exit(1)
    except Exception as e:
        log.critical(f"应用程序启动期间的致命错误: {str(e)}")
        log.exception("完整异常详情:")
        sys.exit(1)
