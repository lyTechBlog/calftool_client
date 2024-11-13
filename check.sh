#!/bin/bash
# 脚本名称：check_monitor.sh

# 使用 pgrep 检查 monitor.sh 是否在运行
if pgrep -f monitor.sh > /dev/null
then
    echo "运行中"
else
    echo "未运行"
fi