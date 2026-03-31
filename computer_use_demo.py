"""
DreamFinder — Computer Use Demo
================================
Uses the Claude API's computer use tool to interact with the DreamFinder
web app in a browser. Claude can take screenshots, click elements, type
text, and navigate the sleep consultation quiz autonomously.

Prerequisites:
    pip install anthropic Pillow

Usage:
    1. Set your API key:  export ANTHROPIC_API_KEY="sk-ant-..."
    2. Open DreamFinder in a browser on your desktop
    3. Run:  python computer_use_demo.py

    Optionally pass a custom prompt:
        python computer_use_demo.py "Navigate through the quiz and pick a firm mattress"

Environment variables:
    ANTHROPIC_API_KEY   — Required. Your Anthropic API key.
    DISPLAY_WIDTH       — Screen width in pixels  (default: 1920)
    DISPLAY_HEIGHT      — Screen height in pixels (default: 1080)
"""

import anthropic
import base64
import io
import os
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DISPLAY_WIDTH = int(os.environ.get("DISPLAY_WIDTH", 1920))
DISPLAY_HEIGHT = int(os.environ.get("DISPLAY_HEIGHT", 1080))
MODEL = "claude-opus-4-6"
BETA_FLAG = "computer-use-2025-11-24"
MAX_TURNS = 30

DEFAULT_PROMPT = (
    "You are testing the DreamFinder sleep consultation web app. "
    "Take a screenshot first, then walk through the entire quiz from start "
    "to finish. Click the appropriate answers for a side-sleeper who prefers "
    "a medium-firm mattress with cooling features. After the quiz, take a "
    "final screenshot of the recommendation results."
)

# ---------------------------------------------------------------------------
# Tool execution helpers
# ---------------------------------------------------------------------------


def take_screenshot() -> str:
    """Capture the screen and return a base64-encoded PNG."""
    try:
        # Try scrot (Linux)
        path = "/tmp/screenshot.png"
        subprocess.run(["scrot", path], check=True, capture_output=True)
        with open(path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode()
    except FileNotFoundError:
        pass

    try:
        # Try macOS screencapture
        path = "/tmp/screenshot.png"
        subprocess.run(["screencapture", "-x", path], check=True, capture_output=True)
        with open(path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode()
    except FileNotFoundError:
        pass

    raise RuntimeError(
        "No screenshot tool found. Install 'scrot' (Linux) or use macOS."
    )


def execute_mouse_action(action: str, coordinate: list[int], **kwargs):
    """Execute a mouse action using xdotool (Linux) or cliclick (macOS)."""
    x, y = coordinate

    try:
        if action == "left_click":
            subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"], check=True)
        elif action == "right_click":
            subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "3"], check=True)
        elif action == "double_click":
            subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "--repeat", "2", "1"], check=True)
        elif action == "left_click_drag":
            end = kwargs.get("end_coordinate", coordinate)
            subprocess.run(["xdotool", "mousemove", str(x), str(y), "mousedown", "1"], check=True)
            subprocess.run(["xdotool", "mousemove", str(end[0]), str(end[1]), "mouseup", "1"], check=True)
        return True
    except FileNotFoundError:
        print("  [!] xdotool not found — install it for mouse control")
        return False


def execute_keyboard_action(action: str, text: str = "", key: str = ""):
    """Execute keyboard input using xdotool."""
    try:
        if action == "type":
            subprocess.run(["xdotool", "type", "--clearmodifiers", text], check=True)
        elif action == "key":
            # Convert Claude's key format (e.g. "ctrl+s") to xdotool format
            subprocess.run(["xdotool", "key", key], check=True)
        return True
    except FileNotFoundError:
        print("  [!] xdotool not found — install it for keyboard control")
        return False


def execute_scroll(coordinate: list[int], direction: str, amount: int = 3):
    """Scroll at the given coordinate."""
    x, y = coordinate
    try:
        subprocess.run(["xdotool", "mousemove", str(x), str(y)], check=True)
        button = "5" if direction == "down" else "4"
        for _ in range(amount):
            subprocess.run(["xdotool", "click", button], check=True)
        return True
    except FileNotFoundError:
        print("  [!] xdotool not found — install it for scroll control")
        return False


def handle_tool_call(tool_name: str, tool_input: dict) -> dict:
    """Route a computer use tool call to the appropriate handler."""
    action = tool_input.get("action")

    if action == "screenshot":
        print("  [screenshot]")
        img_b64 = take_screenshot()
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64,
            },
        }

    if action in ("left_click", "right_click", "double_click", "left_click_drag"):
        coord = tool_input.get("coordinate", [0, 0])
        print(f"  [{action}] at ({coord[0]}, {coord[1]})")
        execute_mouse_action(action, coord, **tool_input)
        time.sleep(0.5)
        # Return a screenshot so Claude can see the result
        img_b64 = take_screenshot()
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64,
            },
        }

    if action == "type":
        text = tool_input.get("text", "")
        print(f"  [type] '{text[:40]}...'") if len(text) > 40 else print(f"  [type] '{text}'")
        execute_keyboard_action("type", text=text)
        return {"type": "text", "text": "Typed successfully."}

    if action == "key":
        key = tool_input.get("key", "")
        print(f"  [key] {key}")
        execute_keyboard_action("key", key=key)
        return {"type": "text", "text": f"Pressed {key}."}

    if action == "scroll":
        coord = tool_input.get("coordinate", [DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2])
        direction = tool_input.get("direction", "down")
        amount = tool_input.get("amount", 3)
        print(f"  [scroll] {direction} at ({coord[0]}, {coord[1]})")
        execute_scroll(coord, direction, amount)
        time.sleep(0.3)
        img_b64 = take_screenshot()
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64,
            },
        }

    if action == "wait":
        wait_ms = tool_input.get("duration", 1000)
        print(f"  [wait] {wait_ms}ms")
        time.sleep(wait_ms / 1000)
        return {"type": "text", "text": f"Waited {wait_ms}ms."}

    return {"type": "text", "text": f"Unknown action: {action}"}


# ---------------------------------------------------------------------------
# Main agent loop
# ---------------------------------------------------------------------------


def run(prompt: str):
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    tools = [
        {
            "type": "computer_20251124",
            "name": "computer",
            "display_width_px": DISPLAY_WIDTH,
            "display_height_px": DISPLAY_HEIGHT,
        },
    ]

    messages = [{"role": "user", "content": prompt}]

    print(f"Display: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")
    print(f"Model:   {MODEL}")
    print(f"Prompt:  {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print("-" * 60)

    for turn in range(1, MAX_TURNS + 1):
        print(f"\n--- Turn {turn} ---")

        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=4096,
            tools=tools,
            messages=messages,
            betas=[BETA_FLAG],
        )

        # Collect assistant content blocks
        assistant_content = response.content

        # Print any text blocks
        for block in assistant_content:
            if hasattr(block, "text"):
                print(f"  Claude: {block.text}")

        # Check if we're done
        if response.stop_reason == "end_turn":
            print("\n[Done] Claude finished.")
            break

        # Process tool use blocks
        tool_results = []
        for block in assistant_content:
            if block.type == "tool_use":
                result = handle_tool_call(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": [result],
                    }
                )

        if not tool_results:
            print("\n[Done] No more tool calls.")
            break

        # Append assistant message and tool results for next turn
        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})

    else:
        print(f"\n[Stopped] Reached max turns ({MAX_TURNS}).")

    print("\nSession complete.")


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT
    run(prompt)
