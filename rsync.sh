#!/bin/bash

rsync -av -e 'ssh -p 3778' site/ vmre.ca:vmre/

