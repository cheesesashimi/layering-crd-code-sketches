#!/bin/bash

echo "Zipping up your local dir"
# This requires pigz (https://zlib.net/pigz/) to use all available processor
# cores to help speed up gzip archive creation.
# There's probably some additional optimizations around only updating the archive.
tar -c --exclude-vcs --exclude=./bin -f - . | pigz -9 > archive.tar.gz
echo "Uploading archive and starting build..."
oc start-build --follow hypershift-operator --namespace hypershift --from-archive archive.tar.gz
echo "Deleting archive"
rm archive.tar.gz
