#!/bin/bash

(./run-1.sh) 2>&1 > run-1.log &   # 模拟任务1
(./run-2.sh) 2>&1 > run-2.log &   # 模拟任务2
(./run-3.sh) 2>&1 > run-3.log &   # 模拟任务3

wait
echo "所有sleep任务已完成！"
