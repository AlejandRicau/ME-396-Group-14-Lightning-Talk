import arcade
from pyglet.math import Vec2

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
SCREEN_TITLE = "Arcade 3.3 DualSense Controller Visualizer (v4 Final)"
DEAD_ZONE = 0.1


class ControllerVisualizer(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.DARK_SLATE_BLUE)

        # Controller manager setup
        self.manager = arcade.ControllerManager()
        self.manager.push_handlers(self)

        self.active = None
        controllers = arcade.get_controllers()
        if controllers:
            self._use_controller(controllers[0])
            print(f"[INFO] Connected to controller: {controllers[0].name}")
        else:
            print("[INFO] No controllers found. Plug one in!")

        # Input state
        self.left_x = self.left_y = 0.0
        self.right_x = self.right_y = 0.0
        self.left_trigger = self.right_trigger = 0.0
        self.dpad_x = self.dpad_y = 0
        self.buttons_pressed = set()

    # ---------- Controller setup ----------
    def _use_controller(self, ctrl):
        self.active = ctrl
        ctrl.open()
        ctrl.push_handlers(self)
        print("[DEBUG] Controller attributes:")
        for attr in dir(ctrl):
            if not attr.startswith("_"):
                print("   ", attr)

    def on_connect(self, ctrl):
        print(f"[CONNECT] {ctrl}")
        if not self.active:
            self._use_controller(ctrl)

    def on_disconnect(self, ctrl):
        print(f"[DISCONNECT] {ctrl}")
        if ctrl == self.active:
            ctrl.remove_handlers(self)
            self.active = None

    # ---------- Input events ----------
    def on_button_press(self, ctrl, button_name):
        print(f"[EVENT] Button press: {button_name}")
        self.buttons_pressed.add(button_name)

        # Explicit D-pad fallback (avoid shoulder confusion)
        if button_name == "dpad_up":
            self.dpad_y = 1
        elif button_name == "dpad_down":
            self.dpad_y = -1
        elif button_name == "dpad_left":
            self.dpad_x = -1
        elif button_name == "dpad_right":
            self.dpad_x = 1

    def on_button_release(self, ctrl, button_name):
        print(f"[EVENT] Button release: {button_name}")
        self.buttons_pressed.discard(button_name)
        if button_name in {"dpad_up", "dpad_down"}:
            self.dpad_y = 0
        elif button_name in {"dpad_left", "dpad_right"}:
            self.dpad_x = 0

    # ---------- Sticks ----------
    def on_stick_motion(self, ctrl, stick_name, position: Vec2):
        x_value, y_value = position.x, position.y
        x_value = 0 if abs(x_value) < DEAD_ZONE else x_value
        y_value = 0 if abs(y_value) < DEAD_ZONE else y_value

        if stick_name.lower() == "leftstick":
            self.left_x, self.left_y = x_value, y_value
        elif stick_name.lower() == "rightstick":
            self.right_x, self.right_y = x_value, y_value

    # ---------- Triggers ----------
    def on_trigger_motion(self, ctrl, trigger_name, value):
        if "left" in trigger_name.lower():
            self.left_trigger = value
        elif "right" in trigger_name.lower():
            self.right_trigger = value

    # ---------- D-pad ----------
    def on_dpad_motion(self, ctrl, vector: Vec2):
        """Correct pyglet 2.x signature: (controller, Vec2)"""
        try:
            self.dpad_x, self.dpad_y = int(vector.x), int(vector.y)
            print(f"[EVENT] D-pad motion: ({self.dpad_x}, {self.dpad_y})")
        except Exception as e:
            print(f"[WARN] Bad D-pad vector: {e}")

    # ---------- Polling fallback ----------
    def on_update(self, delta_time):
        """Continuously poll analog values in case events drop."""
        if not self.active:
            return

        if hasattr(self.active, "left_analog"):
            pos = self.active.left_analog
            self.left_x, self.left_y = pos.x, pos.y
        if hasattr(self.active, "right_analog"):
            pos = self.active.right_analog
            self.right_x, self.right_y = pos.x, pos.y
        if hasattr(self.active, "lefttrigger"):
            self.left_trigger = self.active.lefttrigger
        if hasattr(self.active, "righttrigger"):
            self.right_trigger = self.active.righttrigger

    # ---------- Drawing ----------
    def on_draw(self):
        self.clear()
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        # Left stick
        radius = 60
        arcade.draw_circle_outline(cx - 200, cy, radius, arcade.color.LIGHT_GRAY, 2)
        arcade.draw_circle_filled(cx - 200 + self.left_x * radius,
                                  cy + self.left_y * radius, 10, arcade.color.AO)

        # Right stick
        arcade.draw_circle_outline(cx + 200, cy, radius, arcade.color.LIGHT_GRAY, 2)
        arcade.draw_circle_filled(cx + 200 + self.right_x * radius,
                                  cy + self.right_y * radius, 10, arcade.color.ORANGE)

        # Triggers
        bar_w, max_h = 30, 150
        lt_h, rt_h = self.left_trigger * max_h, self.right_trigger * max_h

        lt_outline = arcade.rect.LBWH(cx - 300 - bar_w / 2, cy - 100 - max_h / 2, bar_w, max_h)
        rt_outline = arcade.rect.LBWH(cx + 300 - bar_w / 2, cy - 100 - max_h / 2, bar_w, max_h)
        arcade.draw_rect_outline(lt_outline, arcade.color.GRAY, border_width=2)
        arcade.draw_rect_outline(rt_outline, arcade.color.GRAY, border_width=2)

        lt_fill = arcade.rect.LBWH((cx - 300) - (bar_w - 4) / 2,
                                   (cy - 100 - max_h / 2),
                                   bar_w - 4, lt_h)
        rt_fill = arcade.rect.LBWH((cx + 300) - (bar_w - 4) / 2,
                                   (cy - 100 - max_h / 2),
                                   bar_w - 4, rt_h)
        arcade.draw_rect_filled(lt_fill, arcade.color.LIGHT_BLUE)
        arcade.draw_rect_filled(rt_fill, arcade.color.LIGHT_PINK)

        # D-pad
        dpad_center_x, dpad_center_y = cx, cy - 180
        arrow_size, spacing = 20, 35
        color_on, color_off = arcade.color.AZURE, arcade.color.GRAY_BLUE

        # Up
        arcade.draw_triangle_filled(
            dpad_center_x, dpad_center_y + spacing + arrow_size,
            dpad_center_x - arrow_size, dpad_center_y + spacing,
            dpad_center_x + arrow_size, dpad_center_y + spacing,
            color_on if self.dpad_y > 0 else color_off)
        # Down
        arcade.draw_triangle_filled(
            dpad_center_x, dpad_center_y - spacing - arrow_size,
            dpad_center_x - arrow_size, dpad_center_y - spacing,
            dpad_center_x + arrow_size, dpad_center_y - spacing,
            color_on if self.dpad_y < 0 else color_off)
        # Left
        arcade.draw_triangle_filled(
            dpad_center_x - spacing - arrow_size, dpad_center_y,
            dpad_center_x - spacing, dpad_center_y + arrow_size,
            dpad_center_x - spacing, dpad_center_y - arrow_size,
            color_on if self.dpad_x < 0 else color_off)
        # Right
        arcade.draw_triangle_filled(
            dpad_center_x + spacing + arrow_size, dpad_center_y,
            dpad_center_x + spacing, dpad_center_y + arrow_size,
            dpad_center_x + spacing, dpad_center_y - arrow_size,
            color_on if self.dpad_x > 0 else color_off)

        # Text info
        lines = [
            "🎮 Arcade 3.3 DualSense Controller Visualizer (v4 Final)",
            f"Controller: {self.active.name if self.active else 'None'}",
            f"Left Stick: ({self.left_x:+.2f}, {self.left_y:+.2f})",
            f"Right Stick: ({self.right_x:+.2f}, {self.right_y:+.2f})",
            f"Triggers: LT={self.left_trigger:.2f}, RT={self.right_trigger:.2f}",
            f"D-Pad: ({self.dpad_x:+.0f}, {self.dpad_y:+.0f})",
            f"Buttons: {', '.join(sorted(self.buttons_pressed)) if self.buttons_pressed else 'None'}",
        ]
        y = SCREEN_HEIGHT - 40
        for line in lines:
            arcade.draw_text(line, 30, y, arcade.color.WHITE, 16)
            y -= 24

    def on_close(self):
        if self.active:
            self.active.remove_handlers(self)
            self.active.close()
        super().on_close()


def main():
    ControllerVisualizer()
    arcade.run()


if __name__ == "__main__":
    main()
