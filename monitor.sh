#!/bin/bash
# 脚本名称：monitor.sh
# 检查 client.py 是否运行，如果没有，则重新启动

while true; do
    # 检查client.py是否在运行
    if ! pgrep -f client.py > /dev/null
    then
        echo "$(date): client.py is not running. Restarting..."
        bash -c "conda run -n python310_env --no-capture-output python3 client.py >> run.log 2>&1 &"
        echo "$(date): client.py restarted."
    fi
    # 每隔10秒检查一次
    sleep 10
done
