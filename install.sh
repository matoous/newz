#!/bin/bash

version=$(python -V 2>&1 | grep -Po '(?<=Python )(.+)')
if [[ -z "$version" ]]
then
    echo "No Python!"
fi

parsedVersion=$(echo "${version//./}")
if [[ "$parsedVersion" -lt "350" ]]
then
    echo "Invalid version, Newz requires at least Python 3.5.0"
else
    echo "Valid version"
    python3.5 -m venv /venv
    source venv/bin/activate
    pip install -r
    deactivate
fi