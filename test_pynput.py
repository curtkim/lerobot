from pynput import keyboard

def on_press(key):
    try:
        if key.char == 'l':
            print('left')
        elif key.char == 'h':
            print('right')
    except AttributeError:
        # Special keys (like ctrl, alt, etc.) don't have char attribute
        pass

def on_release(key):
    # Stop listener when ESC is pressed
    if key == keyboard.Key.esc:
        return False

# Create listener
with keyboard.Listener(
    on_press=on_press,
    on_release=on_release) as listener:
    print("Press 'l' for left, 'h' for right. Press ESC to exit.")
    listener.join()
