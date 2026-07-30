# -*- coding: utf-8 -*-
import sys
import socket
import os
import subprocess
import winsound
import ctypes
import ctypes.wintypes
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMenu, QAction, QVBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer, QRect, QRectF
from PyQt5.QtGui import QPixmap, QCursor, QPainter, QPainterPath, QColor, QPen
from log_monitor import LogMonitorThread

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ==========================================
# 闂佸憡鏌ｉ崝搴ㄥ极妤ｅ啯鐓€鐎广儱娲ㄩ弸?(闁荤姴娲弨閬嶆偋閹绢喖绠叉い鏃囧亹閺変粙姊婚崟顐ｅ櫣闁搞劌绻樺畷鍫曟倷椤掆偓閸撲即鏌涢幇顒€鎮侀柟渚垮姂瀵?
# ==========================================
SPRITE_CONFIG = {
    "idle": {
        "dir": resource_path(r"assets\idle_frames"),
        "fps": 10
    },
    "working": {
        "dir": resource_path(r"assets\working_frames"),
        "fps": 10
    },
    "handing_file": {
        "dir": resource_path(r"assets\handing_file_frames"),
        "fps": 10
    },
    "spank_ready": {
        "path": resource_path(r"assets\spanking_frames\1.png"),
        "cols": 1, "rows": 1, "fps": 10
    },
    "spanking": {
        "dir": resource_path(r"assets\spanking_frames"),
        "fps": 15
    }
}

