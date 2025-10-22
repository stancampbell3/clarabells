#!/usr/bin/bash
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' . stan.campbell@dendrite:/Users/stan.campbell/Tools/clara/