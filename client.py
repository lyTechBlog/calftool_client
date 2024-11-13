import asyncio
import websockets
import json
import os
import sys
import argparse
from datetime import datetime
from tools.screen_shoot import screen_shot
from tools.image_tool import image_2_base64

PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
sys.path.append(f"{PROJECT_DIR}/src")
from tools.log_module import log

def parse_arguments():
    parser = argparse.ArgumentParser(description="WebSocket client script")
    parser.add_argument('--debug', action='store_true', help="Run in debug mode")
    parser.add_argument('-d', '--domain', default="thefreeai.cn",
                       help="Server domain (default: thefreeai.cn)")
    args = parser.parse_args()
    
    # Construct URI based on domain and debug mode
    uri = f"ws://{args.domain}/calftoolws" if not args.debug else "ws://localhost:15010/calftoolws"
    log.info(f"Using URI: {uri}")
    
    return args, uri

async def send_data(user_id="test", uri=None):
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                log.info(f"{user_id} Connected to server")
                
                # Send a text message
                text_data = {
                    "user_id": user_id,
                    "type": "text",
                    "content": "Hello, WebSocket!"
                }
                await websocket.send(json.dumps(text_data))
                log.debug(f"{user_id} sent text message {text_data}")
                
                # Listen for messages from the server
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    if data["type"] == "screen_shoot":
                        log.info("Received screen_shoot request from server")
                        
                        # Take a screenshot and send it back
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
                        log.info(f"{user_id} sent image message {log_screen_shot_message}")
                    else:
                        log.info(f"{user_id} Received unknown message from server: {data}")
        
        except (websockets.exceptions.ConnectionClosed, 
                ConnectionRefusedError, 
                OSError) as e:  # 添加 OSError 异常捕获
            log.error(f"Connection error: {str(e)}. Attempting to reconnect in 2 seconds...")
            await asyncio.sleep(2)  # 增加重试间隔到5秒
            continue  # 显式继续循环
        
        except Exception as e:  # 捕获其他未预期的异常
            log.error(f"Unexpected error: {str(e)}. Attempting to reconnect in 2 seconds...")
            await asyncio.sleep(2)
            continue

if __name__ == "__main__":
    args, uri = parse_arguments()
    print(uri)
    while True:  # 添加外层循环确保程序永远运行
        try:
            asyncio.get_event_loop().run_until_complete(
                send_data(uri=uri)
            )
        except KeyboardInterrupt:  # 允许通过 Ctrl+C 优雅退出
            print("\nShutting down client...")
            break
        except Exception as e:
            log.error(f"Main loop error: {str(e)}. Restarting...")
            continue