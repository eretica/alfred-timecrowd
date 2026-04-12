#!/bin/bash
# .alfredworkflow ファイルを生成する
cd "$(dirname "$0")"
zip -r TimeCrowd.alfredworkflow \
  info.plist main.py action.py timecrowd.py config.py state.py \
  -x "*.DS_Store" -x "__pycache__/*"
echo "Created: TimeCrowd.alfredworkflow"
