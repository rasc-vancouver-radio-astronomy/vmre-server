#!/bin/bash

rm -rf site
mkdir -p site
cp -rv power/* site/
cp -rv events/* site/
cp -rv plots/* site/
cp -rv static/* site/
cp -rv html/* site/
ssh vmre@vmre.ca mkdir -p html/dev
rsync -av --delete site/ vmre@vmre.ca:html/dev/

