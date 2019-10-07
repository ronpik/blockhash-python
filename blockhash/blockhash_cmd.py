#! /usr/bin/env python
#
# Perceptual image hash calculation tool based on algorithm descibed in
# Block Mean Value Based Image Perceptual Hashing by Bian Yang, Fan Gu and Xiamu Niu
#
# Copyright 2014 Commons Machinery http://commonsmachinery.se/
# Distributed under an MIT license, please see LICENSE in the top dir.

import argparse
from typing import Iterable

from PIL import Image

from .blockhash import ImageBlockhashCalculator


def parse_image_paths(image_paths: Iterable[str]):
    return map(Image.open, image_paths)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--quick', type=bool, default=False,
        help='Use quick hashing method. Default: False')
    parser.add_argument('--bits', type=int, default=16,
        help='Create hash of size N^2 bits. Default: 16')
    parser.add_argument('--size',
        help='Resize image to specified size before hashing, e.g. 256x256')
    parser.add_argument('--interpolation', type=int, default=1, choices=[1, 2, 3, 4],
        help='Interpolation method: 1 - nearest neightbor, 2 - bilinear, 3 - bicubic, 4 - antialias. Default: 1')
    parser.add_argument('--debug', action='store_true',
        help='Print hashes as 2D maps (for debugging)')
    parser.add_argument('filenames', nargs='+')

    args = parser.parse_args()


    blockhasher = ImageBlockhashCalculator(args.quick, args.bits, args.size, args.interpolation, args.debug)
    images = parse_image_paths(args.filenames)
    hashes = blockhasher.compute_blockhash(images)
    for blockhash, filename in zip(hashes, args.filenames):
        print(f"{blockhash}  {filename}")