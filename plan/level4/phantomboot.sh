#!/bin/bash

set -e

source bootenv.sh
git clone git://github.com/nimbusproject/Phantom.git
cd phantom
$PHANTOM_PYTHON setup.py install
