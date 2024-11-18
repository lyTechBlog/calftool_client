import os
import shutil

def cleanup_qt_frameworks():
    # Clean up build and dist directories
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

    # Clean PyInstaller cache
    cache_dir = os.path.expanduser('~/Library/Application Support/pyinstaller')
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir) 