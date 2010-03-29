# -*- coding: utf-8 -*-

"""Module for image output.

This exports the class:
  - Image -- Save a board as an image.

Copyright (C) 2005-2008  Xosé Otero <xoseotero@users.sourceforge.net>

Modification history:
2005/10/12  Antti Kuntsi
	Use PIL version < 1.1.5

"""

__all__ = ["Image"]


import sys
import os
import re

import PIL.Image
import PIL.ImageColor
import PIL.ImageDraw
import PIL.ImageFont

from board import Value
from config import options


class Image(object):
    """Save a board as an image."""
    def __init__(self, board, filename):
        """Save a board as an image.

        Arguments:
        board -- the board
        filename -- the filename

        """
        self.numbers = board.numbers
        self.cellsize = board.cellsize
        self.boardsize = board.boardsize
        self.filename = filename
        if options.get("image", "format"):
            self.format = options.get("image", "format")
        else:
            self.format = re.sub(".*\.", "", filename)

        # 10% for borders
        self.square_width = options.getint("image", "width") / \
                            (self.boardsize + 1)
        self.square_height = options.getint("image", "height") / \
                             (self.boardsize + 1)

        self.create()

        self.draw_board()
        self.draw_numbers()

        self.save()

    def in_greyscale(self, colour):
        """Return if a colour is in grey scale."""
        rgb = PIL.ImageColor.getrgb(colour)
        return rgb[0] == rgb[1] == rgb[2]

    def create(self):
        """Create a blank image widthxheight."""
        if not options.get("image", "background"):
            mode = "RGBA"
        elif self.in_greyscale(options.get("image", "background")) and \
             self.in_greyscale(options.get("image", "lines_colour")) and \
             self.in_greyscale(options.get("image", "font_colour")):
            mode = "L"
        else:
            mode = "RGB"
        self.im = PIL.Image.new(mode, (options.getint("image", "width"),
                                       options.getint("image", "height")),
                                options.get("image", "background"))
        self.draw = PIL.ImageDraw.Draw(self.im)

    def save(self):
        """Save to file."""
        self.im.save(self.filename, self.format)

    def draw_board(self):
        """Draw the board.

        Only the board, to draw numbers draw_numbers it is used.

        """
        # margins
        x = options.getint("image", "width") / 20 # 5% left margin
        y = options.getint("image", "height") / 20 # 5% top margin

        self.draw.rectangle(((x, y), (options.getint("image", "width") - x,
                                      options.getint("image", "height") - y)),
                            outline=options.get("image", "lines_colour"),
                            fill=None)

        linewidth = 0

        # horizontal lines
        for i in xrange(self.boardsize):
            if i > 0 and i % self.cellsize[1] == 0:
                linewidth = 2
            else:
                linewidth = 1
            # PIL <= 1.1.4
            for offset in range(linewidth):
                self.draw.line(((x, y + i * self.square_height + offset),
                                (options.getint("image", "width") - x,
                                 y + i * self.square_height + offset)),
                               options.get("image", "lines_colour"))
            # PIL > 1.1.5
            #self.draw.line(((x, y + i * self.square_height),
            #                (options.getint("image", "width") - x,
            #                 y + i * self.square_height)),
            #               fill=options.get("image", "lines_colour"),
            #               width=linewidth)

        # vertical lines
        for i in xrange(self.boardsize):
            if i > 0 and i % self.cellsize[0] == 0:
                linewidth = 2
            else:
                linewidth = 1
            # PIL <= 1.1.4
            for offset in range(linewidth):
                self.draw.line(((x + i * self.square_width + offset, y),
                                (x + i * self.square_width + offset,
                                 options.getint("image", "height") - y)),
                               options.get("image", "lines_colour"))
            # PIL > 1.1.5
            #self.draw.line(((x + i * self.square_width, y),
            #                (x + i * self.square_width,
            #                 options.getint("image", "height") - y)),
            #               fill=options.get("image", "lines_colour"),
            #               width=linewidth)

    def draw_numbers(self):
        """Draw the numbers."""
        font = PIL.ImageFont.truetype(options.get("image", "font"),
                                      options.getint("image", "font_size"))

        # 5% margin + half square
        x = options.getint("image", "width") / 20 + self.square_width / 2
        y = options.getint("image", "height") / 20 + self.square_height / 2
        for i in xrange(self.boardsize):
            for j in xrange(self.boardsize):
                if self.numbers[j][i] != 0:
                    if options.getboolean("sudoku", "use_letters"):
                        text = str(Value(self.numbers[j][i]))
                    else:
                        text = str(Value(self.numbers[j][i]).integer())
                    size = self.draw.textsize(text, font=font)
                    # this should be:
                    #self.draw.text((x + i * self.square_width - size[0] / 2,
                    #                y + j * self.square_height - size[1] / 2),
                    #                text)
                    # but it's not centered without the + 2 in the y coord
                    self.draw.text((x + i * self.square_width - size[0] / 2,
                                    y + j * self.square_height - size[1] / 2 +
                                    2),
                                   text,
                                   fill=options.get("image", "font_colour"),
                                   font=font)
