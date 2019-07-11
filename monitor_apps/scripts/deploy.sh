#!/usr/bin/env bash
Tag=$1
echo "creating release"
cd ../../
branch=$(git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/')
git checkout release
git fetch
git merge $branch
git tag -a v$Tag -m 'app release'
git push origin release
echo "building"
cd monitor_apps/scripts/
sh build.sh $Tag
cd ../../ansible
ansible-playbook deploy.yml --extra-vars "tag=$Tag -i inventory/hosts"
echo "deploy done"
echo $TAG >> Versions.txt
