#!/bin/bash
# 脚本名称：setup_and_run.sh

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
    if [ $? -ne 0 ]; then
        echo "Failed to create conda environment."
        exit 1
    fi
    echo "Conda environment 'python310_env' created successfully."
fi

# 验证Python版本
echo "Verifying Python version..."
conda run -n python310_env --no-capture-output python3 --version

# 判断是否传入--debug参数
DEBUG_MODE=""
if [[ "$1" == "--debug" ]]; then
    DEBUG_MODE="--debug"
    echo "Running in debug mode."
else
    echo "Running in normal mode."
fi

# 启动client.py
echo "Starting client.py..."
bash -c "conda run -n python310_env --no-capture-output python3 client.py $DEBUG_MODE >> run.log 2>&1 &"

# 启动 monitor.sh
echo "Starting monitor.sh..."
nohup bash -x monitor.sh > monitor.log 2>&1 &
