"""Debug script to see what controls are available in Control Panel"""
import sys
import time
import subprocess
from pywinauto import Desktop

# Open Control Panel
subprocess.Popen("control", shell=True)
print("Waiting for Control Panel to open...")
time.sleep(3)

# Find the window
desktop = Desktop(backend="uia")
windows = desktop.windows()

print("\nAll open windows:")
for i, window in enumerate(windows):
    try:
        title = window.window_text()
        print(f"{i}. {title}")
    except:
        pass

print("\n" + "="*50)
print("Looking for Control Panel window...")

control_panel = None
for window in windows:
    try:
        title = window.window_text().lower()
        if "control" in title or "panel" in title:
            control_panel = window
            print(f"Found: {window.window_text()}")
            break
    except:
        pass

if control_panel:
    print("\n" + "="*50)
    print("Top-level children (direct children only):")
    try:
        for i, child in enumerate(control_panel.children()):
            try:
                text = child.window_text()
                ctype = child.element_info.control_type
                classname = child.element_info.class_name
                print(f"{i}. '{text}' (type={ctype}, class={classname})")
            except Exception as e:
                print(f"{i}. <error: {e}>")
    except Exception as e:
        print(f"Error listing children: {e}")

    print("\n" + "="*50)
    print("All descendants (first 50):")
    try:
        for i, child in enumerate(control_panel.descendants()[:50]):
            try:
                text = child.window_text()
                ctype = child.element_info.control_type
                print(f"{i}. '{text}' (type={ctype})")
            except Exception as e:
                print(f"{i}. <error: {e}>")
    except Exception as e:
        print(f"Error listing descendants: {e}")
else:
    print("Control Panel window not found!")
