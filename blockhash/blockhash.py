#! /usr/bin/env python
#
# Perceptual image hash calculation tool based on algorithm descibed in
# Block Mean Value Based Image Perceptual Hashing by Bian Yang, Fan Gu and Xiamu Niu
#
# Copyright 2014 Commons Machinery http://commonsmachinery.se/
# Distributed under an MIT license, please see LICENSE in the top dir.

import math
from PIL import Image
from typing import Tuple, Union, Iterable


def median(data):
    data = sorted(data)
    length = len(data)
    if length % 2 == 0:
        return (data[length // 2 - 1] + data[length // 2]) / 2.0
        
    return data[length // 2]

def total_value_rgba(im, data, x, y):
    r, g, b, a = data[y * im.size[0] + x]
    if a == 0:
        return 765
    else:
        return r + g + b

def total_value_rgb(im, data, x, y):
    r, g, b = data[y * im.size[0] + x]
    return r + g + b

def translate_blocks_to_bits(blocks, pixels_per_block):
    half_block_value = pixels_per_block * 256 * 3 / 2

    # Compare medians across four horizontal bands
    bandsize = len(blocks) // 4
    for i in range(4):
        m = median(blocks[i * bandsize : (i + 1) * bandsize])
        for j in range(i * bandsize, (i + 1) * bandsize):
            v = blocks[j]

            # Output a 1 if the block is brighter than the median.
            # With images dominated by black or white, the median may
            # end up being 0 or the max value, and thus having a lot
            # of blocks of value equal to the median.  To avoid
            # generating hashes of all zeros or ones, in that case output
            # 0 if the median is in the lower value space, 1 otherwise
            blocks[j] = int(v > m or (abs(v - m) < 1 and m > half_block_value))


def bits_to_hexhash(bits):
    return '{0:0={width}x}'.format(int(''.join([str(x) for x in bits]), 2), width = len(bits) // 4)


def blockhash_even(im, bits):
    if im.mode == 'RGBA':
        total_value = total_value_rgba
    elif im.mode == 'RGB':
        total_value = total_value_rgb
    else:
        raise RuntimeError('Unsupported image mode: {}'.format(im.mode))

    data = im.getdata()
    width, height = im.size
    blocksize_x = width // bits
    blocksize_y = height // bits

    result = []

    for y in range(bits):
        for x in range(bits):
            value = 0

            for iy in range(blocksize_y):
                for ix in range(blocksize_x):
                    cx = x * blocksize_x + ix
                    cy = y * blocksize_y + iy
                    value += total_value(im, data, cx, cy)

            result.append(value)

    translate_blocks_to_bits(result, blocksize_x * blocksize_y)
    return bits_to_hexhash(result)

def blockhash(im, bits):
    if im.mode == 'RGBA':
        total_value = total_value_rgba
    elif im.mode == 'RGB':
        total_value = total_value_rgb
    else:
        raise RuntimeError('Unsupported image mode: {}'.format(im.mode))

    data = im.getdata()
    width, height = im.size

    even_x = width % bits == 0
    even_y = height % bits == 0

    if even_x and even_y:
        return blockhash_even(im, bits)

    blocks = [[0 for col in range(bits)] for row in range(bits)]

    block_width = float(width) / bits
    block_height = float(height) / bits

    for y in range(height):
        if even_y:
            # don't bother dividing y, if the size evenly divides by bits
            block_top = block_bottom = int(y // block_height)
            weight_top, weight_bottom = 1, 0
        else:
            y_frac, y_int = math.modf((y + 1) % block_height)

            weight_top = (1 - y_frac)
            weight_bottom = (y_frac)

            # y_int will be 0 on bottom/right borders and on block boundaries
            if y_int > 0 or (y + 1) == height:
                block_top = block_bottom = int(y // block_height)
            else:
                block_top = int(y // block_height)
                block_bottom = int(-(-y // block_height)) # int(math.ceil(float(y) / block_height))

        for x in range(width):
            value = total_value(im, data, x, y)

            if even_x:
                # don't bother dividing x, if the size evenly divides by bits
                block_left = block_right = int(x // block_width)
                weight_left, weight_right = 1, 0
            else:
                x_frac, x_int = math.modf((x + 1) % block_width)

                weight_left = (1 - x_frac)
                weight_right = (x_frac)

                # x_int will be 0 on bottom/right borders and on block boundaries
                if x_int > 0 or (x + 1) == width:
                    block_left = block_right = int(x // block_width)
                else:
                    block_left = int(x // block_width)
                    block_right = int(-(-x // block_width)) # int(math.ceil(float(x) / block_width))

            # add weighted pixel value to relevant blocks
            blocks[block_top][block_left] += value * weight_top * weight_left
            blocks[block_top][block_right] += value * weight_top * weight_right
            blocks[block_bottom][block_left] += value * weight_bottom * weight_left
            blocks[block_bottom][block_right] += value * weight_bottom * weight_right

    result = [blocks[row][col] for row in range(bits) for col in range(bits)]

    translate_blocks_to_bits(result, block_width * block_height)
    return bits_to_hexhash(result)


class ImageBlockhashCalculator(object):

    def __init__(self, quick: bool = False, bits: int = 16, size: Tuple[int, int] = None, interpolation: int = 1, debug: bool = True):
        """
        quick: Use quick hashing method. Default: False
        interpolation: Interpolation method: 1 - nearest neightbor, 2 - bilinear, 3 - bicubic, 4 - antialias. Default: 1'
        """
        self.blockhash_method = None
        self.set_blockhash_method(quick)

        self.bits = bits
        self.size = self.__verify_size_param(size)
        self.interpolation = self.__parse_interpolation(interpolation)
        self.debug = debug

    def __verify_size_param(self, size: Union[Tuple[int, int], None]):
        if size is None:
            return None

        if len(size) == 2:
            return (int(size[0]), int(size[1]))

    def __parse_interpolation(self, interpolation: int):
        if interpolation == 1:
            return Image.NEAREST
        elif interpolation == 2:
            return Image.BILINEAR
        elif interpolation == 3:
            return Image.BICUBIC
        elif interpolation == 4:
            return Image.ANTIALIAS
        else:
            raise ValueError("interpolation must be an int between 1 and 4.")

    def set_blockhash_method(self, quick: bool):
        self.blockhash_method = blockhash_even if quick else blockhash


    def compute_blockhash(self, images: Iterable[Image]):
        for im in images:
            # convert indexed/grayscale images to RGB
            if im.mode == '1' or im.mode == 'L' or im.mode == 'P':
                im = im.convert('RGB')
            elif im.mode == 'LA':
                im = im.convert('RGBA')

            if self.size is not None:
                im = im.resize(self.size, self.interpolation)

            image_blockhash = self.blockhash_method(im, self.bits)

            if self.debug:
                bin_hash = '{:0{width}b}'.format(int(image_blockhash, 16), width=self.bits ** 2)
                mapping = [bin_hash[i:i+self.bits] for i in range(0, len(bin_hash), self.bits)]
                print("")
                print("\n".join(mapping))
                print("")

            yield image_blockhash


def parse_image_paths(image_paths: Iterable[str]):
    return map(Image.open, image_paths)

   

