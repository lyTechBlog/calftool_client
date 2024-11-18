import os
import sys
import PyInstaller.__main__
from cleanup import cleanup_qt_frameworks

def build():
    # Clean up before building
    cleanup_qt_frameworks()
    
    # Get the absolute path to the resources directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define build arguments without resources
    args = [
        'client.py',
        '--name=CalfTool',
        '--windowed',
        '--noconsole',
        '--runtime-hook=runtime_hook.py',
        '--clean',
        '--noconfirm',
        # Replace PyQt5 exclusions with PyQt6 inclusions
        '--hidden-import=PyQt6',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtWidgets',
        '--icon=calf_tool.icns'
    ]
    
    # Add resources only if the directory exists
    resources_path = os.path.join(current_dir, 'resources')
    if os.path.exists(resources_path) and os.path.isdir(resources_path):
        # Add resources directory
        args.append(f'--add-data={resources_path}:resources')
        
        # Add icon if it exists
        icon_path = os.path.join(resources_path, 'calf_tool.icns')
        if os.path.exists(icon_path):
            args.append(f'--icon={icon_path}')
    else:
        print(f"Warning: Resources directory not found at {resources_path}")
        print("Building without resources...")
    
    # Print build configuration
    print("Build configuration:")
    for arg in args:
        print(f"  {arg}")
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)

if __name__ == '__main__':
    build() 