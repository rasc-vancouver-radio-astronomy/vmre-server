#!/bin/bash

rm -rf site
mkdir -p site
rsync -av plots/ site/
rsync -av static/ site/
rsync -av html/ site/
ssh vmre@vmre.ca mkdir -p html/
rsync -av --delete site/ vmre@vmre.ca:html/

