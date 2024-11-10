import base64
import os
from PIL import Image
def image_2_base64(image_path):
    with open(image_path, "rb") as image_file:
        # 读取二进制数据
        image_data = image_file.read()
        # 编码为 Base64
        base64_encoded_data = base64.b64encode(image_data)
        # 将字节数据转换为字符串
        base64_message = base64_encoded_data.decode('utf-8')
        return base64_message

def save_base64_image(base64_image, path):
    """
    将 base64 编码的图像保存到本地.

    :param base64_image: str, Base64 编码的图片数据
    :param path: str, 保存图片的完整路径
    :return: str, 保存结果消息
    """
    try:
        # 创建目录如果不存在
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # 解码 Base64 字符串
        image_data = base64.b64decode(base64_image)
        
        # 将图像数据写入文件
        with open(path, 'wb') as image_file:
            image_file.write(image_data)

        return False, f"Image saved successfully to {path}"
    except Exception as e:
        return True, f"Error saving image: {e}"
  
def crop_image(image_path, left, top, width, height):
    """
    裁剪图像并保存到本地。
    
    :param image_path: str, 原始图像路径
    :param left: int, 裁剪区域的左上角 x 坐标
    :param top: int, 裁剪区域的左上角 y 坐标
    :param width: int, 裁剪宽度
    :param height: int, 裁剪高度
    :return: str, 新图像保存路径
    """
    try:
        # 打开图像文件
        with Image.open(image_path) as img:
            # 定义裁剪区域 (left, upper, right, lower)
            crop_area = (left, top, left + width, top + height)
            # 进行裁剪
            cropped_img = img.crop(crop_area)
            # 构造新的文件名
            base, ext = os.path.splitext(image_path)
            new_image_path = f"{base}_{left}_{top}_{width}_{height}{ext}"
            # 保存裁剪后的图像
            cropped_img.save(new_image_path)
            return new_image_path
    except Exception as e:
        print(f"Error cropping image: {e}")
        return None