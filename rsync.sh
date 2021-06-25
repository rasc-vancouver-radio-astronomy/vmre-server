#!/bin/bash

mkdir -p site
cp -rv power/* site/
cp -rv events/* site/
cp -rv plots/* site/
cp -rv static/* site/
cp -rv html/* site/
rsync -av --delete site/ vmre@vmre.ca:html/

