import arcade
from pyglet.math import Vec2
from pyglet.event import EventDispatcher
import math

DEAD_ZONE = 0.2
TRIGGER_THRESHOLD = 0.6


class ViewWithGamepadSupport(arcade.View, EventDispatcher):
    """
    Base window class providing reusable gamepad support.
    Inherit this for any game view that needs controller input.
    """

    def __init__(self, window: arcade.Window = None):
        super().__init__(window)

        # ---------------- Controller Setup ----------------
        self.manager = arcade.ControllerManager()
        self.manager.push_handlers(self)

        self.active = None
        controllers = arcade.get_controllers()
        if controllers:
            self._use_controller(controllers[0])
            print(f"[INFO] Connected to controller: {controllers[0].name}")
        else:
            print("[INFO] No controllers detected.")

        # ---------------- Input State ----------------
        self.left_x = self.left_y = 0.0
        self.right_x = self.right_y = 0.0
        self.left_trigger = self.right_trigger = 0.0
        self._left_state = None
        self._right_state = None
        self._left_trigger_pressed = False
        self._right_trigger_pressed = False
        self.dpad_x = self.dpad_y = 0
        self.buttons_pressed = set()

        # ---------------- Register Custom Events ----------------
        # 8-way stick + centered
        directions = [
            "left", "right", "up", "down",
            "up_left", "up_right", "down_left", "down_right", "centered",
        ]
        for side in ("leftstick", "rightstick"):
            for d in directions:
                self.register_event_type(f"on_{side}_{d}")

        # Trigger pressed / released
        for trig in ("lefttrigger", "righttrigger"):
            for state in ("pressed", "released"):
                self.register_event_type(f"on_{trig}_{state}")

        #D-pad
        for d in ("up", "down", "left", "right", "centered"):
            self.register_event_type(f"on_dpad_{d}")

    # ==========================================================
    # Controller Lifecycle
    # ==========================================================
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

    # ==========================================================
    # Button & D-Pad Handling
    # ==========================================================
    def on_button_press(self, ctrl, button_name):
        self.buttons_pressed.add(button_name)
        # D-pad fallback (avoid shoulder confusion)
        if button_name == "dpad_up":
            self.dpad_y = 1
        elif button_name == "dpad_down":
            self.dpad_y = -1
        elif button_name == "dpad_left":
            self.dpad_x = -1
        elif button_name == "dpad_right":
            self.dpad_x = 1

    def on_button_release(self, ctrl, button_name):
        self.buttons_pressed.discard(button_name)
        if button_name in {"dpad_up", "dpad_down"}:
            self.dpad_y = 0
        elif button_name in {"dpad_left", "dpad_right"}:
            self.dpad_x = 0

    def on_dpad_motion(self, ctrl, vector: Vec2):
        old_x, old_y = getattr(self, "dpad_x", 0), getattr(self, "dpad_y", 0)
        new_x, new_y = int(vector.x), int(vector.y)
        self.dpad_x, self.dpad_y = new_x, new_y

        # Edge-triggered events
        if new_x == 1 and old_x != 1:
            self.dispatch_event("on_dpad_right")
        elif new_x == -1 and old_x != -1:
            self.dispatch_event("on_dpad_left")
        elif new_y == 1 and old_y != 1:
            self.dispatch_event("on_dpad_up")
        elif new_y == -1 and old_y != -1:
            self.dispatch_event("on_dpad_down")

        # When returning to center
        if (new_x, new_y) == (0, 0) and (old_x, old_y) != (0, 0):
            self.dispatch_event("on_dpad_centered")

    # ==========================================================
    # Sticks
    # ==========================================================
    def on_stick_motion(self, ctrl, stick_name, position: Vec2):
        x, y = position.x, position.y
        if abs(x) < DEAD_ZONE:
            x = 0
        if abs(y) < DEAD_ZONE:
            y = 0

        if stick_name.lower() == "leftstick":
            self.left_x, self.left_y = x, y
            self._update_stick_state("left")
        elif stick_name.lower() == "rightstick":
            self.right_x, self.right_y = x, y
            self._update_stick_state("right")

    def _compute_direction(self, x, y):
        """Return one of 8 directions or None if centered."""
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

    def _update_stick_state(self, side):
        """Detect edge crossings and dispatch one-shot events."""
        if side == "left":
            x, y = self.left_x, self.left_y
            attr = "_left_state"
        else:
            x, y = self.right_x, self.right_y
            attr = "_right_state"

        current = getattr(self, attr)
        new_state = self._compute_direction(x, y)

        if new_state and new_state != current:
            setattr(self, attr, new_state)
            self.dispatch_event(f"on_{side}stick_{new_state}")
        elif new_state is None and current is not None:
            setattr(self, attr, None)
            self.dispatch_event(f"on_{side}stick_centered")

    # ==========================================================
    # Triggers
    # ==========================================================
    def on_trigger_motion(self, ctrl, trigger_name, value):
        if "left" in trigger_name.lower():
            self.left_trigger = value
            self._update_trigger_state("left")
        elif "right" in trigger_name.lower():
            self.right_trigger = value
            self._update_trigger_state("right")

    def _update_trigger_state(self, side):
        if side == "left":
            value = self.left_trigger
            attr = "_left_trigger_pressed"
        else:
            value = self.right_trigger
            attr = "_right_trigger_pressed"

        is_pressed = getattr(self, attr)
        trig_name = f"{side}trigger"

        # pressed
        if not is_pressed and value > TRIGGER_THRESHOLD:
            setattr(self, attr, True)
            self.dispatch_event(f"on_{trig_name}_pressed")
        # released
        elif is_pressed and value < TRIGGER_THRESHOLD * 0.8:
            setattr(self, attr, False)
            self.dispatch_event(f"on_{trig_name}_released")

    # ==========================================================
    def on_close(self):
        """Clean up Controller after closing the window."""
        if self.active:
            self.active.remove_handlers(self)
            self.active.close()

