from PIL import Image
import os
import shutil

def convert_ico_to_icns(ico_path, output_name):
    # 确保输入文件存在
    if not os.path.exists(ico_path):
        print(f"错误: 找不到文件 {ico_path}")
        return False

    # 创建临时工作目录
    iconset_name = f"{output_name}.iconset"
    if os.path.exists(iconset_name):
        shutil.rmtree(iconset_name)
    os.makedirs(iconset_name)

    # 首先将 ICO 转换为 PNG
    temp_png = "temp_icon.png"
    try:
        img = Image.open(ico_path)
        # 获取 ICO 文件中最大的图像
        if hasattr(img, 'n_frames'):
            max_size = max((i.size for i in [img.seek(n) or img for n in range(img.n_frames)]))
            for n in range(img.n_frames):
                img.seek(n)
                if img.size == max_size:
                    break
        img.save(temp_png, 'PNG')

        # 定义需要的尺寸
        sizes = [16, 32, 128, 256, 512]
        
        # 生成不同尺寸的图片
        for size in sizes:
            img = Image.open(temp_png)
            # 普通分辨率
            icon_path = os.path.join(iconset_name, f'icon_{size}x{size}.png')
            img_resized = img.resize((size, size), Image.Resampling.LANCZOS)
            img_resized.save(icon_path)
            
            # 高分辨率 (@2x)
            icon_path_2x = os.path.join(iconset_name, f'icon_{size}x{size}@2x.png')
            img_resized = img.resize((size*2, size*2), Image.Resampling.LANCZOS)
            img_resized.save(icon_path_2x)

        # 使用 iconutil 生成 icns（仅在 macOS 上可用）
        os.system(f'iconutil -c icns {iconset_name}')
        
        # 清理临时文件
        os.remove(temp_png)
        shutil.rmtree(iconset_name)
        
        print(f"成功: 已生成 {output_name}.icns")
        return True

    except Exception as e:
        print(f"错误: 转换过程中出现问题 - {str(e)}")
        # 清理临时文件
        if os.path.exists(temp_png):
            os.remove(temp_png)
        if os.path.exists(iconset_name):
            shutil.rmtree(iconset_name)
        return False

if __name__ == "__main__":
    # 转换 calf_tool.ico 到 calf_tool.icns
    convert_ico_to_icns("calf_tool.ico", "calf_tool") 