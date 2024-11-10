import os
import time
import pyautogui

def screen_shot(image_dir, region_=None):
  if not os.path.exists(image_dir):
    os.makedirs(image_dir, exist_ok=True)

  if region_ is None:
    screen_image = pyautogui.screenshot()
  else: 
    screen_image = pyautogui.screenshot(region = region_)
  cur_time = int(time.time())
  raw_image_path = f"{image_dir}/{cur_time}.png"
  screen_image.save(raw_image_path)
  return raw_image_path
