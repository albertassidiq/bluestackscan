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
        # Auto-detect ADB
        bs_adb = r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe"
        if os.path.exists(bs_adb):
            self.adb_cmd = f'"{bs_adb}"'
        else:
            self.adb_cmd = "adb"
            
        self.adb = f"{self.adb_cmd} -s 127.0.0.1:{adb_port}"
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
        # Try finding devices first
        print(f"    Using ADB: {self.adb_cmd}")
        subprocess.run(f"{self.adb_cmd} start-server", shell=True, capture_output=True)
        
        cmd = f"{self.adb_cmd} connect 127.0.0.1:5555"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        ok = "connected" in result.stdout.lower() or "already" in result.stdout.lower()
        if ok:
             print(f"✓ {result.stdout.strip()}")
        else:
             print(f"✗ Connection Failed. Output:\n{result.stdout}\nError:\n{result.stderr}")
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
            print("    SCROLL DOWN (Exact 178px)")
            # Adjusted to match exact user request: 178px
            # 700 - 178 = 522
            self.cmd("shell input swipe 500 700 500 522 500")
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
        Returns a LIST of candidates sorted by Y (Top-to-Bottom).
        Each candidate: {'x': x, 'y': y, 'dist': dist_from_center}
        """
        data = self.get_ocr_data(img)
        if not data: return []
        
        candidates = [] 
        for i, txt in enumerate(data['text']):
            if txt and "aktif" in txt.lower():
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                
                # Filter valid badge area (SAFE ZONE Y > 220)
                if 200 < x < 600 and 220 < y < 950 and w > 20: 
                    # Check ignored ranges
                    is_ignored = False
                    for (ymin, ymax) in ignored_y_ranges:
                        if ymin <= y <= ymax:
                            is_ignored = True
                            break
                    if is_ignored: continue

                    # Check processed status (AGGRESSIVE & DEBUG)
                    is_processed = False
                    nearby_texts = [] # For debug
                    
                    for j, txt2 in enumerate(data['text']):
                        if i == j: continue
                        # Widen Vertical to Y-200 to Y+100 (Cover whole card area)
                        dy = data['top'][j] - y
                        if -200 < dy < 100:
                            # Horizontal check (wide)
                            if abs(data['left'][j] - x) < 900:
                                t = txt2.upper().strip()
                                if t: nearby_texts.append(t)
                                
                                if "SUDAH" in t or "GC" in t or "STATUS" in t or "SELESAI" in t:
                                    is_processed = True
                                    print(f"    [SKIP] Found processed keyword '{t}' near candidate Y={y}")
                                    break
                    
                    if not is_processed:
                        # print(f"    [Candidate] Y={y} OK. Nearby text: {nearby_texts}") # Optional: Enable if desperate
                        candidates.append({'x': x, 'y': y, 'dist': abs(y - 550)})
                    
                    if not is_processed:
                        candidates.append({'x': x, 'y': y, 'dist': abs(y - 550)})
        
        # Sort Top-to-Bottom by default
        candidates.sort(key=lambda k: k['y'])
        return candidates

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
        print("RUNNING AUTOMATION v7.2 (Better Bottom Logic)")
        print("="*40)
        
        if not self.connect(): return
        
        processed_count = 0
        current_ignored_ys = [] 
        last_screen_hash = ""
        is_bottom = False

        while processed_count < max_items:
            img = self.screenshot()
            ocr_text = pytesseract.image_to_string(img).lower()
            current_screen_hash = hash(ocr_text)
            
            print(f"\nScanning (Processed: {processed_count})...")
            
            # 1. AUTO-COLLAPSE (But check for Tandai first!)
            if any(x in ocr_text for x in ["lihat peta", "detail lengkap", "hasil ground check", "lihat lokasi gc"]):
                print("  (!) Detected OPEN card.")
                
                # CHECK: Is "Tandai" visible? If yes, process it first!
                if "tandai" in ocr_text:
                    print("  (!) 'Tandai' found on open card. Processing...")
                    if self.do_tandai_flow():
                        processed_count += 1
                        print(f"    ✓ TANDAI FLOW COMPLETE - Total: {processed_count}")
                    else:
                        print("    Tandai flow failed or already processed.")
                    
                    # Now collapse the card
                    print("    Collapsing card...")
                    self.tap(400, 300)
                    time.sleep(1.5)
                else:
                    # No Tandai visible, just collapse
                    print("    No 'Tandai' found. Collapsing...")
                    self.tap(400, 300) # Standard Header Position
                    time.sleep(1.5)
                    
                continue 

            # 2. CHECK "MUAT LEBIH BANYAK"
            if "muat lebih banyak" in ocr_text:
                print("  (!) Found 'Muat Lebih Banyak'. Tapping...")
                loc = self.find_click_position("muat lebih banyak", img)
                if loc:
                    self.tap(loc[0], loc[1])
                else:
                    self.tap(500, 900) # Guess bottom area
                
                print("    Waiting for load...")
                time.sleep(3.0) 
                
                # VALIDATION: Check if button is still there
                check_img = self.screenshot()
                if "muat lebih banyak" in pytesseract.image_to_string(check_img).lower():
                    print("    (!) Click failed? 'Muat Lebih Banyak' still visible.")
                    print("    Retrying force tap (510, 920)...")
                    self.tap(510, 920)
                    time.sleep(3.0)
                    
                    # Check again
                    if "muat lebih banyak" in pytesseract.image_to_string(self.screenshot()).lower():
                         print("    (!) Still visible. Skipping scroll to avoid missing items.")
                         continue

                print("    Load success. Rescanning view immediately (No scroll)...")
                # self.swipe_up() # User requested to check candidates first
                time.sleep(1.5)
                continue
            
            # 3. FIND CANDIDATES
            candidates = self.find_target_card(img, ignored_y_ranges=current_ignored_ys)
            
            if candidates:
                # STRATEGY:
                # If Bottom Mode, we prefer candidates LOWER in the list if open (to finish bottom items)
                # But since we have checks for 'processed', just taking the first Valid one is usually ok.
                # However, to be safe at bottom, we don't clear ignored list, so we naturally move down.
                
                target = candidates[0]
                y = target['y']
                print(f"  Selected Candidate at Y={y} (BottomMode={is_bottom})")
                
                # EXPAND
                self.tap(400, y)
                time.sleep(2.0)
                
                check_img = self.screenshot()
                ocr_check = pytesseract.image_to_string(check_img).lower()
                
                expanded_ok = "tandai" in ocr_check or "latitude" in ocr_check or "peta" in ocr_check
                
                if expanded_ok:
                    if "tandai" not in ocr_check:
                         print("  Expanded but 'Tandai' missing. Skipping.")
                         self.tap(400, y) # Collapse
                    else:
                         print("  Expanded & 'Tandai' found.")
                         if self.do_tandai_flow():
                             processed_count += 1
                             print("    Collapsing card...")
                             self.tap(400, y) 
                             time.sleep(1.0)
                         else:
                             print("    Flow failed.")
                             self.tap(400, y)
                else:
                     print("  Failed to expand. Try chevron...")
                     self.tap(950, y)
                     time.sleep(2.0)
                     if "tandai" in pytesseract.image_to_string(self.screenshot()).lower():
                         if self.do_tandai_flow():
                             processed_count += 1
                             self.tap(950, y)
                     else:
                         print("  Could not expand.")
                
                # Add to ignore for this loop
                current_ignored_ys.append((y - 20, y + 20))

            else:
                 print("  No candidates found.")

            # SCROLL LOGIC
            print("  Scrolling...")
            self.swipe_up()
            
            # CHECK FOR BOTTOM / STUCK
            new_img = self.screenshot()
            new_hash = hash(pytesseract.image_to_string(new_img).lower())
            
            if new_hash == current_screen_hash:
                print("  Screen did not change (Stuck/Bottom).")
                is_bottom = True
                
                # IMPORTANT: DO NOT clear current_ignored_ys here!
                # If we are stuck, we want to skip the Y we just tried and try the NEXT one on the same screen.
                # Only clear if we actually moved to a new screen.
                print("  -> Bottom detected. Keeping ignore list to try next candidate.")
                
                # If we have exhausted all candidates on this static screen, break
                if not candidates: 
                    print("  -> No more candidates on this bottom screen. FINISHED.")
                    break
            else:
                is_bottom = False 
                current_ignored_ys = [] # Reset ignores logic only if we moved to new screen

if __name__ == "__main__":
    BlueStacksAutomation().run()
