import arcade

from helpers import *
from ViewWithGamepadSupport import ViewWithGamepadSupport

class GameOverView(ViewWithGamepadSupport):
    def __init__(self,score=0,level =0):
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
        self.score = score
        self.level = level
        self.bgm = arcade.load_sound('sounds/game_over.mp3')

    def on_show_view(self):
        """ This is run once when we switch to this view """
        self.window.background_color = arcade.csscolor.BLACK

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        self.title_text = arcade.Text(
            "Game Over",
            x=self.window.width / 2,
            y=self.window.height / 2,
            color=arcade.color.WHITE,
            font_size=50,
            anchor_x="center",
        )
        self.instruction_text = arcade.Text(
            f"Better luck next time! \nYou reached Level {self.level + 1}\nYour score was {self.score}",
            x=self.window.width / 2,
            y=self.window.height / 2-75,
            color=arcade.color.WHITE,
            font_size=20,
            anchor_x="center",
            multiline=True,
            wrap_width=WINDOW_WIDTH,
        )
        self.bgm.play()

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

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        """ If the user presses the mouse button, close the game. """
        self.window.close()

    def on_button_press(self, ctrl, button_name):
        if button_name == "start":
            self.window.close()