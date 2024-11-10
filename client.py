import asyncio
import websockets
import json
import time
from datetime import datetime
import os,sys
from tools.screen_shoot import screen_shot
from tools.image_tool import image_2_base64

PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
sys.path.append(f"{PROJECT_DIR}/src")
from tools.log_module import log
async def send_data(user_id="test_mm"):
    #uri = "ws://localhost:15010/calftoolws"
    uri = "ws://thefreeai.cn/calftoolws"
    log.info("start send data")
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                log.info(f"{user_id} start Connected to server")

                # 发送文本消息
                text_data = {
                    "user_id": user_id,
                    "type": "text",
                    "content": "Hello, WebSocket!"
                }
                await websocket.send(json.dumps(text_data))
                log.debug(f"{user_id} send text message {text_data}")
                
                # 监听服务端消息
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    if data["type"] == "sreen_shoot":
                        log.info("Received ping message from server")
                        # 返回当前系统时间
                        image_path = screen_shot(image_dir=user_id)
                        image_base64_data = image_2_base64(image_path)
                        current_time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                        screen_shot_message = {
                            "user_id": user_id,
                            "type": "image",
                            "content": image_base64_data,
                            "file_name": f"{current_time}.png",
                        }
                        log_screen_shot_message = {
                            "user_id": user_id,
                            "type": "image",
                            "content_size": len(image_base64_data),
                            "file_name": f"{current_time}.png",
                        }
                        await websocket.send(json.dumps(screen_shot_message))
                        log.info(f"{user_id} send image message {log_screen_shot_message}")
                    else:
                        log.info(f"{user_id} Received unknown message from server: {data}")
        
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
            print("Disconnected from server. Attempting to reconnect...")
            await asyncio.sleep(1)  # 等待5秒后重试连接

# 运行客户端
asyncio.get_event_loop().run_until_complete(send_data())
