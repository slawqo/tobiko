#!/usr/bin/env python

import os
import sys

args = sys.argv[1:] or ['.']
results = [os.path.realpath(a) for a in args]
output = '\n'.join(results) + '\n'
sys.stdout.write(output)
