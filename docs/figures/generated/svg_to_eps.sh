#!/bin/bash

for file in *.svg ; do
    echo $file ;
    flatpak run org.inkscape.Inkscape "${file}" -o ${file%%.svg}.eps --export-ignore-filters --export-ps-level=3
done
