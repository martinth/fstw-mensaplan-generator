# -*- coding: utf-8 -*-

"""Module to create/resolve sudokus.

This exports the class:
  - Sudoku -- create/resolve a sudoku

This exports the functions:
  - difficulty -- return the difficulty of a sudoku

Copyright (C) 2005-2008  Xosé Otero <xoseotero@users.sourceforge.net>

Modification history:
2005/10/12  Antti Kuntsi
	More generic grid form support, the board will be Y x X grid of X x Y
	regions.
2006/07/08  Paul Jimenez
	Make combination(n, r) into a generator.

"""

__all__ = ["Sudoku", "difficulty"]


import random

from board import Board


class Sudoku(object):
    """Create/resolve a sudoku."""
    def __init__(self, board, difficulty="normal"):
        """Create a sudoku with the board.

        Possible values to all positions will be calculated.

        Arguments:
        board -- the board

        Keyword arguments:
        difficulty -- the sudoku difficulty ("easy", "normal" or "hard")
                      ("normal" is the default)

        """
        self._clear_changes()
        self.from_board(board)
        self._difficulty = difficulty

        self._algorithms = {}
        self._algorithms["easy"] = ()
        self._algorithms["normal"] = (self._calculate_uniq_values,
                                      self._remove_deductable_values)
        self._algorithms["hard"] = (self._calculate_uniq_values,
                                    self._remove_deductable_values,
                                    self._unmatched_candidate_deletion)

    def __getitem__(self, (row, column)):
        """Get the value for the (row, column) position.

        Arguments:
        (row, column) -- a tuple/list/iterable with 2 values

        """
        if len(self._possible_values[row][column]) == 1:
            return self._possible_values[row][column][0]
        else:
            return 0

    def __setitem__(self, (row, column), value):
        """Set value as the (row, column) position value.

        Arguments:
        (row, column) -- a tuple/list/iterable with 2 values
        value -- the number

        """
        if value:
            self._possible_values[row][column] = [value]
            self._add_change()
            self._propagate_value_substraction(row, column, value)
        elif self[row, column]:
            self._initialize_possible_values(row, column)
            self._remove_change()


    # Values initialization
    def _initialize_possible_values(self, j, i):
        """Initialize the position (j, i) adding all the values as possible
        values.

        Arguments:
        j -- j coord
        i -- i coord

        """
        self._possible_values[j][i] = range(1, self._boardsize + 1)

    def _initialize_values(self):
        self._possible_values = []
        for j in xrange(self._boardsize):
            self._possible_values.append([])
            for i in xrange(self._boardsize):
                self._possible_values[j].append([])
                self._initialize_possible_values(j, i)


    # Helper functions
    def _region_horizontal_limits(self, j, i):
        """Return the horizontal limits of the region where (j, i) is..

        Arguments:
        j -- j coord
        i -- i coord

        """
        hini = (i / self._cellsize[0]) * self._cellsize[0]
        hmax = hini + self._cellsize[0]
        return (hini, hmax)

    def _region_vertical_limits(self, j, i):
        """Return the vertical limits of the region where (j, i) is..

        Arguments:
        j -- j coord
        i -- i coord

        """
        vini = (j / self._cellsize[1]) * self._cellsize[1]
        vmax = vini + self._cellsize[1]
        return (vini, vmax)


    # Changes numbers management
    def _clear_changes(self):
        """Set the changes to 0."""
        self._number_changes = 0

    def _add_change(self):
        """Add 1 to the changes."""
        self._number_changes += 1

    def _remove_change(self):
        """Reduce 1 to the changes."""
        self._number_changes -= 1

    def _changes(self):
        """Return the numbers of changes made."""
        return self._number_changes


    # Conversiton from/to Board
    def from_board(self, board):
        """Create a new sudoku from a board.

        Arguments:
        board -- the board

        """
        self._boardsize = board.boardsize
        self._cellsize = board.cellsize
        self._initialize_values()

        for j in xrange(self._boardsize):
            for i in xrange(self._boardsize):
                if board[j, i] != 0:
                    self[j, i] = board[j, i]

    def to_board(self):
        """Return a board with the numbers of the sudoku."""
        board = Board(self._cellsize)

        for j in xrange(self._boardsize):
            for i in xrange(self._boardsize):
                board[j,i] = self[j, i]

        return board


    # Value substraction
    def _value_substraction(self, j, i, value):
        """Remove value from the possible values of (j, i).

        Arguments:
        j -- j coord
        i -- i coord
        value -- value to remove

        """
        if value in self._possible_values[j][i]:
            self._possible_values[j][i].remove(value)

            if len(self._possible_values[j][i]) == 1:
                self[j, i] = self._possible_values[j][i][0]

    def _propagate_value_substraction(self, j, i, value):
        # Internal functions
        def propagate_value_substraction_horizontal(j, i, value):
            for h in xrange(self._boardsize):
                if h != i:
                    self._value_substraction(j, h, value)

        def propagate_value_substraction_vertical(j, i, value):
            for v in xrange(self._boardsize):
                if v != j:
                    self._value_substraction(v, i, value)

        def propagate_value_substraction_region(j, i, value):
            hini, hmax = self._region_horizontal_limits(j, i)
            vini, vmax = self._region_vertical_limits(j, i)

            for v in xrange(vini, vmax):
                for h in xrange(hini, hmax):
                    if h != i or v != j:
                        self._value_substraction(v, h, value)


        # Function code
        propagate_value_substraction_horizontal(j, i, value)
        propagate_value_substraction_vertical(j, i, value)
        propagate_value_substraction_region(j, i, value)


    # Calculate position values
    def possible_values(self, j, i):
        """Return the position values for the position.

        Arguments:
        j -- j coord
        i -- i coord

        """
        return self._possible_values[j][i]


    # Sudoku solution
    def finished(self):
        """Return if the sudoku if finished."""
        for j in xrange(self._boardsize):
            for i in xrange(self._boardsize):
                if len(self._possible_values[j][i]) != 1:
                    return False

        return True


    def solvable(self):
        """Return if the sudoku is solvable.

        This will check if the sudoku has not errors (duplicated numbers in
        a row, etc).
        
        """
        # Internal functions
        def solvable_horizontal(j):
            """Return if the sudoku is correct in the row.

            Arguments:
            j -- j coord

            """
            values = []
            for i in xrange(self._boardsize):
                if len(self._possible_values[j][i]) == 1:
                    value = self._possible_values[j][i][0]
                    if value in values:
                        return False
                    values.append(value)

            return True

        def solvable_vertical(i):
            """Return if the sudoku is correct in the col.

            Arguments:
            i -- i coord

            """
            values = []
            for j in xrange(self._boardsize):
                if len(self._possible_values[j][i]) == 1:
                    value = self._possible_values[j][i][0]
                    if value in values:
                        return False
                    values.append(value)

            return True

        def solvable_region(j, i):
            """Return if the sudoku is correct in the region.

            Arguments:
            j -- j coord
            i -- i coord

            """
            hini, hmax = self._region_horizontal_limits(j, i)
            vini, vmax = self._region_vertical_limits(j, i)

            values = []
            for v in xrange(vini, vmax):
                for h in xrange(hini, hmax):
                    if len(self._possible_values[v][h]) == 1:
                        value = self._possible_values[v][h][0]
                        if value in values:
                            return False
                        values.append(value)

            return True


        # Function code
        for j in xrange(self._boardsize):
            if not solvable_horizontal(j):
                return False
        for i in xrange(self._boardsize):
            if not solvable_vertical(i):
                return False
        for j in xrange(self._cellsize[1], self._boardsize, self._cellsize[1]):
            for i in xrange(self._cellsize[0], self._boardsize,
                            self._cellsize[0]):
                if not solvable_region(j, i):
                    return False

        return True


    def _calculate_uniq_values(self):
        """(A, B) has X as the unique value in the row/column/region, if X
        is a possible value in the position (A, B) and in the rest of
        row/column/region it doen't appear X as possible value.
        In this case, X is the value of (A, B).

        """
        # Internal functions
        def uniq_horizontal_appearance(j, i, value):
            """Return if value is only found in (j, i) in all the row j.

            Arguments:
            j -- j coord
            i -- i coord
            value - the value

            """
            if not value in self._possible_values[j][i]:
                return False

            for h in xrange(self._boardsize):
                if h != i:
                    if value in self._possible_values[j][h]:
                        return False

            return True

        def uniq_horizontal_value(j, i):
            """Try to find a value in (j, i) uniq to all the row j.

            Arguments:
            j -- j coord
            i -- i coord

            """
            for value in self._possible_values[j][i]:
                if uniq_horizontal_appearance(j, i, value):
                    self[j, i] = value
                    break

        def uniq_vertical_appearance(j, i, value):
            """Return if value is only found in (j, i) in all the col i.

            Arguments:
            j -- j coord
            i -- i coord
            value - the value

            """
            if not value in self._possible_values[j][i]:
                return False

            for v in xrange(self._boardsize):
                if v != j:
                    if value in self._possible_values[v][i]:
                        return False

            return True

        def uniq_vertical_value(j, i):
            """Try to find a value in (j, i) uniq to all the col i.

            Arguments:
            j -- j coord
            i -- i coord

            """
            for value in self._possible_values[j][i]:
                if uniq_vertical_appearance(j, i, value):
                    self[j, i] = value
                    break

        def uniq_region_appearance(j, i, value):
            """Return if value is only found in (j, i) in all the region.

            Arguments:
            j -- j coord
            i -- i coord
            value -- the value

            """
            if not value in self._possible_values[j][i]:
                return False

            hini, hmax = self._region_horizontal_limits(j, i)
            vini, vmax = self._region_vertical_limits(j, i)

            for v in xrange(vini, vmax):
                for h in xrange(hini, hmax):
                    if h != i or v != j:
                        if value in self._possible_values[v][h]:
                            return False

            return True

        def uniq_region_value(j, i):
            """Try to find a value in (j, i) uniq to all the region.

            Arguments:
            j -- j coord
            i -- i coord

            """
            for value in self._possible_values[j][i]:
                if uniq_region_appearance(j, i, value):
                    self[j, i] = value
                    break


        # Function code
        for j in xrange(self._boardsize):
            for i in xrange(self._boardsize):
                if len(self._possible_values[j][i]) == 1:
                    continue

                uniq_horizontal_value(j, i)
                uniq_vertical_value(j, i)
                uniq_region_value(j, i)


    def _remove_deductable_values(self):
        """In a region, if a value is only possible in a row/column, it can
        be deducted that in the rest of the row/column (ouside the region)
        this value can't be possible (so, remove from they possible values).

        """
        # Internal functions
        def remove_horizontal_deductible_values(j, i):
            """Remove the deductible values from the row.

            Arguments:
            j -- j coord
            i -- i coord

            """
            # Internal functions
            def check(j, i, value):
                """Return if the value is possible in rest of the rows in the
                region.

                Arguments:
                j -- j coord
                i -- i coord
                value -- value to check

                """
                hini, hmax = self._region_horizontal_limits(j, i)
                vini, vmax = self._region_vertical_limits(j, i)

                for v in xrange(vini, vmax):
                    if v != j:
                        for h in xrange(hini, hmax):
                            if value in self._possible_values[v][h]:
                                return False

                return True

            def remove(j, i, value):
                """Remove value from the rest of the rows in the region.

                Arguments:
                j -- j coord
                i -- i coord

                """
                hini, hmax = self._region_horizontal_limits(j, i)

                for h in xrange(hini):
                    self._value_substraction(j, h, value)

                for h in xrange(hmax + 1, self._boardsize):
                    self._value_substraction(j, h, value)


            # Function code
            if len(self._possible_values[j][i]) <= 1:
                return

            for value in self._possible_values[j][i]:
                if check(j, i, value):
                    remove(j, i, value)

        def remove_vertical_deductible_values(j, i):
            """Remove the deductible values from the col.

            Arguments:
            j -- j coord
            i -- i coord

            """
            # Internal functions
            def check(j, i, value):
                """Return if the value is possible in rest of the cols in the
                region.

                Arguments:
                j -- j coord
                i -- i coord
                value -- value to check

                """
                hini, hmax = self._region_horizontal_limits(j, i)
                vini, vmax = self._region_vertical_limits(j, i)

                for v in xrange(vini, vmax):
                    for h in xrange(hini, hmax):
                        if h != i:
                            if value in self._possible_values[v][h]:
                                return False

                return True

            def remove(j, i, value):
                """Remove value from the rest of the cols in the region.

                Arguments:
                j -- j coord
                i -- i coord

                """
                vini, vmax = self._region_vertical_limits(j, i)

                for v in xrange(vini):
                    self._value_substraction(v, i, value)

                for v in xrange(vmax + 1, self._boardsize):
                    self._value_substraction(v, i, value)


            # Function code
            if len(self._possible_values[j][i]) <= 1:
                return

            for value in self._possible_values[j][i]:
                if check(j, i, value):
                    remove(j, i, value)


        # Function code
        for j in xrange(self._boardsize):
            for i in xrange(self._boardsize):
                remove_horizontal_deductible_values(j, i)
                remove_vertical_deductible_values(j, i)


    def _unmatched_candidate_deletion(self):
        """A given set of n cells in any particular block, row, or column
        can only accommodate n different numbers."""
        # Internal functions
        def combination(n, r):
            if r == 1:
                for i in n:
                    yield [i]
            else:
                for i in xrange(len(n) - r + 1):
                    for vs in combination(n[i + 1:], r - 1):
                        vs.insert(0, n[i])
                        yield vs

        def possible(combination):
            """Return if some values can be found in the combination.

            This check if each position has more possible values than
            possitions has the combination.

            """
            lenght = len(combination)
            for c in combination:
                if len(self._possible_values[c[0]][c[1]]) > lenght:
                    return False
            return True

        def addition(combination):
            ret = []
            for c in combination:
                ret.extend(self._possible_values[c[0]][c[1]])
            return ret

        def uniq(s):
            ret = []
            for i in s:
                if not i in ret:
                    ret.append(i)
            return ret

        def horizontal(j):
            # Internal functions
            def unsolved_positions():
                unsolved = []
                for i in xrange(self._boardsize):
                    if len(self._possible_values[j][i]) > 1:
                        unsolved.append((j, i))
                return unsolved

            def remove(combination, values):
                for i in xrange(self._boardsize):
                    if (j, i) not in combination:
                        for value in values:
                            self._value_substraction(j, i, value)


            # Function code
            unsolved = unsolved_positions()
            for x in xrange(len(unsolved) - 1, 1, -1):
                for c in combination(unsolved, x):
                    if possible(c):
                        values = uniq(addition(c))
                        if len(values) == x:
                            remove(c, values)


        def vertical(i):
            # Internal functions
            def unsolved_positions():
                unsolved = []
                for j in xrange(self._boardsize):
                    if len(self._possible_values[j][i]) > 1:
                        unsolved.append((j, i))
                return unsolved

            def remove(combination, values):
                for j in xrange(self._boardsize):
                    if (j, i) not in combination:
                        for value in values:
                            self._value_substraction(j, i, value)


            # Function code
            unsolved = unsolved_positions()
            for x in xrange(len(unsolved) - 1, 1, -1):
                for c in combination(unsolved, x):
                    values = uniq(addition(c))
                    if len(values) == x:
                        remove(c, values)


        def region(j, i):
            hini, hmax = self._region_horizontal_limits(j, i)
            vini, vmax = self._region_vertical_limits(j, i)

            # Internal functions
            def unsolved_positions():
                unsolved = []
                for j in xrange(vini, vmax):
                    for i in xrange(hini, hmax):
                        if len(self._possible_values[j][i]) > 1:
                            unsolved.append((j, i))
                return unsolved

            def addition(combination):                
                ret = []
                for c in combination:
                    ret.extend(self._possible_values[c[0]][c[1]])
                return ret

            def remove(combination, values):
                for v in xrange(vini, vmax):
                    for h in xrange(hini, hmax):
                        if (v, h) not in combination:
                            for value in values:
                                self._value_substraction(v, h, value)


            # Function code
            unsolved = unsolved_positions()
            for x in xrange(len(unsolved) - 1, 1, -1):
                for c in combination(unsolved, x):
                    if possible(c):
                        values = uniq(addition(c))
                        if len(values) == x:
                            remove(c, values)


        # Function code
        for j in xrange(self._boardsize):
            horizontal(j)
        for i in xrange(self._boardsize):
            vertical(i)
        for j in xrange(0, self._boardsize, self._cellsize[1]):
            for i in xrange(0, self._boardsize, self._cellsize[0]):
                region(j, i)


    def __algorithms(self):
        for algol in self._algorithms[self._difficulty]:
            algol()

    def solve(self):
        """Solve the sudoku."""
        if not self.solvable():
            return False

        changes = -1
        while changes != self._changes():
            changes = self._changes()
            self.__algorithms()

        if self.finished():
            return True
        else:
            return False


    # Sudoku creation
    def are_holes(self):
        """Return if the sudoku can't be finished."""
        for j in xrange(self._boardsize):
            for i in xrange(self._boardsize):
                if len(self._possible_values[j][i]) == 0:
                    return True

        return False


    def give_numbers(self, solved, how_many):
        """Add extra numbers to the sudoku.

        Arguments:
        solved -- the board solved
        how_many -- the numbers of numbers to add.

        """
        while how_many > 0 and not self.finished():
            i = random.randint(0, self._boardsize - 1)
            j = random.randint(0, self._boardsize - 1)
            if len(self._possible_values[j][i]) == 1:
                continue

            self._possible_values[j][i] = [solved[j, i]]
            how_many -= 1

    def create(self, handicap=0):
        """Create a new sudoku with handicap.

        The handicap are the extra numbers given.

        Keyword arguments:
        handicap -- the handicap (default 0)

        """
        # Internal functions
        def create_sudoku_position(j, i):
            """Try to set a number in the position.

            Only if the possible values are equal to value this will work.

            Arguments:
            j -- j coord
            i -- i coord

            """
            if len(self._possible_values[j][i]) <= 1:
                return

            self[j, i] = random.choice(self._possible_values[j][i])

            if self.are_holes():
                self[j, i] = 0
            else:
                self.__algorithms()

        def create_numbers():
            """Create a finished sudoku.

            All positions will have a number.

            """
            self._clear_changes()
            self._initialize_values()

            while True:
                changes = -1
                while changes != self._changes():
                    changes = self._changes()

                    for j in xrange(self._boardsize):
                        for i in xrange(self._boardsize):
                            if not self[j, i]:
                                create_sudoku_position(j, i)

                if self.finished():
                    break

                self._clear_changes()
                self._initialize_values()

        def create_hole(j, i):
            """Create if it is possible in the position (j, i).

            Arguments:
            j -- j coord
            i -- i coord

            """
            if not self[j, i]:
                return

            board = self.to_board()
            board[j, i] = 0
            if Sudoku(board, self._difficulty).solve():
                self[j, i] = 0

        def create_holes():
            """Create holes randomly.

            After call this, only the neccesary numbers remain.

            """
            for i in xrange(0, self._boardsize ** 2):
                create_hole(random.randint(0, self._boardsize - 1),
                            random.randint(0, self._boardsize - 1))

            changes = -1
            while changes != self._changes():
                changes = self._changes()

                for j in xrange(self._boardsize):
                    for i in xrange(self._boardsize):
                        create_hole(j, i)


        # Function code
        create_numbers()

        if handicap:
            solved = self.to_board()
            create_holes()
            self.give_numbers(solved, handicap)
        else:
            create_holes()


def difficulty(board):
    """Return the difficulty of a sudoku.

    The difficulty returned can be "easy", "normal", "hard" or None for
    sudokus not solvable (bad sudokus or too difficult for Python Sudoku).

    Arguments:
    board -- the board

    """
    for difficulty in ("easy", "normal", "hard"):
        sudoku = Sudoku(board, difficulty)
        if sudoku.solve():
            return difficulty
    return None
