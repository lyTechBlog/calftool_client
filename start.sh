#!/bin/bash

# 脚本名称：install_python310_conda.sh

# 检查是否已经安装了conda
if ! command -v conda &> /dev/null
then
    echo "conda could not be found, please install Anaconda or Miniconda first."
    exit 1
fi

# 检查环境是否已经存在
if conda info --envs | grep -q "python310_env"
then
    echo "Conda environment 'python310_env' already exists."
else
    # 创建一个新的conda环境，并安装Python 3.10
    echo "Creating a new conda environment with Python 3.10..."
    conda create --name python310_env python=3.10 -y

    # 检查环境是否创建成功
    if [ $? -eq 0 ]; then
        echo "Conda environment 'python310_env' created successfully."
    else
        echo "Failed to create conda environment."
        exit 1
    fi
fi

# 验证Python版本
echo "Verifying Python version..."
bash -c "conda run -n python310_env python --version"

# 如果需要，可以在这里添加其他包的安装命令

# 脚本结束
# 使用 conda run 确保在 python310_env 环境中运行 client.py
bash -c "conda run -n python310_env python3 client.py >> run.log 2>&1 &"
echo "Script finished."
echo "test_mm 启动成功"