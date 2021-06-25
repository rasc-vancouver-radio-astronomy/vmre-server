#!/bin/bash

cp -rv csv/* site/
rsync -av --delete site/ vmre@vmre.ca:html/