class Bubble(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 25) # Bottom margin for tail
        
        self.label = QLabel("", self)
        self.label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: black;
                font-family: "Microsoft YaHei";
                font-size: 14px;
            }
        """)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        w = rect.width()
        h = rect.height()
        tail_height = 15
        tail_width = 15
        radius = 10
        
        path = QPainterPath()
        bubble_rect = QRectF(1, 1, w - 2, h - tail_height - 1)
        path.addRoundedRect(bubble_rect, radius, radius)
        
        tail_path = QPainterPath()
        tail_x = w / 2
        tail_path.moveTo(tail_x - tail_width/2, h - tail_height - 1)
        tail_path.lineTo(tail_x, h - 1)
        tail_path.lineTo(tail_x + tail_width/2, h - tail_height - 1)
        
        path = path.united(tail_path)
        
        painter.setPen(QPen(QColor("#cccccc"), 2))
        painter.setBrush(QColor("white"))
        painter.drawPath(path)
        
    def show_message(self, text, pos_x, pos_y):
        self.label.setText(text)
        self.label.adjustSize()
        self.adjustSize()
        # Position slightly above the pet
        self.move(pos_x, pos_y - self.height() - 10)
        self.show()

class Pet(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        self.frames = {}
        self.load_sprites()
        
        self.current_state = "idle"
        self.current_frame = 0
        
        # 闂佸憡鏌ｉ崝搴ㄥ极閸撗勫闁斥晛鍟ˇ褔鏌?        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_frame)

        self.proximity_timer = QTimer(self)
        self.proximity_timer.timeout.connect(self.check_mouse_proximity)
        
        # 濠殿喗蓱濮婂綊宕?
        self.bubble = Bubble()
        
        # 婵炲瓨鍤庨崐鎾惰姳娴煎瓨鍋愰柤鍝ヮ暯閸?        
        self.dragging = False
        self.offset = QPoint()
        self.is_spank_mode = False
        self.is_spanking_playing = False
        self.mouse_in_proximity = False
        self.is_handing_file_paused = False
        self.mouse_whip_process = None
        
        # 闂佸搫鍟ㄩ崕杈╂崲閺冨牊鍎庨柟瀵稿仜娴?
        self.monitor = LogMonitorThread()
        self.monitor.state_changed.connect(self.on_state_changed)
        self.monitor.start()
        
        self.set_state("idle")

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.label = QLabel(self)
        self.setMouseTracking(True)
        self.label.setMouseTracking(True)
        
        screen = QApplication.primaryScreen().geometry()
        self.move(100, screen.height() - 400)

    def load_sprites(self):
        """"""
        for state, config in SPRITE_CONFIG.items():
            frame_list = []
            
            if "dir" in config:
                dir_path = config["dir"]
                if not os.path.exists(dir_path):
                    print(f"目录不存在: {dir_path}")
                    self.frames[state] = []
                    continue
                
                files = [f for f in os.listdir(dir_path) if f.lower().endswith('.png')]
                files.sort(key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else x)
                
                for f in files:
                    frame = QPixmap(os.path.join(dir_path, f))
                    if state == "working":
                        frame = frame.scaledToHeight(280, Qt.SmoothTransformation)
                    else:
                        frame = frame.scaledToHeight(380, Qt.SmoothTransformation)
                    frame_list.append(frame)
            else:
                path = config["path"]
                if not os.path.exists(path):
                    print(f"图片不存在: {path}")
                    self.frames[state] = []
                    continue
                    
                sheet = QPixmap(path)
                frame_w = sheet.width() // config["cols"]
                frame_h = sheet.height() // config["rows"]
                
                for row in range(config["rows"]):
                    for col in range(config["cols"]):
                        rect = QRect(col * frame_w, row * frame_h, frame_w, frame_h)
                        frame = sheet.copy(rect)
                    if state == "working":
                        frame = frame.scaledToHeight(280, Qt.SmoothTransformation)
                    else:
                        frame = frame.scaledToHeight(380, Qt.SmoothTransformation) # 婵烇絽娲︾换鍐偓鍨⒐缁傚秹鎼归悷鎵虫寘濠殿噯绲鹃弻褏娆?
                        frame_list.append(frame)
                        
            self.frames[state] = frame_list

    def set_state(self, state):
        if state not in self.frames or not self.frames[state]:
            return
            
        if self.current_state == state and state != "idle":
            return
            
        self.current_state = state
        self.current_frame = 0
        self.is_handing_file_paused = False
        self.bubble.hide()
        
        if state == "idle":
            self.bubble.show_message("老板好！", self.x(), self.y())
        elif state == "spanking":
            self.bubble.show_message("别打啦！", self.x(), self.y())
        elif state == "working":
            self.bubble.show_message("叶总，文件马上就好", self.x(), self.y())
        elif state == "handing_file":
            self.bubble.show_message("叶总，文件请过目一下", self.x(), self.y())
        fps = SPRITE_CONFIG[state]["fps"]
        interval = 1000 // fps
        
        self.anim_timer.start(interval)
        self.update_image()

    def update_frame(self):
        frames = self.frames.get(self.current_state, [])
        if not frames:
            return
            
        self.current_frame += 1
        
        # 濠㈣泛瀚幃濠囨偋鐟欏嫮鏆曢柣妯垮煐閳ь兛鑳剁划銊╁级閻斿皷鍋撻弰蹇曞竼
        if self.current_frame >= len(frames):
            if self.current_state == "handing_file":
                self.current_frame = len(frames) - 1
                self.anim_timer.stop()
                self.is_handing_file_paused = True
                self.bubble.show_message("叶总，文件请过目一下", self.x(), self.y())
                return
            elif self.current_state == "spanking":
                self.is_spanking_playing = False
                self.set_state("spank_ready")
                return
            elif self.current_state == "idle":
                self.current_frame = len(frames) - 1
                self.anim_timer.stop() # 闂佺顑嗙划灞斤耿椤忓牆瀚夐柍褜鍓熷畷銉︽償濠靛牜浼囬柣?                return
            else:
                self.current_frame = 0 # 閻庣敻鍋婃禍鐐虹嵁閸℃稑绠绘い鎾跺枑閺?
                
        self.update_image()

    def update_image(self):
        frames = self.frames.get(self.current_state, [])
        if frames and self.current_frame < len(frames):
            pixmap = frames[self.current_frame]
            self.label.setPixmap(pixmap)
            self.label.resize(pixmap.size())
            self.resize(pixmap.size())

    def on_state_changed(self, log_state):
        if self.is_spank_mode:
            return
        if log_state == "handing_file" and not getattr(self, 'is_handing_file_paused', False):
            self.set_state("handing_file")
        elif log_state == "working":
            self.set_state("working")

    def enterEvent(self, event):
        if not self.is_spank_mode and self.current_state == "idle":
            # 鼠标移入时重新播放待机动画
            self.current_frame = 0
            self.anim_timer.start(1000 // SPRITE_CONFIG["idle"]["fps"])
        super().enterEvent(event)
            
    def check_mouse_proximity(self):
        if not getattr(self, "is_spank_mode", False):
            return
            
        cursor_pos = QCursor.pos()
        pet_rect = self.geometry()
        trigger_distance = 250
        expanded_rect = pet_rect.adjusted(-trigger_distance, -trigger_distance, trigger_distance, trigger_distance)
        
        is_in_proximity = expanded_rect.contains(cursor_pos)
        
        if is_in_proximity and not self.mouse_in_proximity:
            if not getattr(self, "is_spanking_playing", False):
                self.is_spanking_playing = True
                self.set_state("spank_ready")
                QTimer.singleShot(133, self.start_spanking_animation)
                
        self.mouse_in_proximity = is_in_proximity

    def start_spanking_animation(self):
        if self.is_spank_mode and getattr(self, "is_spanking_playing", False):
            self.set_state("spanking")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if getattr(self, "is_handing_file_paused", False):
                self.bubble.hide()
                self.set_state("idle")
                self.activate_antigravity()
            else:
                self.dragging = True
                self.offset = event.globalPos() - self.pos()
            event.accept()
        elif event.button() == Qt.RightButton:
            if getattr(self, "is_spank_mode", False):
                self.disable_spank_mode()
            else:
                self.contextMenuEvent(event)
            event.accept()

    def activate_antigravity(self):
        import webbrowser
        try:
            webbrowser.open("antigravity://")
        except Exception as e:
            print(f"Failed to open antigravity: {e}")
            
    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)
            if not self.bubble.isHidden():
                self.bubble.move(self.x(), self.y() - self.bubble.height() - 10)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        if not self.is_spank_mode:
            spank_action = QAction("抽打老板模式(开启后右键可关闭)", self)
            spank_action.triggered.connect(self.enable_spank_mode)
            menu.addAction(spank_action)
        else:
            idle_action = QAction("停止抽打，恢复待机", self)
            idle_action.triggered.connect(self.disable_spank_mode)
            menu.addAction(idle_action)
            
        menu.addSeparator()
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)
        
        menu.exec_(QCursor.pos())

    def enable_spank_mode(self):
        self.is_spank_mode = True
        self.is_spanking_playing = False
        self.mouse_in_proximity = False
        self.set_state("spank_ready")
        self.proximity_timer.start(50) 
        try:
            whip_path = resource_path("MouseWhip.exe")
            
            if os.path.exists(whip_path):
                self.mouse_whip_process = subprocess.Popen(whip_path)
            else:
                print("MouseWhip.exe not found at:", whip_path)
        except Exception as e:
            print("Failed to start MouseWhip:", e)
        
    def disable_spank_mode(self):
        self.is_spank_mode = False
        self.is_spanking_playing = False
        self.proximity_timer.stop()
        self.set_state("idle")
        
        if self.mouse_whip_process:
            try:
                self.mouse_whip_process.kill()
            except Exception:
                pass
            self.mouse_whip_process = None
        
        # Async taskkill as fallback to avoid blocking the UI thread
        subprocess.Popen("taskkill /f /im MouseWhip.exe >nul 2>&1", shell=True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet = Pet()
    pet.show()
    sys.exit(app.exec_())
