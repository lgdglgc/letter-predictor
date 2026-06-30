#!/bin/bash
# =============================================================================
# Railway 每日凌晨执行脚本：回测分析 + 导出补丁
# 在 Railway 中配置 Cron：0 3 * * *
# =============================================================================
set -e

PROJECT_DIR="/app"
cd "$PROJECT_DIR"

echo "===== [$(date '+%Y-%m-%d %H:%M:%S')] 开始存档分析 ====="

mkdir -p prediction_archive config logs

python3 analyze_archive.py \
  --archive-dir prediction_archive \
  --export-prefix prediction_archive/analysis_report \
  --latest-patch-path config/weight_patch.latest.json \
  --latest-matrix-patch-path config/matrix_patch.latest.json \
  --latest-param-patch-path config/param_patch.latest.json

echo "===== [$(date '+%Y-%m-%d %H:%M:%S')] 分析完毕 ====="
