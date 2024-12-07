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
            elif title == "Error":
                self.dialog.status.setText("状态: 连接失败")
                self.dialog.status.setStyleSheet("color: red")
                self.dialog.error_label.setText(message)
                self.dialog.updateButtonState(True)
                self.dialog.status.repaint()
            elif title == "Connecting":
                self.dialog.status.setText("状态: 连接中...")
                self.dialog.status.setStyleSheet("color: orange")
                self.dialog.error_label.setText("")
                self.dialog.updateButtonState(False)
                self.dialog.status.repaint()

class CustomInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入")
        layout = QVBoxLayout()
        
        # 添加提示标签
        label = QLabel("第一步：")
        layout.addWidget(label)
        
        # 添加输入框并设置占位符和样式
        self.input = QLineEdit("")
        self.input.setPlaceholderText("请输入内测码")
        self.input.setStyleSheet("QLineEdit::placeholder { color: gray; }")
        layout.addWidget(self.input)
        
        # 添加错误消息标签
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red")
        layout.addWidget(self.error_label)
        
        # 添加第二步提示标签
        step_two_label = QLabel("第二步：")
        layout.addWidget(step_two_label)
        
        # 添加"同意截屏权限"按钮
        self.permission_button = QPushButton("同意截屏权限")
        self.permission_button.clicked.connect(self.request_permission)
        layout.addWidget(self.permission_button)
        
        # 初始化权限状态标签并隐藏
        self.permission_status = QLabel("截屏权限: 未授权")
        self.permission_status.setStyleSheet("color: orange")
        self.permission_status.hide()  # 隐藏标签
        layout.addWidget(self.permission_status)
        
        # 添加第三步提示标签
        step_three_label = QLabel("第三步：")
        layout.addWidget(step_three_label)
        
        # 添加开始连接按钮
        self.button = QPushButton("连接")
        self.button.clicked.connect(self.start_connection)
        self.button.setEnabled(False)  # 在权限授予前禁用
        layout.addWidget(self.button)
        
        # 状态标签
        self.status = QLabel("未连接...")
        self.status.setStyleSheet("color: black")
        layout.addWidget(self.status)
        self.status.hide()  # 初始时隐藏状态标签
        
        # 添加第四步提示标签
        step_four_label = QLabel("第四步：")
        layout.addWidget(step_four_label)
        
        # 添加退出按钮，作用相当于点击 "×"
        self.exit_button = QPushButton("后台无痕运行")
        self.exit_button.clicked.connect(self.close)
        layout.addWidget(self.exit_button)
        
        self.setLayout(layout)
        
        # 添加关闭事件处理
        self.closeEvent = self.handleClose
    
    def handleClose(self, event):
        if hasattr(self, 'user_id') and self.status.text() == "状态: 连接成功":
            # 在最小化到后台前显示提示
            QMessageBox.information(
                self,
                '提示',
                '程序将在后台继续运行。\n',
                QMessageBox.StandardButton.Ok
            )
            event.accept()  # 允许关闭
            # 设置应用程序为后台模式
            if sys.platform == 'darwin':
                import AppKit
                AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyProhibited)
        else:
            # 在退出前显示确认对话框
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
        self.status.show()  # 连接开始时显示状态标签
        self.status.setText("链接服务中...")
    
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
            self.permission_status.show()  # ��示标签
            self.button.setEnabled(True)
            self.permission_button.setEnabled(False)
            
        except Exception as e:
            self.permission_status.setText(f"截屏权限错误: {str(e)}")
            self.permission_status.setStyleSheet("color: red")
            self.permission_status.show()  # 显示标签
            self.button.setEnabled(False)

if __name__ == "__main__":
    args, uri = parse_arguments()
    log.info(f"应用程序启动，使用URI: {uri}")
    
    try:
        app = QApplication(sys.argv)
        # 初始时设置为常规模式以显示对话框
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
        
        # 修改异步任务以处理对话框关闭后的状态
        async def main():
            while True:
                while not hasattr(dialog, 'user_id'):
                    await asyncio.sleep(0.1)
                    app.processEvents()
                
                result = await send_data(user_id=dialog.user_id, uri=uri, window=window)
                
                # 检查结果
                if result == "invalid_user_id":
                    dialog.showError("用户ID无效，请重试。")
                    dialog.updateButtonState(True)
                    delattr(dialog, 'user_id')
                elif result == "connection_timeout":
                    dialog.showError("连接尝试已超过2小时，请重试。")
                    dialog.updateButtonState(True)
                    delattr(dialog, 'user_id')
        
        # 使用 asyncio 运行任务
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
            print("\n正在关闭客户端...")
        except Exception as e:
            log.error(f"循环错误: {str(e)}")
            window.showMessage("Error", f"连接错误: {str(e)}")
            sys.exit(1)
    except Exception as e:
        log.critical(f"应用程序启动期间的致命错误: {str(e)}")
        log.exception("完整异常详情:")
        sys.exit(1)
