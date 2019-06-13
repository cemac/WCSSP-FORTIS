#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import googlefuncts as gcf
dstring = ("")
hstring = ("")
parser = argparse.ArgumentParser(description=dstring)
parser.add_argument('--workshop', help=hstring)
parser.add_argument('--dest', help=r'path to destination folder')
args = parser.parse_args()
if args.dest:
    dest = args.dest
else:
    dest = '.'
if args.workshop:
    prefix = args.workshop + '/'
    local = dest + '/' + args.workshop + '/'
    blobs = gcf.get_blobs('wcssp-fortis', prefix)
    for blob in blobs:
        fname = blob.name
        gcf.download_blob('wcssp-fortis', fname, str(dest) + '/' + fname)
else:
    print('requires workshop name')
