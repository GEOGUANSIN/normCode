NormCode Canvas - Resources
============================

This folder contains resources for the application packaging.

Required Files:
---------------
1. icon.ico - Application icon (Windows ICO format)
   - Recommended sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
   - Used for: executable icon, window title bar, taskbar, shortcuts

Optional Files:
---------------
2. logo.png - Application logo for splash screen or about dialog
3. banner.bmp - Installer banner (for Inno Setup, 164x314 pixels)
4. wizard.bmp - Installer wizard image (for Inno Setup, 55x58 pixels)

Creating icon.ico:
------------------
You can create an ICO file using:
1. GIMP (free): File > Export As > .ico
2. IcoFX (commercial)
3. Online tools: https://icoconvert.com/

Note: If icon.ico is not present, the build will use the default Python icon.

