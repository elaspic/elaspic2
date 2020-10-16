#!/bin/bash

set -ev

rsync -av \
    --include="*/" --include="*.svg" --include="*.png" --include="*.pdf" --exclude="*" \
    --prune-empty-dirs \
    ./notebooks/ ./docs/images/
