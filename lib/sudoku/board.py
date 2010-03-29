# -*- coding: utf-8 -*-

"""Module with Board class.

This exports:
  - Value -- board value representation.
  - Board -- a board with NxN positions.

Copyright (C) 2005-2008  Xosé Otero <xoseotero@users.sourceforge.net>

Modification history:
2005/10/12  Antti Kuntsi
	New file format to support generic grid form.

"""

__all__ = ["Board", "Value"]


class Value(object):
    """Board value representation.

    This class converts values greater than 9 to letters.
    For example, 10 = A, 11 = B, etc.

    """
    def __init__(self, value):
        """Form a value representation.

        value can be a integer or a letter.
        The letter representation is always a upper one.

        Arguments:
        value -- the value

        """
        if isinstance(value, int):
            self.__value = value
            self.__str = self.string()
        elif isinstance(value, str) and len(value) == 1:
            if value.isdigit():
                self.__value = int(value)
            else:
                self.__value = ord(value.upper()) - ord("A") + 10
            self.__str = self.string()
        elif isinstance(value, Value):
            self.__value = value.__value
            self.__str = value.__str
        else:
            raise ValueError("unknow value %s" % str(value))

    def __str__(self):
        """Return the string representation.

        This is different to string() because the value is cached.

        """
        return self.__str

    def __nonzero__(self):
        """Return if the value is different to 0."""
        if self.__value:
            return True
        else:
            return False

    def integer(self):
        """Return the integer value."""
        return self.__value

    def string(self):
        """Return the string representation."""
        if self.__value < 10:
            return str(self.__value)
        else:
            return chr(ord('A') + self.__value - 10)


class Board(object):
    """Board with NxN positions.

    Numbers are 0-N*N

    """
    def __init__(self, cellsize=3, board=None, filename=None):
        """Form a board.

        If filename is not None, the numbers are loaded from a filename file.
        If board is not None, the numbers are loaded from the board.
        If filename and board are None a void board is created, with the size
        specified by cellsize.

        Keyword arguments:
        cellsize -- integer of the cell side lenght, default 3 for a 9x9
                    board (cellsize must be > 1)
                 -- or a tuple/list of 2 integers for a H*W grid on W*H grids
        board -- source board
        filename -- the file name (default None)

        """
        if board:
            self.load_board(board)
        elif filename:
            self.filename = filename
            self.load(filename)
        else:
            self.filename = None
            if type(cellsize) == int:
                cellsize = int(cellsize)
                self.cellsize = (cellsize, cellsize)
                self.boardsize = cellsize ** 2
                self.clear()
            else:
                self.cellsize = (int(cellsize[0]), int(cellsize[1]))
                self.boardsize = self.cellsize[0] * self.cellsize[1]
                self.clear()

        if self.boardsize <= 1:
            raise ValueError("board too small")


    def __getitem__(self, (row, column)):
        """Return the number from a positions.

        Arguments:
        (row, column) -- a tuple/list/iterable with 2 values

        """
        return self.numbers[row][column]

    def __setitem__(self, (row, column), value):
        """Set the number to a position.

        Arguments:
        (row, column) -- a tuple/list/iterable with 2 values
        value -- the number

        """
        if value > self.boardsize:
            raise ValueError("value > boardsize")
        self.numbers[row][column] = value


    def clear(self):
        """Remove all values."""
        self.numbers = []
        for i in xrange(self.boardsize):
            self.numbers.append([])
            for j in xrange(self.boardsize):
                self.numbers[i].append(0)


    def load_board(self, board):
        """Load the numbers from a board.

        Arguments:
        board -- source board

        """
        self.filename = board.filename
        self.cellsize = board.cellsize
        self.boardsize = board.boardsize

        for j in xrange(board.boardsize):
            for i in xrange(board.boardsize):
                self.numbers[j][i] = board[j, i]


    def load(self, filename):
        """Load the numbers from a file.

        Arguments:
        filename -- the file name

        """
        self.filename = filename

        f = file(filename, "rU")
        array = []
        lineno = 0
        dimensions = None
        for line in f.xreadlines():
                lineno += 1
                items = [item for item in line.split() if item]
                if not items or items[0][0] == "#":
                    if len(items) >= 4 and items[1].lower() == "boardsize":
                        try:
                            dimensions = [int(item) for item in "".join(items[2:]).split("x")]
                        except:
                            raise ValueError
                    continue
                try:
                    row = [Value(item).integer() for item in items]
                    array += row
                except ValueError:
                    raise ValueError("'%s' line %d: Not a number sequence" % (filename, lineno))

        f.close()
        if not dimensions: # Old-style square grid of squares
            max_n = int(max(array) ** (1 / 2.0))
            if max_n ** 4 != len(array):
                raise ValueError("%s is not a square grid of squares and grid size not specified" % (filename))
            dimensions = (max_n, max_n)
        self.load_numbers(array, dimensions)


    def load_numbers(self, numbers, (width, height)):
        """Load the numbers from a iterable.

        Arguments:
        numbers -- an iterable with at least 16 numbers
        (width, height) -- width and height of the region

        """
        self.boardsize = width * height
        self.cellsize = (width, height)
        self.clear()

        if self.boardsize ** 2 != len(numbers) or self.boardsize < 2:
            raise ValueError("number-sequence does not match grid size")

        for j in xrange(self.boardsize):
            for i in xrange(self.boardsize):
                self.numbers[j][i] = numbers[j * (self.boardsize) + i]


    def save(self, filename):
        """Save the numbers to a file.

        Arguments:
        filename -- the file name

        """
        f = file(filename, "w")
        f.write("# boardsize %d x %d\n" % self.cellsize)
        for j in xrange(self.boardsize):
            for i in xrange(self.boardsize):
                f.write("%3c" % str(Value(self.numbers[j][i])))
                if i != (self.boardsize - 1):
                    if (i + 1) % self.cellsize[0] == 0:
                        f.write("  ")
            f.write("\n")
            if (j + 1) % self.cellsize[1] == 0 and j != (self.boardsize - 1):
                f.write("\n")
        f.close()
