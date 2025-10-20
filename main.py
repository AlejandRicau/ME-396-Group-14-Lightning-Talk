"""
Tetris

Tetris clone, with some ideas from silvasur's code:
https://gist.github.com/silvasur/565419/d9de6a84e7da000797ac681976442073045c74a4

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.tetris
"""

import arcade
from arcade.clock import GLOBAL_CLOCK
import random
import PIL

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


class GameView(arcade.View):
    """Main application class."""

    def __init__(self):
        super().__init__()
        self.window.background_color = arcade.color.WHITE

        self.board = None  # init of main board
        self.board_preview = None  # init of the preview board
        self.start_frame = 0
        self.game_over = False
        self.paused = False
        self.board_sprite_list = None  # init of board blocks/boxes
        self.board_preview_sprite_list = None  # init of preview blocks/boxes

        self.stone = None  # current stone in hand
        self.next_stone = None  # next stone in line for preview
        self.stone_x = 0  # top left coordinate of stone (empty included)
        self.stone_y = 0
        self.stored_stone = None

        self.ghost_x = self.stone_x  # coordinate for landing prediction
        self.ghost_y = 0

        self.stones = tetris_shapes.copy()  # query of stone to pick from
        random.shuffle(self.stones)

    def new_stone(self,store=False):
        """
        Randomly grab a new stone from the bag of stones,
        if the bag is empty refill the bag and shuffle it.
        Then set the stone's location to the top.
        If we immediately collide, then game-over.
        """
        if store:
            if self.stored_stone is None:
                self.stone = self.stones.pop(0)
            else:
                self.stone = self.stored_stone
        else:
            self.stone = self.stones.pop(0)  # get the first 1 and remove it from the list
        if not self.stones:  # Implemented bag system, so that no two pieces are repeated after each other.
            self.stones = tetris_shapes.copy()
            random.shuffle(self.stones)
        self.next_stone = self.stones[0]  # set the next one to be the preview


        self.board_preview = new_board(
            PREVIEW_ROW_COUNT, PREVIEW_COL_COUNT
        )  # refresh the board
        x_offset = 0
        if len(self.next_stone[0]) == 2:  # make the 2x2 stone to show in the middle
            x_offset = 1
        self.board_preview = (
            join_matrixes(  # join the preview stone with the small preview board
                self.board_preview, self.next_stone, (x_offset, 0)
            )
        )
        self.update_board()

        # Place a new stone on the board
        self.stone_x = int(COLUMN_COUNT / 2 - len(self.stone[0]) / 2)
        self.stone_y = 0
        self.ghost_x = self.stone_x  # update the ghost coordinates
        self.ghost_y = self.ghost_piece_position()  # predict the landing positiion

        if check_collision(self.board, self.stone, (self.stone_x, self.stone_y)):
            self.game_over = True

    def setup(self):
        """Set up the game variables, board and sprite list"""
        self.board = new_board(ROW_COUNT, COLUMN_COUNT)
        self.board_preview = new_board(PREVIEW_ROW_COUNT, PREVIEW_COL_COUNT)
        self.start_frame = GLOBAL_CLOCK.ticks

        self.board_sprite_list = arcade.SpriteList()
        self.board_preview_sprite_list = arcade.SpriteList()

        # spritify the main board
        for row in range(len(self.board)):
            for column in range(len(self.board[0])):
                sprite = arcade.Sprite(texture_list[0])
                sprite.textures = texture_list
                sprite.center_x = (MARGIN + WIDTH) * column + MARGIN + WIDTH // 2
                sprite.center_y = (
                    WINDOW_HEIGHT - (MARGIN + HEIGHT) * (1 + row) + MARGIN + HEIGHT // 2
                )

                self.board_sprite_list.append(sprite)

        # spritify the preview board
        for row in range(len(self.board_preview)):
            for column in range(len(self.board_preview[0])):
                sprite = arcade.Sprite(texture_list[0])
                sprite.textures = texture_list
                sprite.center_x = (
                    (MARGIN + WIDTH) * (COLUMN_COUNT + 1 + column) + MARGIN + WIDTH // 2
                )
                sprite.center_y = (
                    WINDOW_HEIGHT - (MARGIN + HEIGHT) * (1 + row) + MARGIN + HEIGHT // 2
                )

                self.board_preview_sprite_list.append(sprite)

        self.new_stone()
        self.update_board()

    def drop(self):
        """
        Drop the stone down one place.
        Check for collision.
        If collided, then
          join matrixes
          Check for rows we can remove
          Update sprite list with stones
          Create a new stone
        """
        if not self.game_over and not self.paused:
            self.stone_y += 1
            if check_collision(self.board, self.stone, (self.stone_x, self.stone_y)):
                self.board = join_matrixes(
                    self.board, self.stone, (self.stone_x, self.stone_y)
                )

                while True:
                    for i, row in enumerate(self.board[:-1]):
                        if 0 not in row:  # remove row is it is filled
                            self.board = remove_row(self.board, i)
                            break
                    else:
                        break
                self.update_board()
                self.new_stone()

    def rotate_stone(self):
        """Rotate the stone, check collision."""
        if not self.game_over and not self.paused:
            new_stone = rotate_counterclockwise(self.stone)
            if self.stone_x + len(new_stone[0]) >= COLUMN_COUNT:
                self.stone_x = COLUMN_COUNT - len(new_stone[0])
            if not check_collision(self.board, new_stone, (self.stone_x, self.stone_y)):
                self.stone = new_stone

    def on_update(self, delta_time):
        """Update, drop stone if warranted"""
        # This is the mechanism where time progresses
        if GLOBAL_CLOCK.ticks_since(self.start_frame) % 10 == 0:
            self.drop()

    def move(self, delta_x):
        """Move the stone back and forth based on delta x."""
        if not self.game_over and not self.paused:
            new_x = self.stone_x + delta_x
            if new_x < 0:
                new_x = 0
            if new_x > COLUMN_COUNT - len(self.stone[0]):
                new_x = COLUMN_COUNT - len(self.stone[0])
            if not check_collision(self.board, self.stone, (new_x, self.stone_y)):
                self.stone_x = new_x

    def start_game(self):
        pass

    def pause_game(self):
        pass

    def resume_game(self):
        pass

    def get_state(self):
        return {"board": None, "score": 0, "level": 1, "lines": 0, "next_queue": []}

    def store_stone(self):
        temp_stored_stone = self.stone
        self.new_stone(store=True)
        self.stored_stone = temp_stored_stone

    def on_key_press(self, key, modifiers):
        """
        Handle user key presses
        User goes left, move -1
        User goes right, move 1
        Rotate stone,
        or drop down
        """
        # actual keyboard response
        if key == arcade.key.LEFT:
            self.move(-1)
        elif key == arcade.key.RIGHT:
            self.move(1)
        elif key == arcade.key.UP:
            self.rotate_stone()
        elif key == arcade.key.DOWN:
            self.drop()
        elif key == arcade.key.SPACE:
            self.store_stone()

        # update the position of ghost piece
        self.ghost_x, self.ghost_y = self.stone_x, self.ghost_piece_position()

    def draw_grid(self, grid, offset_x, offset_y, board_offset_x=0):
        """
        Draw the grid. Used to draw the falling stones. The board is drawn
        by the sprite list.
        """
        # Draw the grid
        for row_idx, row_data in enumerate(grid):
            for col_idx, cell_value in enumerate(row_data):
                # Figure out what color to draw the box
                if cell_value:
                    color = colors[cell_value]
                    # Do the math to figure out where the box is
                    x = (
                        board_offset_x
                        + (MARGIN + WIDTH)  # unit width of box
                        * (col_idx + offset_x)  # box coordinate
                        + MARGIN
                        + WIDTH // 2
                    )
                    y = (
                        WINDOW_HEIGHT
                        - (MARGIN + HEIGHT) * (row_idx + offset_y)
                        + MARGIN
                        + HEIGHT // 2
                    )

                    # Draw the box
                    arcade.draw_rect_filled(
                        arcade.rect.XYWH(x, y, WIDTH, HEIGHT), color
                    )

    def draw_ghost(self):
        """color the ghost piece where the current stone is predicted to be landing"""

        # Figure out what color to draw the box
        color = list(colors[max(self.stone[0])])
        color[3] /= 3
        color = tuple(color)

        for row_idx, row_data in enumerate(self.stone):
            for col_idx, cell_value in enumerate(row_data):
                # Do the math to figure out where the box is
                x = (self.ghost_x + col_idx) * (MARGIN + WIDTH) + MARGIN + WIDTH // 2
                y = (
                    WINDOW_HEIGHT
                    - (MARGIN + HEIGHT) * (self.ghost_y + row_idx)
                    + MARGIN
                    + HEIGHT // 2
                )

                # Draw the box
                if cell_value:
                    arcade.draw_rect_filled(
                        arcade.rect.XYWH(x, y, WIDTH, HEIGHT), color
                    )

    def update_board(self):
        """
        Update the sprite list to reflect the contents of the 2d grid
        """
        # update main board prites
        for row_idx, row_data in enumerate(self.board):
            for col_idx, cell_value in enumerate(row_data):
                i = row_idx * COLUMN_COUNT + col_idx
                self.board_sprite_list[i].set_texture(cell_value)

        # update preview board sprites
        for row_idx, row_data in enumerate(self.board_preview):
            for col_idx, cell_value in enumerate(row_data):
                i = row_idx * PREVIEW_COL_COUNT + col_idx
                self.board_preview_sprite_list[i].set_texture(cell_value)

    def on_draw(self):
        """Render the screen."""

        # This command has to happen before we start drawing
        self.clear()
        self.board_sprite_list.draw()
        self.board_preview_sprite_list.draw()
        self.draw_grid(self.stone, self.stone_x, self.stone_y)
        self.draw_ghost()  # This is for the landing prediction

    def ghost_piece_position(self):
        """Calculate the position of the ghost piece."""
        ghost_y = self.stone_y
        while not check_collision(self.board, self.stone, (self.stone_x, ghost_y)):
            ghost_y += 1
        return ghost_y


def main():
    """Create the game window, setup, run"""
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    game = GameView()
    game.setup()

    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()
