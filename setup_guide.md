# BlueStacks Automation Setup Guide

## Prerequisites

### 1. Install Python 3.8+
Make sure Python is installed and available in your PATH.

### 2. Install Tesseract OCR

Tesseract is required for text recognition. Download and install from:

**Windows:**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (use default options)
3. **Important:** During installation, note the install path (usually `C:\Program Files\Tesseract-OCR`)
4. Add Tesseract to your PATH:
   - Open "Environment Variables" (search in Windows)
   - Under "System variables", find "Path" and click "Edit"
   - Add the Tesseract install path (e.g., `C:\Program Files\Tesseract-OCR`)
   - Click OK

### 3. Enable ADB in BlueStacks

1. Open BlueStacks
2. Click the **gear icon** (Settings)
3. Go to **Advanced**
4. Enable **Android Debug Bridge (ADB)**
5. Note the port number shown (usually `5555`)
6. **Restart BlueStacks**

### 4. Install ADB (if not already installed)

ADB usually comes with BlueStacks, but if not:

1. Download Android Platform Tools: https://developer.android.com/studio/releases/platform-tools
2. Extract to a folder (e.g., `C:\adb`)
3. Add the folder to your PATH

## Installation

Open PowerShell/Command Prompt in the project folder and run:

```powershell
# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Running the Automation

1. **Open BlueStacks** and launch the app
2. **Navigate to the Usaha list screen** in the app
3. Make sure the BlueStacks window is **visible** (not minimized)
4. Run the script:

```powershell
python bluestacks_automation.py
```

5. Press **Enter** when prompted to start the automation

## Troubleshooting

### "Cannot connect to BlueStacks"

- Make sure BlueStacks is running
- Check that ADB is enabled in BlueStacks settings
- Try restarting BlueStacks
- The script will try ports 5555, 5556, and 5557 automatically

### "Tesseract not found"

- Make sure Tesseract is installed
- Add Tesseract to your PATH
- Or edit the script and update the `tesseract_paths` list

### "Text not found on screen"

- Make sure the app is on the correct screen
- The BlueStacks window must be visible (not minimized)
- Try adjusting the screen resolution to 1920x1080

### Slow performance

- Close other applications
- Increase BlueStacks memory allocation in settings
- The OCR processing takes some time per screenshot

## How It Works

1. **Connect via ADB** - The script connects to BlueStacks using Android Debug Bridge
2. **Take Screenshots** - Captures the BlueStacks screen
3. **OCR Processing** - Uses Tesseract to read text from screenshots
4. **Find Elements** - Locates buttons and text by their content
5. **Send Taps** - Uses ADB to tap at specific coordinates
6. **Repeat** - Processes each usaha and loads more when needed

## Customization

### Adjust timing

If the automation is too fast/slow, edit these in the script:

```python
time.sleep(1)  # Wait time after actions (in seconds)
```

### Change ADB port

```python
automation = BlueStacksAutomation(adb_port=5556)
```

### Limit items to process

```python
automation.run_automation(max_items=10)  # Process only 10 items
```
