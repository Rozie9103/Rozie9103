import random
import time
import threading
import sys
import os
from rich.text import Text
from rich.live import Live

class MatrixEffect:
    """
    Kelas untuk menampilkan efek matrix hacker sinematik dengan head putih dan trail hijau memudar.
    """
    
    def __init__(self, width=80, height=24, speed=0.05, charset=None, color_trail=None):
        """
        Inisialisasi efek matrix.
        
        Args:
            width (int): Lebar layar (jumlah kolom).
            height (int): Tinggi layar (jumlah baris).
            speed (float): Delay antar frame (semakin kecil semakin cepat).
            charset (str, optional): Karakter yang digunakan dalam efek matrix.
            color_trail (list, optional): Daftar warna untuk trail (dari terang ke gelap).
        """
        self.width = width
        self.height = height
        self.speed = speed
        self.stop_event = threading.Event()
        self.thread = None
        
        # Default charset dan warna jika tidak disediakan
        self.charset = charset or "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&"
        self.color_trail = color_trail or ["#00ff00", "#00cc00", "#009900", "#006600", "#003300"]
        
        # Inisialisasi kolom
        self.columns = [
            {
                "head": random.randint(0, height-1),
                "trail": random.randint(6, 16),
                "speed": random.uniform(0.8, 1.5),
                "tick": 0
            }
            for _ in range(width)
        ]
        
        # Buffer untuk setiap baris (untuk efek jejak)
        self.buffer = [[" " for _ in range(width)] for _ in range(height)]
    
    def _update_matrix(self):
        """Update posisi dan karakter dalam buffer matrix."""
        for x, col in enumerate(self.columns):
            col["tick"] += 1
            if col["tick"] >= col["speed"]:
                col["tick"] = 0
                # Geser head ke bawah, reset jika keluar layar
                col["head"] = (col["head"] + 1) % self.height
                # Random panjang trail kadang2
                if random.random() < 0.05:
                    col["trail"] = random.randint(6, 16)
                # Set karakter head baru
                self.buffer[col["head"]][x] = random.choice(self.charset)
                # Kosongkan karakter di ujung trail
                tail = (col["head"] - col["trail"]) % self.height
                self.buffer[tail][x] = " "
    
    def _render_frame(self):
        """Render frame dari buffer dengan efek warna."""
        lines = []
        for y in range(self.height):
            line = Text()
            for x, col in enumerate(self.columns):
                char = self.buffer[y][x]
                # Head
                if y == col["head"]:
                    line.append(char, style="bold white")
                # Trail (warna memudar)
                elif 0 < (col["head"] - y) % self.height <= len(self.color_trail):
                    idx = (col["head"] - y) % self.height - 1
                    color = self.color_trail[min(idx, len(self.color_trail)-1)]
                    line.append(char, style=f"bold {color}")
                else:
                    line.append(" ", style="black")
            lines.append(line)
        return Text("\n").join(lines)
    
    def run(self):
        """Jalankan animasi matrix dalam thread saat ini."""
        with Live(refresh_per_second=30, transient=True) as live:
            while not self.stop_event.is_set():
                self._update_matrix()
                live.update(self._render_frame())
                time.sleep(self.speed)
    
    def start(self):
        """Mulai animasi matrix dalam thread terpisah."""
        if self.thread and self.thread.is_alive():
            return False
        
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def stop(self, join=True):
        """
        Hentikan animasi matrix.
        
        Args:
            join (bool): Jika True, tunggu thread selesai sebelum melanjutkan.
        """
        if not self.thread:
            return
            
        self.stop_event.set()
        if join and self.thread.is_alive():
            self.thread.join()


def matrix_effect_hacker(stop_event, width=80, height=24, speed=0.05):
    """
    Efek matrix hacker sinematik: head putih, trail hijau memudar, randomisasi kecepatan dan panjang trail.
    
    Args:
        stop_event (threading.Event): Event untuk menghentikan animasi.
        width (int): Lebar layar (jumlah kolom).
        height (int): Tinggi layar (jumlah baris).
        speed (float): Delay antar frame (semakin kecil semakin cepat).
    """
    matrix = MatrixEffect(width=width, height=height, speed=speed)
    matrix.stop_event = stop_event
    matrix.run()


def cmatrix_windows_effect(stop_event, width=80, height=24, speed=0.04):
    """
    Efek matrix mirip CMatrix untuk terminal Windows (CMD/PowerShell).
    Hanya karakter ASCII hijau, tanpa library Rich.
    
    Args:
        stop_event (threading.Event): Event untuk menghentikan animasi.
        width (int): Lebar layar (jumlah kolom).
        height (int): Tinggi layar (jumlah baris).
        speed (float): Delay antar frame (semakin kecil semakin cepat).
    """
    charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&"
    columns = [random.randint(0, height-1) for _ in range(width)]
    
    # Enable ANSI escape code on Windows (for color)
    if os.name == 'nt':
        os.system('')
    
    GREEN = "\033[32m"
    BRIGHT_GREEN = "\033[1;32m"
    RESET = "\033[0m"
    CLEAR = "\033[2J"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"
    
    try:
        sys.stdout.write(CLEAR + HIDE_CURSOR)
        sys.stdout.flush()
        while not stop_event.is_set():
            for y in range(height):
                line = ""
                for x in range(width):
                    if columns[x] == y:
                        # Head karakter (lebih terang)
                        char = random.choice(charset)
                        line += f"{BRIGHT_GREEN}{char}{RESET}"
                    elif columns[x] < y and y <= columns[x] + 5:
                        # Trail karakter (hijau normal)
                        if random.random() > 0.3:  # Beberapa karakter hilang untuk efek memudar
                            char = random.choice(charset)
                            line += f"{GREEN}{char}{RESET}"
                        else:
                            line += " "
                    else:
                        line += " "
                print(line)
            
            # Geser head ke bawah dengan kecepatan random
            columns = [(y+1) % height if random.random() > 0.05 else y for y in columns]
            time.sleep(speed)
            
            # Kembali ke atas layar
            sys.stdout.write(f"\033[{height}A")
            sys.stdout.flush()
    finally:
        sys.stdout.write(SHOW_CURSOR + RESET + "\n")
        sys.stdout.flush()


# Contoh pemakaian:
# 
# 1. Menggunakan fungsi lama (kompatibilitas):
# import threading
# stop_event = threading.Event()
# matrix_thread = threading.Thread(target=matrix_effect_hacker, args=(stop_event, 80, 24, 0.05))
# matrix_thread.start()
# # ... (jalankan proses lain)
# stop_event.set()
# matrix_thread.join()
#
# 2. Menggunakan kelas baru (lebih fleksibel):
# matrix = MatrixEffect(width=80, height=24, speed=0.05)
# matrix.start()
# # ... (jalankan proses lain)
# matrix.stop()
#
# 3. Menggunakan efek CMatrix untuk Windows:
# import threading
# stop_event = threading.Event()
# matrix_thread = threading.Thread(target=cmatrix_windows_effect, args=(stop_event, 80, 24, 0.04))
# matrix_thread.start()
# # ... (jalankan proses lain)
# stop_event.set()
# matrix_thread.join()
