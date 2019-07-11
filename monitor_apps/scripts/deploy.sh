#!/usr/bin/env bash
mode=$1
Tag=$2
case $mode in
    docker)
          echo "building"
          cd monitor_apps/scripts/
          sh build.sh $Tag
          ;;
    release)
          echo "creating release"
          cd ../../
          branch=$(git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/')
          git checkout release
          git fetch
          git merge $branch
          git tag -a v$Tag -m 'app release'
          git push origin release
          ;;
    deploy)
          echo "deploying"
          cd ../../ansible
          cat /dev/null > vars/tags.yml
          echo "---" >> vars/tags.yml
          echo "tag: $Tag" >> vars/tags.yml
          ansible-playbook deploy.yml  -i inventory/hosts
          ;;
esac

echo $TAG >> Versions.txt
