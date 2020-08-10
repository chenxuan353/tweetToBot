#!/bin/bash

# 定义进程
process = 'go-cqhttp'
readonly process

# 文件路径
nohup /root/cq/go-cqhttp &

# 轮询监控
while true
do
if [$? -ne 0]
then
    echo 'Operating'
else
    echo 'Stopped'
    nohup /root/cq/go-cqhttp &
fi
sleep 300
done

