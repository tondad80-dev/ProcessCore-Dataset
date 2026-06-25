#!/bin/bash
git add .
TIMESTAMP=$(date +"%Y-%m-%d %H:%M")
git commit -m "Auto-update dataset: $TIMESTAMP"
git push origin main
