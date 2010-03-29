# -*- coding: utf-8 -*-

"""Python Sudoku package.

Create a sudoku of 3x3:
    from pythonsudoku import Board, Sudoku
    sudoku = Sudoku(Board(3))
    sudoku.create(0)
    sudoku.to_board().save("file_solved.sdk")
   
# Solve a sudoku:
    from pythonsudoku import Board, Sudoku
    sudoku = Sudoku(Board(filename="file.sdk"))
    sudoku.solve()
    sudoku.to_board().save("file_solved.sdk")

See pdf.py and image.py for PDF and image ouput.


Copyright (C) 2005-2008  XosÃ© Otero <xoseotero@users.sourceforge.net>

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

__all__ = ["Sudoku", "Board"]


from sudoku import Sudoku
from sudoku import Board
