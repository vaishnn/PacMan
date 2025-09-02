import sys
import os
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtGui import QFontDatabase

# --- Debugging Snippet ---

# 1. Get the directory where this script is located.
script_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Define the font's filename.
font_filename = "fonts/Figtree/static/Figtree_Light.ttf" # <-- CHANGE THIS

# 3. Join the script's directory with the font filename to create a full, reliable path.
#    (This assumes the font is in the SAME folder as your script.
#    If it's in a subfolder called 'fonts', use:
#    os.path.join(script_dir, "fonts", font_filename))
absolute_font_path = os.path.join(script_dir, font_filename)

# 4. Print the path and check if it exists BEFORE giving it to Qt.
print(f"Attempting to load font from: {absolute_font_path}")
if not os.path.exists(absolute_font_path):
    print("--- ERROR: FILE DOES NOT EXIST AT THIS PATH! ---")
    sys.exit() # Exit if the file isn't found

# --- Standard PyQt Logic ---
app = QApplication(sys.argv)

font_id = QFontDatabase.addApplicationFont(absolute_font_path)

# 5. Check the return value from Qt.
if font_id == -1:
    print("--- QT FAILED TO LOAD THE FONT! ---")
    print("The file exists, so it might be corrupted or not a valid font file.")
else:
    font_families = QFontDatabase.applicationFontFamilies(font_id)
    print(f"Font loaded successfully! Family: '{font_families[0]}'")

# You can continue with your app logic here...
# label = QLabel("Testing...")
# label.show()
# sys.exit(app.exec())
