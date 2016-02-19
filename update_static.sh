#!/bin/bash

git submodule update
cd website
git pull origin master
harp compile
cd ..
rm -rf static
cp -r website/www/demos/displacy static
