#!/usr/bin/env bash
CamInput=$1
CamOut=$2
emlink=$(curl -s $CamInput|grep src|awk '{print $4}'|sed 's/"/ /g'|awk '{print $2}')
empath=$(curl -s $emlink |grep n_url|awk '{print $4}'|sed 's/"//g'|sed 's/;/ /g')
ffmpeg -re -i $empath -tune zerolatency -crf 18 http://localhost:8090/$CamOut