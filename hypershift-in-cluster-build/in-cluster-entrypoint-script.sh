#!/bin/bash
set -xeuo

env
pwd
id
whoami

tmpdir="$(mktemp -d)"
export HOME="$tmpdir"
cp /tmp/update-script/script.py "${tmpdir}/script.py"
chmod +x "${tmpdir}/script.py"
"${tmpdir}/script.py"
