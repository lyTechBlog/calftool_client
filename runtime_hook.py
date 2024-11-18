import os
import sys
import logging
import shutil

def setup_runtime():
    # 设置正确的工作目录
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        if sys.platform == 'darwin':
            # macOS app bundle 情况下，向上两级找到 .app 包的根目录
            application_path = os.path.dirname(os.path.dirname(os.path.dirname(application_path)))
        os.chdir(application_path)
    
    # 确保日志目录存在
    log_dir = os.path.join(os.path.dirname(sys.executable), 'logs')
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception:
            pass
    
    # 设置基本的日志记录
    logging.basicConfig(
        filename=os.path.join(log_dir, 'app.log'),
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handle PyQt6 resources for macOS
    if sys.platform == 'darwin' and getattr(sys, 'frozen', False):
        qt_path = os.path.join(os.path.dirname(sys.executable), '_internal/PyQt6/Qt6')
        if os.path.exists(qt_path):
            def clean_framework_dir(framework_path):
                try:
                    # Clean up framework symlinks and directories
                    versions_dir = os.path.join(framework_path, 'Versions')
                    resources_dir = os.path.join(framework_path, 'Resources')
                    current_link = os.path.join(versions_dir, 'Current') if os.path.exists(versions_dir) else None
                    
                    # Remove Resources
                    if os.path.exists(resources_dir):
                        if os.path.islink(resources_dir):
                            os.unlink(resources_dir)
                        else:
                            shutil.rmtree(resources_dir)
                    
                    # Remove Current
                    if current_link and os.path.exists(current_link):
                        if os.path.islink(current_link):
                            os.unlink(current_link)
                        else:
                            shutil.rmtree(current_link)
                except (OSError, IOError) as e:
                    pass

            # Process all framework directories
            for root, dirs, files in os.walk(qt_path):
                for dir_name in dirs:
                    if dir_name.endswith('.framework'):
                        framework_path = os.path.join(root, dir_name)
                        clean_framework_dir(framework_path)

setup_runtime() 