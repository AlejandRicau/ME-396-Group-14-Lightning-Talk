import arcade
from arcade.clock import GLOBAL_CLOCK
from arcade.experimental.crt_filter import CRTFilter
from pyglet.math import Vec2
import random
import PIL
from constants import *

def create_textures():
    """Create a list of images for sprites based on the global colors."""
    new_textures = []
    for color in colors:
        image = PIL.Image.new("RGBA", (WIDTH, HEIGHT), color)
        new_textures.append(arcade.Texture(image))
    return new_textures


texture_list = create_textures()


def rotate_counterclockwise(shape):
    """Rotates a matrix clockwise"""
    return [
        [shape[y][x] for y in range(len(shape))]
        for x in range(len(shape[0]) - 1, -1, -1)
    ]


def check_collision(board, shape, offset):
    """
    See if the matrix stored in the shape will intersect anything
    on the board based on the offset. Offset is an (x, y) coordinate.
    """
    off_x, off_y = offset
    for cy, row in enumerate(shape):
        for cx, cell in enumerate(row):
            if cell and board[cy + off_y][cx + off_x]:
                return True
    return False


def remove_row(board, row):
    """Remove a row from the board, add a blank row on top."""
    del board[row]
    return [[0 for _ in range(COLUMN_COUNT)]] + board


def join_matrixes(matrix_1, matrix_2, matrix_2_offset):
    """Copy matrix 2 onto matrix 1 based on the passed in x, y offset coordinate"""
    # Nemo: This function is used to join board with the sprite stones
    offset_x, offset_y = matrix_2_offset
    for cy, row in enumerate(matrix_2):
        for cx, val in enumerate(row):
            matrix_1[cy + offset_y - 1][cx + offset_x] += val
    return matrix_1


def new_board(rows, cols):
    """Create a grid of 0's. Add 1's to the bottom for easier collision detection."""
    # Create the main board of 0's
    board = [[0 for _x in range(cols)] for _y in range(rows)]
    # Add a bottom border of 1's
    # Nemo: only add 1's if it is for the main board, I hide the 1's by reducing the window height
    if rows == ROW_COUNT:
        board += [[1 for _x in range(cols)]]
    return board