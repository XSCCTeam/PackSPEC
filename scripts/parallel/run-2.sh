#!/bin/bash

# 显示倒计时
for i in {3..1}; do
    echo -ne "$ATTENTION_LABEL Time remaining to stop: $i seconds.\r"
    sleep 1
done