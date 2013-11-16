#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# $Date$
#
# To the extent possible under law, Roland Smith has waived all copyright and
# related or neighboring rights to dicom2png.py. This work is published from
# the Netherlands. See http://creativecommons.org/publicdomain/zero/1.0/

"""Convert DICOM files to PNG format, remove blank areas. The blank erea
   removal is based on the image size of a Philips flat detector. The image
   goes from 2048x2048 pixels to 1574x2048 pixels."""

from __future__ import division, print_function

__version__ = '$Revision$'[11:-2]

import os
import sys
import subprocess
from multiprocessing import cpu_count
from time import sleep
from checkfor import checkfor


def startconvert(fname):
    """Use the convert(1) program from the ImageMagick suite to convert the
       image and crop it."""
    size = '1574x2048'
    args = ['convert', fname, '-units', 'PixelsPerInch', '-density', '300',
            '-crop', size+'+232+0', '-page', size+'+0+0', fname+'.png']
    with open(os.devnull, 'w') as bb:
        p = subprocess.Popen(args, stdout=bb, stderr=bb)
    print('Start processing', fname)
    return (fname, p)


def manageprocs(proclist):
    """Check a list of subprocesses for processes that have ended and
    remove them from the list.
    """
    for it in proclist:
        fn, pr = it
        result = pr.poll()
        if result is not None:
            proclist.remove(it)
            if result == 0:
                print('Finished processing', fn)
            else:
                s = 'The conversion of {} exited with error code {}.'
                print(s.format(fn, result))
    sleep(0.5)


def main(argv):
    """Main program.

    Keyword arguments:
    argv -- command line arguments
    """
    if len(argv) == 1:
        binary = os.path.basename(argv[0])
        print("{} ver. {}".format(binary, __version__), file=sys.stderr)
        print("Usage: {} [file ...]".format(binary), file=sys.stderr)
        sys.exit(0)
    del argv[0]
    checkfor('convert')
    procs = []
    maxprocs = cpu_count()
    for ifile in argv:
        while len(procs) == maxprocs:
            manageprocs(procs)
        procs.append(startconvert(ifile))
    while len(procs) > 0:
        manageprocs(procs)


## This is the main program ##
if __name__ == '__main__':
    main(sys.argv)