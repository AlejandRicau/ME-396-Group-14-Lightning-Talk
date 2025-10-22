from enum import unique

import arcade.key

from helpers import *
from gameOverView import GameOverView

class GameView(arcade.View):
    """Main application class."""

    def __init__(self):
        super().__init__()
        self.window.background_color = arcade.color.BLACK
        self.crt_filter = CRTFilter(WINDOW_WIDTH*2, WINDOW_HEIGHT*2,
                                    resolution_down_scale=1.0,
                                    hard_scan=-8.0,
                                    hard_pix=-3.0,
                                    display_warp=Vec2(1.0 / 100.0, 1.0 / 100.0),
                                    mask_dark=0.5,
                                    mask_light=1.5)
        self.filter_on = CRT_FILTER_ON

        self.board = None  # init of main board
        self.board_preview = None  # init of the preview board
        self.board_stored = None
        self.start_frame = 0
        self.game_over = False
        self.paused = False
        self.board_sprite_list = None  # init of board blocks/boxes
        self.board_preview_sprite_list = None  # init of preview blocks/boxes
        self.board_stored_sprite_list = None # init of stored stone region

        self.stone = None  # current stone in hand
        self.next_stone = None  # next stone in line for preview
        self.stone_x = 0  # top left coordinate of stone (empty included)
        self.stone_y = 0
        self.stored_stone = None

        self.ghost_x = self.stone_x  # coordinate for landing prediction
        self.ghost_y = 0

        self.stones = tetris_shapes.copy()  # query of stone to pick from
        random.shuffle(self.stones)

        # load sounds
        self.bgm = arcade.load_sound('sounds/BGM.mp3')
        self.bgm_player = None

        self.move_sound = arcade.load_sound('sounds/56.mp3')
        self.move_sound_player = None

        self.drop_sound = arcade.load_sound('sounds/57.mp3')
        self.drop_sound_player = None

        self.stone_fallen_sound = arcade.load_sound('sounds/52.mp3')
        self.stone_fallen_sound_player = None

        self.line_clear_sound = arcade.load_sound('sounds/51.mp3')
        self.line_clear_sound_player = None

        self.rotate_sound = arcade.load_sound('sounds/80.mp3')
        self.rotate_sound_player = None

        self.store_sound = arcade.load_sound('sounds/78.mp3')
        self.store_sound_player = None

    def new_stone(self,store=False):
        """
        Randomly grab a new stone from the bag of stones,
        if the bag is empty refill the bag and shuffle it.
        Then set the stone's location to the top.
        If we immediately collide, then game-over.
        """
        if store: # logic for storage of a piece.
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
            self.bgm.stop(self.bgm_player)
            game_view = GameOverView()
            self.window.show_view(game_view)

    def setup(self):
        """Set up the game variables, board and sprite list"""
        self.board = new_board(ROW_COUNT, COLUMN_COUNT)
        self.board_preview = new_board(PREVIEW_ROW_COUNT, PREVIEW_COL_COUNT)
        self.board_stored = new_board(PREVIEW_ROW_COUNT, PREVIEW_COL_COUNT)
        self.start_frame = GLOBAL_CLOCK.ticks

        self.board_sprite_list = arcade.SpriteList()
        self.board_preview_sprite_list = arcade.SpriteList()
        self.board_stored_sprite_list = arcade.SpriteList()

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
                    WINDOW_HEIGHT - (MARGIN + HEIGHT) * (3 + row) + MARGIN + HEIGHT // 2
                )

                self.board_preview_sprite_list.append(sprite)

        # spritify the stored stone board
        for row in range(len(self.board_stored)):
            for column in range(len(self.board_stored[0])):
                sprite = arcade.Sprite(texture_list[0])
                sprite.textures = texture_list
                sprite.center_x = (
                        (MARGIN + WIDTH) * (COLUMN_COUNT + 1 + column) + MARGIN + WIDTH // 2
                )
                sprite.center_y = (
                        WINDOW_HEIGHT - (MARGIN + HEIGHT) * (6 + row +PREVIEW_ROW_COUNT) + MARGIN + HEIGHT // 2
                )
                self.board_stored_sprite_list.append(sprite)



        self.new_stone()
        self.update_board()
        self.bgm_player = self.bgm.play(loop=True)

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
                            self.line_clear_sound.play()
                            break
                    else:
                        self.stone_fallen_sound.play()
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

    def get_state(self):
        return {"board": None, "score": 0, "level": 1, "lines": 0, "next_queue": []}

    def update_store_board(self):
        self.board_stored = new_board(
            PREVIEW_ROW_COUNT, PREVIEW_COL_COUNT
        )  # refresh the board
        x_offset = 0
        piece_id = 0
        if self.stored_stone is not None:
            piece_id = set(self.stored_stone[0])
            piece_id.discard(0)
            piece_id = piece_id.pop()
        if self.stored_stone is not None and piece_id == 2:  # make the 2x2 stone to show in the middle
            x_offset = 1
        if self.stored_stone is not None:
            self.board_stored = (
                join_matrixes(  # join the stores stone with the small preview board
                    self.board_stored, tetris_shapes[piece_id-1], (x_offset, 0)
                )
            )

    def store_stone(self): # Method to store current stone.
        temp_stored_stone = self.stone
        self.new_stone(store=True) # create a new stone, call the store flag to activate related logic
        self.stored_stone = temp_stored_stone
        self.update_store_board()
        self.update_board()


    def on_key_press(self, key, modifiers):
        """
        Handle user key presses
        User goes left, move -1
        User goes right, move 1
        Rotate stone,
        or drop down
        """
        # actual keyboard response
        if not self.paused:
            if key == arcade.key.LEFT:
                self.move(-1)
                self.move_sound_player = self.move_sound.play()
            elif key == arcade.key.RIGHT:
                self.move(1)
                self.move_sound_player = self.move_sound.play()
            elif key == arcade.key.UP:
                self.rotate_stone()
                self.rotate_sound_player = self.rotate_sound.play()
            elif key == arcade.key.DOWN:
                self.drop()
                self.drop_sound_player = self.drop_sound.play()
            elif key == arcade.key.SPACE:
                self.store_stone()
                self.store_sound_player = self.store_sound.play()

        if key == arcade.key.P:
            if self.paused:
                self.paused = False
                self.bgm_player.play()
            else:
                self.paused = True
                self.bgm_player.pause()

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
        # update main board sprites
        for row_idx, row_data in enumerate(self.board):
            for col_idx, cell_value in enumerate(row_data):
                i = row_idx * COLUMN_COUNT + col_idx
                self.board_sprite_list[i].set_texture(cell_value)

        # update preview board sprites
        for row_idx, row_data in enumerate(self.board_preview):
            for col_idx, cell_value in enumerate(row_data):
                i = row_idx * PREVIEW_COL_COUNT + col_idx
                self.board_preview_sprite_list[i].set_texture(cell_value)


        for row_idx, row_data in enumerate(self.board_stored):
            for col_idx, cell_value in enumerate(row_data):
                i = row_idx * PREVIEW_COL_COUNT + col_idx
                self.board_stored_sprite_list[i].set_texture(cell_value)

    def on_draw(self):
        """Render the screen."""

        # This command has to happen before we start drawing
        if self.filter_on:
            self.crt_filter.use()
            self.crt_filter.clear()
            self.board_sprite_list.draw()
            self.board_preview_sprite_list.draw()
            self.board_stored_sprite_list.draw()
            self.draw_grid(self.stone, self.stone_x, self.stone_y)
            self.draw_ghost()  # This is for the landing prediction
            arcade.draw_rect_outline(
                arcade.rect.LBWH(MARGIN, MARGIN, ((WIDTH + MARGIN) * COLUMN_COUNT), (WINDOW_HEIGHT - 2 * MARGIN)),
                arcade.color.WHITE, BORDER_WIDTH)


            self.window.use()
            self.clear()
            self.crt_filter.draw()
        else:
            self.clear()
            self.board_sprite_list.draw()
            self.board_preview_sprite_list.draw()
            self.board_stored_sprite_list.draw()
            self.draw_grid(self.stone, self.stone_x, self.stone_y)
            self.draw_ghost()  # This is for the landing prediction

            arcade.draw_rect_outline(
                arcade.rect.LBWH(MARGIN, MARGIN, ((WIDTH + MARGIN) * COLUMN_COUNT), (WINDOW_HEIGHT - 2*MARGIN)),
                arcade.color.WHITE, BORDER_WIDTH)

    def ghost_piece_position(self):
        """Calculate the position of the ghost piece."""
        ghost_y = self.stone_y
        while not check_collision(self.board, self.stone, (self.stone_x, ghost_y)):
            ghost_y += 1
        return ghost_y