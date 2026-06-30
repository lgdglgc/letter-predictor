#!/bin/bash
# =============================================================================
# Railway 每次开奖日执行脚本：更新数据 + 生成预测
# 在 Railway 中配置 Cron：30 22 * * 2,4,6
# =============================================================================
set -e

PROJECT_DIR="/app"
cd "$PROJECT_DIR"

echo "===== [$(date '+%Y-%m-%d %H:%M:%S')] 开始执行 ====="

# 确保目录存在
mkdir -p prediction_archive config logs

echo "--- 步骤 1: 更新开奖数据 ---"
python3 update_data.py
echo "数据更新完成"

echo "--- 步骤 2: 生成本期预测 ---"
python3 predict.py --mode team --num 5
echo "预测生成完成"

echo "===== [$(date '+%Y-%m-%d %H:%M:%S')] 执行完毕 ====="
