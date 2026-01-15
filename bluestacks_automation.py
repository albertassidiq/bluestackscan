"""
BlueStacks Android App Automation v7
- v6 features (Assume coords, SUDAH detection, Re-scan)
- v7: Stuck detection (Loop breaking), Stronger swipes, Explicit 'Status' detection
"""

import subprocess
import time
import re
import os
import sys

try:
    from PIL import Image
    import pytesseract
except ImportError:
    print("pip install Pillow pytesseract")
    sys.exit(1)


class BlueStacksAutomation:
    def __init__(self, adb_port=5555):
        self.adb = f"adb -s 127.0.0.1:{adb_port}"
        self.screenshot_path = "temp_screenshot.png"
        if os.name == 'nt':
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    def cmd(self, command):
        try:
            result = subprocess.run(f"{self.adb} {command}", shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout
        except:
            return ""
    
    def connect(self):
        subprocess.run("adb start-server", shell=True, capture_output=True)
        result = subprocess.run(f"adb connect 127.0.0.1:5555", shell=True, capture_output=True, text=True)
        ok = "connected" in result.stdout.lower() or "already" in result.stdout.lower()
        print(f"{'✓' if ok else '✗'} {result.stdout.strip()}")
        return ok
    
    def screenshot(self):
        for _ in range(3):
            try:
                if os.path.exists(self.screenshot_path):
                    os.remove(self.screenshot_path)
                
                self.cmd("shell screencap -p /sdcard/screen.png")
                self.cmd(f"pull /sdcard/screen.png {self.screenshot_path}")
                
                time.sleep(0.5) # Wait for write
                if os.path.exists(self.screenshot_path) and os.path.getsize(self.screenshot_path) > 0:
                    return Image.open(self.screenshot_path)
            except Exception as e:
                print(f"    Screenshot error (retrying): {e}")
                time.sleep(1)
                
        return None
    
    def tap(self, x, y):
        print(f"    TAP ({x}, {y})")
        self.cmd(f"shell input tap {x} {y}")
        time.sleep(1.2)
    
    def swipe_up(self, strong=False):
        if strong:
            print("    STRONG SCROLL DOWN (Swipe Up)")
            self.cmd("shell input swipe 500 900 500 200 300")
        else:
            print("    SCROLL DOWN (Small - 1 item)")
            # Swipe jarak dekat: dari 700 ke 550 (geser naik ~150px = tinggi rata2 1 kartu)
            self.cmd("shell input swipe 500 700 500 550 500")
        time.sleep(1.5)
    
    def get_ocr_data(self, img=None):
        if img is None:
            img = self.screenshot()
        return pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT) if img else None
    
    def find_click_position(self, search_text, img=None, y_min=0, y_max=9999):
        data = self.get_ocr_data(img)
        if not data: return None
        for i, txt in enumerate(data['text']):
            # Loose match
            if txt and search_text.lower() in txt.lower():
                y = data['top'][i]
                if y_min < y < y_max:
                    return (data['left'][i] + data['width'][i]//2, y + data['height'][i]//2)
        return None

    def find_target_card(self, img=None, ignored_y_ranges=[]):
        """
        Finds candidate 'Aktif' badge. Ignores if 'SUDAH'/'GC' matches nearby.
        Also ignores Y coords in ignored_y_ranges (list of (min, max)).
        """
        data = self.get_ocr_data(img)
        if not data: return None
        
        candidates = []
        for i, txt in enumerate(data['text']):
            if txt and "aktif" in txt.lower():
                # Filter valid badge area
                if 200 < data['left'][i] < 600 and 150 < data['top'][i] < 950 and data['width'][i] > 20:
                    candidates.append(i)
        
        if not candidates: return None
            
        for i in candidates:
            y_badge = data['top'][i]
            x_badge = data['left'][i]
            
            # Check ignored ranges (Stuck detection)
            is_ignored = False
            for (ymin, ymax) in ignored_y_ranges:
                if ymin <= y_badge <= ymax:
                    is_ignored = True
                    break
            if is_ignored: continue

            # Check for PROCESSED status text nearby
            is_processed = False
            for j, txt in enumerate(data['text']):
                if i == j: continue
                if abs(data['top'][j] - y_badge) < 60: # Same row
                    t = txt.upper()
                    if "SUDAH" in t or "GC" in t or "STATUS" in t:
                        if data['left'][j] > x_badge - 50: # Right of or near badge
                            is_processed = True
                            break
            
            if not is_processed:
                return {'x': x_badge, 'y': y_badge}
        return None

    def do_tandai_flow(self):
        print("    >> START TANDAI FLOW")
        
        # 1. Click 'Tandai'
        loc = self.find_click_position("Tandai", y_min=200)
        if not loc:
            print("    ✗ 'Tandai' not found (Card might be processed?)")
            return False

        self.tap(loc[0], loc[1])
        time.sleep(1.5)

        # 2. Click '-- Pilih --'
        loc = self.find_click_position("Pilih")
        if loc:
            self.tap(loc[0], loc[1])
            time.sleep(1.0)
        else:
             print("    ✗ 'Pilih' not found")
             return False
            
        # 3. Select '1. Ditemukan'
        img = self.screenshot() 
        loc = self.find_click_position("1.", img, y_min=100, y_max=700)
        if not loc:
             loc = self.find_click_position("Ditemukan", img, y_min=100, y_max=700)
        
        if loc:
            self.tap(loc[0] + 50, loc[1])
            time.sleep(1.0)
        else:
            print("    Using fallback tap for dropdown option")
            self.tap(300, 320)
            time.sleep(1.0)
            
        # 4. Click Submit
        img = self.screenshot()
        loc = self.find_click_position("DICEK", img, y_min=700)
        if not loc: loc = self.find_click_position("TANDAI", img, y_min=700)
             
        if loc:
            self.tap(loc[0], loc[1])
            time.sleep(3.0) 
        else:
            print("    Fallback submit tap")
            self.tap(1490, 1010)
            time.sleep(3.0)

        # 5. Click OK
        print("    Clicking 'OK'...")
        self.tap(320, 235) 
        time.sleep(1.5)
        
        print("    ✓ TANDAI FLOW COMPLETE")
        return True

    def run(self, max_items=100):
        print("\n" + "="*40)
        print("RUNNING AUTOMATION v7")
        print("="*40)
        
        if not self.connect(): return
        
        processed_count = 0
        last_y = -1
        stuck_count = 0
        
        # We can temporarily ignore Ys that we just failed on
        current_ignored_ys = [] 
        last_screen_hash = ""

        while processed_count < max_items:
            img = self.screenshot()
            
            # Simple hash: unique set of text on screen to detect if scroll happened
            ocr_blob = pytesseract.image_to_string(img)
            current_screen_hash = hash(ocr_blob)
            
            print(f"\nScanning (Processed: {processed_count}, Stuck: {stuck_count})...")
            
            target = self.find_target_card(img, ignored_y_ranges=current_ignored_ys)
            
            if target:
                y = target['y']
                print(f"  Found Candidate at Y={y}")
                
                # Check stuck
                if abs(y - last_y) < 20:
                    stuck_count += 1
                else:
                    stuck_count = 0
                    # Only reset ignores if we have moved to a NEW card
                    # BUT we might have multiple candidates on one screen.
                    # We should not clear ignores for the current screen.
                
                last_y = y
                
                if stuck_count > 2:
                    print("  STUCK DETECTED (Same card > 2 times). Skipping this Y area.")
                    current_ignored_ys.append((y - 30, y + 30))
                    
                    # Try to force scroll
                    self.swipe_up(strong=True)
                    
                    # Check if scroll worked
                    new_img = self.screenshot()
                    new_hash = hash(pytesseract.image_to_string(new_img))
                    if new_hash == current_screen_hash:
                        print("  Screen did not change after scroll. END OF LIST?")
                        break
                    
                    # If screen changed, continue efficiently
                    continue

                # EXPAND
                self.tap(400, y)
                time.sleep(2.0)
                
                # VERIFY
                check_img = self.screenshot()
                ocr_text = pytesseract.image_to_string(check_img).lower()
                
                # Check expanded state
                expanded_ok = "tandai" in ocr_text or "latitude" in ocr_text or "peta" in ocr_text
                
                if expanded_ok:
                    # Double check if it's already processed ("Lihat Peta" or "Status")
                    if "tandai" not in ocr_text:
                        print("  Expanded, but 'Tandai' missing (Already Processed?). Skipping.")
                        self.tap(400, y) # Collapse
                        # Add to ignore list for this screen so we don't pick it again immediately
                        current_ignored_ys.append((y - 30, y + 30))
                        
                        # Just continue to find next candidate on SAME screen if possible
                        # Don't scroll yet if there are other candidates?
                        # For simplicity, scroll a bit to move on
                        self.swipe_up()
                        continue
                    
                    print("  Expanded & 'Tandai' found.")
                    if self.do_tandai_flow():
                        processed_count += 1
                        stuck_count = 0
                        print("    Collapsing card...")
                        self.tap(400, y)
                        time.sleep(1.0)
                        
                        self.swipe_up()
                        
                        # Reset ignores after successful processing and scroll
                        current_ignored_ys = [] 
                    else:
                         print("  Flow failed. Collapsing.")
                         self.tap(400, y)
                         self.swipe_up()
                         stuck_count += 1

                else:
                    # Try chevron
                    print("  Failed to expand. Try chevron...")
                    self.tap(950, y)
                    time.sleep(2.0)
                    
                    check2 = pytesseract.image_to_string(self.screenshot()).lower()
                    if "tandai" in check2:
                         print("  Expanded via chevron.")
                         if self.do_tandai_flow():
                             processed_count += 1
                             stuck_count = 0
                             print("    Collapsing...")
                             self.tap(950, y)
                             time.sleep(1.0)
                             self.swipe_up()
                             current_ignored_ys = []
                         else:
                             self.tap(950, y)
                             self.swipe_up()
                             stuck_count += 1
                    else:
                        print("  Could not expand. Skipping.")
                        self.swipe_up()
                        # If detecting same Y next time, stuck logic will catch it

            else:
                print("  No candidates found. Scrolling...")
                self.swipe_up()
                
                # Check end of list
                check_img = self.screenshot()
                new_hash = hash(pytesseract.image_to_string(check_img))
                if new_hash == current_screen_hash:
                    print("  Screen did not change. END OF LIST reached.")
                    break
                
                # Only reset ignores if screen changed
                current_ignored_ys = [] 
                time.sleep(1.0)

        print(f"\nDone. Processed {processed_count} items.")

if __name__ == "__main__":
    BlueStacksAutomation().run()
