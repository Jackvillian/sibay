#!/usr/bin/env bash
Tag=$2
branch=$(git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/')
git checkout release
git fetch
git merge $branch
git tag -a v$Tag -m 'app release'
git push origin release
git checkout $branch