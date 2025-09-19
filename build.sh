pyinstaller --name "PacMan" \
--windowed \
--icon "assets/icons/appLogo.png" \
--add-data "assets:assets" \
--add-data "bin:bin" \
--add-data "components:components" \
--add-data "config:config" \
--add-data "helpers:helpers" \
main.py
