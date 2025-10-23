import arcade
from pyglet.event import EventDispatcher
from pyglet.math import Vec2
import math

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 500
SCREEN_TITLE = "Dual-Stick + Trigger Event System (Arcade 3.3-compatible)"
DEAD_ZONE = 0.15
TRIGGER_ZONE = 0.5
TRIGGER_THRESHOLD = 0.6


class ControllerVisualizer(arcade.Window, EventDispatcher):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.DARK_SLATE_BLUE)

        # Controller manager
        self.manager = arcade.ControllerManager()
        self.manager.push_handlers(self)

        controllers = arcade.get_controllers()
        self.active = None
        if controllers:
            self._use_controller(controllers[0])
            print(f"[INFO] Connected to controller: {controllers[0].name}")
        else:
            print("[INFO] No controllers detected.")

        # Analog states
        self.left_x = self.left_y = 0.0
        self.right_x = self.right_y = 0.0
        self._left_state = None
        self._right_state = None

        # Triggers
        self.left_trigger = self.right_trigger = 0.0
        self._left_trigger_pressed = False
        self._right_trigger_pressed = False

        # Register stick events (8-way + centered)
        directions = [
            "left", "right", "up", "down",
            "up_left", "up_right", "down_left", "down_right", "centered",
        ]
        for side in ("leftstick", "rightstick"):
            for d in directions:
                self.register_event_type(f"on_{side}_{d}")

        # Register trigger events
        for trig in ("lefttrigger", "righttrigger"):
            for state in ("pressed", "released"):
                self.register_event_type(f"on_{trig}_{state}")

        # Cached text objects (for performance)
        cx = SCREEN_WIDTH // 2
        self._cached_text = {
            "L2": arcade.Text("L2", cx - 490, 50, arcade.color.WHITE, 14),
            "R2": arcade.Text("R2", cx + 320, 50, arcade.color.WHITE, 14),
            "hint": arcade.Text(
                "Move sticks (8-way) or pull triggers (thresholded one-shot)",
                cx - 330, 25, arcade.color.WHITE, 14,
            ),
        }

    # ---------- Controller setup ----------
    def _use_controller(self, ctrl):
        self.active = ctrl
        ctrl.open()
        ctrl.push_handlers(self)

    def on_connect(self, ctrl):
        if not self.active:
            self._use_controller(ctrl)

    def on_disconnect(self, ctrl):
        if ctrl == self.active:
            ctrl.remove_handlers(self)
            self.active = None

    # ---------- Stick motion ----------
    def on_stick_motion(self, ctrl, stick_name, position: Vec2):
        x, y = position.x, position.y
        if abs(x) < DEAD_ZONE:
            x = 0.0
        if abs(y) < DEAD_ZONE:
            y = 0.0

        if stick_name.lower() == "leftstick":
            self.left_x, self.left_y = x, y
            self._update_stick_state("left")
        elif stick_name.lower() == "rightstick":
            self.right_x, self.right_y = x, y
            self._update_stick_state("right")

    # ---------- Trigger motion ----------
    def on_trigger_motion(self, ctrl, trigger_name: str, value: float):
        if trigger_name.lower() == "lefttrigger":
            self.left_trigger = value
            self._update_trigger_state("left")
        elif trigger_name.lower() == "righttrigger":
            self.right_trigger = value
            self._update_trigger_state("right")

    def _update_trigger_state(self, side: str):
        if side == "left":
            value = self.left_trigger
            active_attr = "_left_trigger_pressed"
        else:
            value = self.right_trigger
            active_attr = "_right_trigger_pressed"

        is_pressed = getattr(self, active_attr)
        trig_event_prefix = f"{side}trigger"

        # Pressed
        if not is_pressed and value > TRIGGER_THRESHOLD:
            setattr(self, active_attr, True)
            print(f"🔫 {trig_event_prefix} PRESSED ({value:.2f})")
            self.dispatch_event(f"on_{trig_event_prefix}_pressed")

        # Released
        elif is_pressed and value < TRIGGER_THRESHOLD * 0.8:
            setattr(self, active_attr, False)
            print(f"🔫 {trig_event_prefix} RELEASED ({value:.2f})")
            self.dispatch_event(f"on_{trig_event_prefix}_released")

    # ---------- Direction computation ----------
    def _compute_direction(self, x: float, y: float):
        if -DEAD_ZONE <= x <= DEAD_ZONE and -DEAD_ZONE <= y <= DEAD_ZONE:
            return None

        angle = math.degrees(math.atan2(y, x))
        if angle < 0:
            angle += 360

        if 337.5 <= angle or angle < 22.5:
            return "right"
        elif 22.5 <= angle < 67.5:
            return "up_right"
        elif 67.5 <= angle < 112.5:
            return "up"
        elif 112.5 <= angle < 157.5:
            return "up_left"
        elif 157.5 <= angle < 202.5:
            return "left"
        elif 202.5 <= angle < 247.5:
            return "down_left"
        elif 247.5 <= angle < 292.5:
            return "down"
        elif 292.5 <= angle < 337.5:
            return "down_right"
        return None

    def _update_stick_state(self, side: str):
        if side == "left":
            x, y = self.left_x, self.left_y
            state_attr = "_left_state"
        else:
            x, y = self.right_x, self.right_y
            state_attr = "_right_state"

        current_state = getattr(self, state_attr)
        new_state = self._compute_direction(x, y)

        if new_state and new_state != current_state:
            setattr(self, state_attr, new_state)
            print(f"🚨 {side}stick → {new_state.upper()} event")
            self.dispatch_event(f"on_{side}stick_{new_state}")
        elif new_state is None and current_state is not None:
            setattr(self, state_attr, None)
            print(f"⚙️  {side}stick → CENTERED event")
            self.dispatch_event(f"on_{side}stick_centered")

    # ---------- Drawing ----------
    def on_draw(self):
        self.clear()
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        radius = 80

        # Left stick
        arcade.draw_circle_outline(cx - 250, cy, radius, arcade.color.LIGHT_GRAY, 3)
        arcade.draw_circle_filled(
            cx - 250 + self.left_x * radius, cy + self.left_y * radius, 12, arcade.color.AO
        )

        # Right stick
        arcade.draw_circle_outline(cx + 250, cy, radius, arcade.color.LIGHT_GRAY, 3)
        arcade.draw_circle_filled(
            cx + 250 + self.right_x * radius, cy + self.right_y * radius, 12, arcade.color.ORANGE
        )

        # Trigger bars
        lt_bar = int(self.left_trigger * 100)
        rt_bar = int(self.right_trigger * 100)
        lt_rect = arcade.rect.LBWH(cx - 450, 50, lt_bar, 12)
        rt_rect = arcade.rect.LBWH(cx + 350, 50, rt_bar, 12)
        arcade.draw_rect_filled(lt_rect, arcade.color.GREEN)
        arcade.draw_rect_filled(rt_rect, arcade.color.RED)

        # Cached text labels
        self._cached_text["L2"].draw()
        self._cached_text["R2"].draw()
        self._cached_text["hint"].draw()

        # Dynamic trigger values
        arcade.draw_text(f"L2: {self.left_trigger:.2f}", cx - 420, 100, arcade.color.WHITE, 14)
        arcade.draw_text(f"R2: {self.right_trigger:.2f}", cx + 350, 100, arcade.color.WHITE, 14)

    def on_close(self):
        if self.active:
            self.active.remove_handlers(self)
            self.active.close()
        super().on_close()


# ---------- Example listener ----------
def example_listener(window: ControllerVisualizer):
    def make_handler(msg):
        return lambda: print(f"🎯 External handler: {msg}")

    mapping = {}
    directions = [
        "left", "right", "up", "down",
        "up_left", "up_right", "down_left", "down_right", "centered",
    ]
    for side in ("leftstick", "rightstick"):
        for direction in directions:
            mapping[f"on_{side}_{direction}"] = make_handler(f"{side} moved {direction.upper()}")

    for trig in ("lefttrigger", "righttrigger"):
        mapping[f"on_{trig}_pressed"] = make_handler(f"{trig} PRESSED")
        mapping[f"on_{trig}_released"] = make_handler(f"{trig} RELEASED")

    window.push_handlers(**mapping)


def main():
    window = ControllerVisualizer()
    example_listener(window)
    arcade.run()


if __name__ == "__main__":
    main()
