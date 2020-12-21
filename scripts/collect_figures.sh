#!/bin/bash

set -ev

rsync -av \
    --include="*/" --include="*.svg" --include="*.png" --include="*.pdf" --exclude="*" \
    --prune-empty-dirs \
    ./notebooks/ ./docs/images/


SED_PATTERN='s/<svg preserveAspectRatio="none"/CRAZYSTRINGNOTINSVG/g; s/<svg/<svg preserveAspectRatio="none"/g; s/CRAZYSTRINGNOTINSVG/<svg preserveAspectRatio="none"/g'

# find ./docs/images/ -name '*.svg' | xargs -i{} sed -i -e "${SED_PATTERN}" {}
