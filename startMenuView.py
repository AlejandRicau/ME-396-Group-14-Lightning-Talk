import arcade

from helpers import *
from gameView import GameView
from ViewWithGamepadSupport import ViewWithGamepadSupport

class StartMenuView(ViewWithGamepadSupport):
    def __init__(self):
        super().__init__()
        # Create the crt filter
        self.crt_filter = CRTFilter(WINDOW_WIDTH*2, WINDOW_HEIGHT*2,
                                    resolution_down_scale=1.0,
                                    hard_scan=-8.0,
                                    hard_pix=-3.0,
                                    display_warp=Vec2(1.0 / 32.0, 1.0 / 24.0),
                                    mask_dark=0.5,
                                    mask_light=1.5)
        self.filter_on = CRT_FILTER_ON

        self.bgm = arcade.load_sound('sounds/start_menu.mp3')
        self.bgm_player = None

        self.start_sound = arcade.load_sound('sounds/start_game.mp3')

    def on_show_view(self):
        """ This is run once when we switch to this view """
        self.window.background_color = arcade.csscolor.DARK_SLATE_BLUE

        self.title_text = arcade.Text(
            "A Crude Tetris Copy",
            x=self.window.width / 2,
            y=self.window.height / 2,
            color=arcade.color.WHITE,
            font_size=30,
            anchor_x="center",
        )
        self.instruction_text = arcade.Text(
            "Click or press start to play",
            x=self.window.width / 2,
            y=self.window.height / 2 - 75,
            color=arcade.color.WHITE,
            font_size=20,
            anchor_x="center",
        )
        self.bgm_player = self.bgm.play()

    def on_draw(self):
        """ Draw this view """
        if self.filter_on:
            self.crt_filter.use()
            self.crt_filter.clear()
            self.title_text.draw()
            self.instruction_text.draw()

            self.window.use()
            self.clear()
            self.crt_filter.draw()

        else:
            self.clear()
            self.title_text.draw()
            self.instruction_text.draw()

    def start_game(self):
        self.bgm_player.pause()
        self.start_sound.play()
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        """ If the user presses the mouse button, start the game. """
        self.start_game()

    def on_button_press(self, ctrl, button_name):
        if button_name == "start":
            self.on_close()
            self.start_game()
        elif button_name == "back":
            self.window.close()
