#!/usr/bin/env python3
# vim:fileencoding=utf-8:ft=python
# file: img4latex.py
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Created: 2014-12-04 20:14:34 +0100
# Last modified: 2016-11-05 19:43:29 +0100
#
# To the extent possible under law, R.F. Smith has waived all copyright and
# related or neighboring rights to img4latex.py. This work is published
# from the Netherlands. See http://creativecommons.org/publicdomain/zero/1.0/

"""Program to check a PDF, PNG or JPEG file and return a suitable LaTeX
figure environment for it."""

import argparse
import configparser
import logging
import os
import subprocess
import sys
from wand.image import Image

__version__ = '1.4.0'


def main(argv):
    """Entry point for img4latex.

    Arguments:
        argv: All command line arguments.
    """
    after = """
The width and height arguments can also be set in a configuration file
called ~/.img4latexrc. It should look like this:

    [size]
    width = 125
    height = 280

Command-line arguments override settings in the configuration file.
If neither is given, the defaults apply.
"""
    raw = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=raw,
                                     epilog=after)
    parser.add_argument('-w', '--width', default=160, type=float,
                        help='width of the text block in mm. (default 160)')
    parser.add_argument('-t', '--height', default=270, type=float,
                        help='height of the text block in mm. (default 270)')
    parser.add_argument('--log', default='warning',
                        choices=['debug', 'info', 'warning', 'error'],
                        help="logging level (defaults to 'warning')")
    parser.add_argument('-v', '--version',
                        action='version',
                        version=__version__)
    parser.add_argument('file', nargs='*')
    cfg = from_config()
    args = parser.parse_args(argv, namespace=cfg)
    logging.basicConfig(level=getattr(logging, args.log.upper(), None),
                        format='%% %(levelname)s: %(message)s')
    logging.debug('command line arguments = {}'.format(argv))
    logging.debug('parsed arguments = {}'.format(args))
    args.width *= 72 / 25.4  # convert to points
    checkfor(['gs', '-v'])
    if not args.file:
        parser.print_help()
        sys.exit(0)
    for filename in args.file:
        if not os.path.exists(filename):
            logging.error('file "{}" does not exist.'.format(filename))
            continue
        if filename.endswith(('.ps', '.PS', '.eps', '.EPS', '.pdf', '.PDF')):
            bbox = getpdfbb(filename)
            bbwidth = float(bbox[2]) - float(bbox[0])
            bbheight = float(bbox[3]) - float(bbox[1])
            hscale = 1.0
            vscale = 1.0
            if bbwidth > args.width:
                scale = args.width / bbwidth
            if bbheight > args.height:
                scale = args.height / bbheight
            sinfo = 'hscale: {:.3f}, vscale: {:.3f}'
            logging.info(sinfo.format(hscale, vscale))
            scale = min([hscale, vscale])
            if scale < 0.999:
                fs = '[viewport={} {} {} {},clip,scale={s:.3f}]'
                opts = fs.format(*bbox, s=scale)
            else:
                fs = '[viewport={} {} {} {},clip]'
                opts = fs.format(*bbox)
        elif filename.endswith(('.png', '.PNG', '.jpg', '.JPG', '.jpeg',
                                '.JPEG')):
            width, height = getpicsize(filename)
            opts = None
            hscale = args.width / width
            vscale = args.height / height
            sinfo = 'hscale: {:.3f}, vscale: {:.3f}'
            logging.info(sinfo.format(hscale, vscale))
            scale = min([hscale, vscale])
            if scale < 0.999:
                opts = '[scale={:.3f}]'.format(scale)
        else:
            fskip = 'file "{}" has an unrecognized format. Skipping...'
            logging.error(fskip.format(filename))
            continue
        output_figure(filename, opts)
    print()


def from_config():
    """Read configuration data.

    Returns:
        An Argparse.Namespace object
    """

    values = argparse.Namespace()
    config = configparser.ConfigParser()
    if not config.read(os.environ['HOME'] + os.sep + '.img4latexrc'):
        # print("DEBUG: no config file found")
        return None
    for name in ['width', 'height']:
        if name in config['size']:
            values.name = float(config['size'][name])
            # print("DEBUG: {} = {} from cfg file".format(name, values.name))
    return values


def checkfor(args, rv=0):
    """
    Make sure that a program necessary for using this script is available.
    If the required utility is not found, this function will exit the program.

    Arguments:
        args: String or list of strings of commands. A single string may not
            contain spaces.
        rv: Expected return value from evoking the command.
    """
    if isinstance(args, str):
        if ' ' in args:
            raise ValueError('no spaces in single command allowed')
        args = [args]
    try:
        rc = subprocess.call(args, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        if rc != rv:
            raise OSError
        logging.info('found required program "{}"'.format(args[0]))
    except OSError as oops:
        outs = 'required program "{}" not found: {}.'
        logging.error(outs.format(args[0], oops.strerror))
        sys.exit(1)


def getpdfbb(fn):
    """Use ghostscript to get the BoundingBox of a PostScript or PDF
    file.

    Arguments:
        fn: Name of the file to get the BoundingBox from.

    Returns:
        A tuple of strings in the form (llx lly urx ury), where ll means
        lower left and ur means upper right.
    """
    gsopts = ['gs', '-q', '-dFirstPage=1', '-dLastPage=1', '-dNOPAUSE',
              '-dBATCH', '-sDEVICE=bbox', fn]
    gsres = subprocess.check_output(gsopts, stderr=subprocess.STDOUT)
    bbs = gsres.decode().splitlines()[0]
    return bbs.split(' ')[1:]


def getpicsize(fn):
    """Use ImageMagick to get the width and height of a bitmapped file.

    Arguments:
        fn: Name of the file to check.

    Returns:
        Width, hight of the image in points.
    """
    factor = {
        'pixelsperinch': 72,
        'pixelspercentimeter': 28.35,
        'undefined': 72
    }
    with Image(filename=fn) as img:
        if img.units is not 'undefined':
            hres, vres = img.resolution
            logging.info('resolution: {}x{} {}'.format(hres, vres, img.units))
        else:
            hres, vres = 300, 300
        return (img.width / hres * factor[img.units],
                img.height / vres * factor[img.units])
    return None


def output_figure(fn, options=None):
    """Print the LaTeX code for the figure.

    Arguments:
        fn: name of the file.
        options: options to add to the \includegraphics command.
    """
    fb = fn.rpartition('.')[0]
    fbnodir = fb[fn.rfind('/') + 1:]
    print()
    print(r'\begin{figure}[!htbp]')
    if options:
        print(r'  \centerline{\includegraphics' + options + '%')
        print(r'    {{{}}}}}'.format(fb))
    else:
        print(r'  \centerline{{\includegraphics{{{}}}}}'.format(fb))
    label = fbnodir.replace(' ', '-').replace('_', '-')
    print(r'  \caption{{\label{{fig:{}}}{}}}'.format(label, label))
    print(r'\end{figure}')


if __name__ == '__main__':
    main(sys.argv[1:])
