#!/bin/zsh

while [ true ]
do
  echo '開始'
  date
  python crawl_tabelog.py
  echo '終了'
  python situation_detail.py
  date
  echo 'sleeping...'
  sleep 1d
done

