# BlueStacks Usaha Automation

Automation script for tagging "Usaha" items in the MatchaPro Android app running on BlueStacks.

## Features
- **Auto-traversal**: Scans the list of businesses ("Usaha") one by one.
- **Auto-tagging**: Expands each card, clicks "Tandai", selects "1. Ditemukan", and submits.
- **Smart Logic**:
    - Detects "Aktif" badges to identify cards.
    - Handles processed cards (skips if "Tandai" is missing or "Sudah GC").
    - Auto-collapses cards after processing.
    - Robust scrolling (processes cards sequentially).
    - Loop detection (forces scroll if stuck on the same card).

## Prerequisites
1. **BlueStacks Emulator**:
    - Enable **ADB** in BlueStacks Settings -> Advanced -> ADB Debugging.
    - Connects to `127.0.0.1:5555`.
2. **Python 3.x**: Installed on your system.
3. **Tesseract OCR**:
    - Download and install [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki).
    - Default path assumed: `C:\Program Files\Tesseract-OCR\tesseract.exe`.
4. **ADB Tools**:
    - Ensure `adb` is in your system PATH (or use the one bundled with Android Studio/Platform Tools).

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/albertassidiq/bluestackscan.git
   ```

2. Install Python dependencies:
   ```bash
   pip install Pillow pytesseract
   ```

## Usage

1. **Open BlueStacks** and launch the **MatchaPro** app.
2. Navigate to the **"Direktori Usaha"** (Business Directory) list view.
3. Run the script:
   ```bash
   python bluestacks_automation.py
   ```
4. The script will automatically connect to ADB and start processing cards visible on the screen.

## Configuration
- **Scroll Speed/Distance**: Adjusted in `swipe_up()` method in `bluestacks_automation.py`.
- **Tesseract Path**: If installed elsewhere, update the path in the `__init__` method.

## Troubleshooting
- **ADB not connected**: Ensure BlueStacks ADB is on and try `adb connect 127.0.0.1:5555` manually.
- **Tesseract not found**: Check if Tesseract is installed and the path in the script matches.
- **Script getting stuck**: The script has built-in loop detection, but if UI changes significantly, coordinate offsets might need adjustment.
