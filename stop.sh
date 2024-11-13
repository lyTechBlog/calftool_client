# 激活新创建的环境
echo "Activating the conda environment 'python310_env'..."
source activate python310_env

# 验证Python版本
echo "Verifying Python version..."
python --version

ps aux | grep client.py | grep -v 'grep' | awk -F ' ' '{print $1}' | xargs kill
ps aux | grep monitor.sh | grep -v 'grep' | awk -F ' ' '{print $1}' | xargs kill
echo "test_mm 已停止"