# 🚀 NormCode Website Dev Server Launchers

Multiple launcher options to start the development server with one click!

## 📋 Available Launchers

### 1. **Batch File Launcher** (Recommended for Windows)
**File:** `launch_dev.bat`

**How to use:**
- Simply **double-click** `launch_dev.bat`
- A command prompt window will open and start the dev server
- Keep the window open while developing
- Press `Ctrl+C` to stop the server

**Pros:** 
- ✅ Works instantly on all Windows systems
- ✅ No additional setup required
- ✅ Easy to double-click

---

### 2. **PowerShell Launcher**
**File:** `launch_dev.ps1`

**How to use:**
- Right-click `launch_dev.ps1` → **Run with PowerShell**
- Or run in terminal: `.\launch_dev.ps1`

**Note:** If you get a security warning, you may need to enable script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Pros:**
- ✅ Colored output
- ✅ Better error handling
- ✅ Native PowerShell integration

---

### 3. **Python Launcher**
**File:** `launch_dev.py`

**How to use:**
- Double-click `launch_dev.py` (if Python is associated)
- Or run in terminal: `python launch_dev.py`

**Requirements:** Python 3.6+

**Pros:**
- ✅ Cross-platform (works on Windows, Mac, Linux)
- ✅ Clean output
- ✅ Good error handling

---

### 4. **GUI Launcher** ⭐ (Coolest Option!)
**File:** `launch_dev_gui.pyw`

**How to use:**
- **Double-click** `launch_dev_gui.pyw`
- A GUI window will appear with Start/Stop buttons
- Click "▶ Start Server" to launch
- Monitor server output in the window
- Click "■ Stop Server" to stop

**Requirements:** Python 3.6+ with tkinter (usually included)

**Pros:**
- ✅ Visual interface
- ✅ Start/Stop controls
- ✅ Real-time output monitoring
- ✅ No command line needed
- ✅ Clear log button
- ✅ Status indicators

---

### 5. **Silent GUI Launcher** 🌟 (Cleanest Experience!)
**File:** `launch_dev_gui_silent.vbs`

**How to use:**
- **Double-click** `launch_dev_gui_silent.vbs`
- The GUI launcher appears **without any console window**
- Completely silent and clean launch

**Requirements:** Python 3.6+ with tkinter

**Pros:**
- ✅ All benefits of GUI Launcher
- ✅ **No console window** appears
- ✅ Cleanest user experience
- ✅ Perfect for desktop shortcuts

---

## 🎯 Quick Start Guide

### For Complete Beginners:
1. Navigate to the `website` folder
2. **Double-click** `launch_dev.bat` (easiest option)
3. Wait for the server to start
4. Open your browser to the URL shown (usually `http://localhost:5173`)
5. Start developing!

### For GUI Fans (Recommended! 🌟):
1. **Double-click** `launch_dev_gui_silent.vbs` (cleanest) or `launch_dev_gui.pyw`
2. Click the "▶ Start Server" button in the GUI
3. Watch the output in the GUI window
4. Open your browser to the URL shown in the output
5. Use the "■ Stop Server" button when done

---

## 🔧 Creating a Desktop Shortcut (Windows)

To make it even easier, create a desktop shortcut:

1. Right-click on your desktop → **New** → **Shortcut**
2. Browse to the launcher file you prefer (e.g., `launch_dev.bat` or `launch_dev_gui.pyw`)
3. Give it a name like "NormCode Dev Server"
4. Click **Finish**

Now you can launch from your desktop with one click! 🎉

---

## ❓ Troubleshooting

### "npm not found" error:
- Install Node.js from [nodejs.org](https://nodejs.org/)
- Restart your computer after installation

### "Cannot load module" error (PowerShell):
- Run PowerShell as Administrator
- Execute: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Try again

### GUI launcher won't start:
- Make sure Python is installed
- tkinter is usually included with Python on Windows
- If missing, reinstall Python with the "tcl/tk" option checked

### Port already in use:
- Another instance is already running
- Stop it or change the port in `vite.config.ts`

---

## 📝 What These Scripts Do

All launchers perform the same basic steps:
1. Navigate to the website directory
2. Run `npm run dev` (Vite dev server)
3. Keep the server running until you stop it

The dev server provides:
- 🔥 Hot Module Replacement (HMR) - instant updates
- ⚡ Fast refresh - no manual reload needed
- 🐛 Better error messages
- 📱 Network access for testing on mobile devices

---

## 🎨 Customization

You can edit any of these launchers to:
- Change the port number
- Add pre-launch checks
- Open the browser automatically
- Run additional commands

Example: To open browser automatically after launch, add to batch file:
```batch
start http://localhost:5173
npm run dev
```

---

## 💡 Pro Tips

1. **Keep the launcher window open** while developing
2. **Watch for errors** in the output
3. **Use the GUI launcher** if you want better control
4. **Create a keyboard shortcut** for the desktop shortcut
5. The server will auto-reload when you save changes to your code

---

Enjoy developing! 🚀✨

