"""
Tetris

Tetris clone, with some ideas from silvasur's code:
https://gist.github.com/silvasur/565419/d9de6a84e7da000797ac681976442073045c74a4

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.tetris
"""

from helpers import *
from startMenuView import StartMenuView


def main():
    """Create the game window, setup, run"""
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    game_view = StartMenuView()
    window.show_view(game_view)
    arcade.run()


if __name__ == "__main__":
    main()
