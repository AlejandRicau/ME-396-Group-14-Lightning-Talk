# Set if CRT Mode is on
CRT_FILTER_ON = True


# Set how many rows and columns we will have
ROW_COUNT = 24
COLUMN_COUNT = 10

# Set the dimension for small window for next-stone preview
PREVIEW_ROW_COUNT = 2
PREVIEW_COL_COUNT = 5

# This sets the WIDTH and HEIGHT of each grid location
WIDTH = 30
HEIGHT = 30

# This sets the margin between each cell
# and on the edges of the screen.
MARGIN = 5

# Do the math to figure out our screen dimensions
WINDOW_WIDTH = (WIDTH + MARGIN) * (PREVIEW_COL_COUNT + COLUMN_COUNT) + MARGIN
WINDOW_HEIGHT = (HEIGHT + MARGIN) * (ROW_COUNT)
WINDOW_TITLE = "Tetris"

colors = [  # the last entry is the transparency of the color
    (0, 0, 0, 255),
    (255, 0, 0, 255),
    (0, 150, 0, 255),
    (0, 0, 255, 255),
    (255, 120, 0, 255),
    (255, 255, 0, 255),
    (180, 0, 255, 255),
    (0, 220, 220, 255),
]

# Define the shapes of the single parts
tetris_shapes = [  # this is the default orientation
    [[1, 1, 1], [0, 1, 0]],
    [[0, 2, 2], [2, 2, 0]],
    [[3, 3, 0], [0, 3, 3]],
    [[4, 0, 0], [4, 4, 4]],
    [[0, 0, 5], [5, 5, 5]],
    [[6, 6, 6, 6]],
    [[7, 7], [7, 7]],
]