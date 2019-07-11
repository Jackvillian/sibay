#!/usr/bin/env bash
Tag=$1
branch=$(git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/(\1)/')
git branch release$Tag
git checkout release$Tag
git merge branch
#sh build.sh $Tag
echo "building done"
echo $branch
#cd ../ansible
#ansible-playbook deploy.yml --extra-vars "tag=$Tag"
