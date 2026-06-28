import sys
import os
import json
import shutil
import zipfile
import uuid
try:
    import rarfile
except ImportError:
    rarfile = None

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QScrollArea, QDialog, QLineEdit, QMessageBox, 
                             QTabWidget, QGridLayout, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon, QPixmap, QCursor, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView

# --- نظام المسارات لملف EXE واحد ---
def get_resource_path(relative_path):
    """جلب مسار الملفات (يعمل أثناء التطوير وبعد التحويل لـ EXE واحد)"""
    try:
        # PyInstaller يستخرج الملفات هنا مؤقتاً عند التشغيل
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_games_directory():
    """تحديد مسار مجلد الألعاب ليكون بجانب ملف الـ EXE وليس في المسار المؤقت"""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "Games")
    return os.path.join(os.path.abspath("."), "Games")

GAMES_DIR = get_games_directory()
ASSETS_DIR = get_resource_path(os.path.join("src", "assets"))
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
APP_ICON_PATH = os.path.join(IMAGES_DIR, "app-icon.png")

# --- التصميم (Premium Dark UI) ---
STYLESHEET = """
QMainWindow, QDialog, QWidget#CentralWidget { background-color: #0F0F15; }
QLabel { color: #FFFFFF; font-family: 'Segoe UI', Arial, sans-serif; }
QPushButton {
    background-color: #6200ea; color: white; border: none;
    padding: 10px 18px; border-radius: 8px; font-size: 14px; font-weight: bold;
}
QPushButton:hover { background-color: #7b1fa2; }
QPushButton:pressed { background-color: #4a00b0; }
QLineEdit {
    background-color: #1A1A24; border: 1px solid #333344;
    border-radius: 8px; padding: 12px; color: white; font-size: 14px;
}
QLineEdit:focus { border: 1px solid #6200ea; }
QScrollArea { border: none; background-color: transparent; }
QScrollArea > QWidget > QWidget { background-color: transparent; }
QTabWidget::pane { border: 1px solid #2a2a35; border-radius: 8px; background: #15151e; margin-top: -1px; }
QTabBar::tab { background: #1A1A24; color: #888; padding: 12px 25px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: bold; font-size: 14px; }
QTabBar::tab:selected { background: #6200ea; color: white; }
QWidget#GameCard { background-color: #15151E; border-radius: 12px; border: 1px solid #2A2A35; }
QWidget#GameCard:hover { background-color: #1C1C28; border: 1px solid #6200ea; }
"""

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("حول المطور")
        self.setFixedSize(450, 300)
        self.setStyleSheet(STYLESHEET)
        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        title = QLabel("Dz game")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #6200ea;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_label = QLabel("المطور: Moussa")
        dev_label.setStyleSheet("font-size: 18px; color: #aaaaaa;")
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        telegram = QLabel('<a href="https://t.me/MoussaCHRF07" style="color: #0088cc; text-decoration: none; font-size: 16px;">💬 Telegram: @MoussaCHRF07</a>')
        telegram.setOpenExternalLinks(True)
        telegram.setAlignment(Qt.AlignmentFlag.AlignCenter)
        facebook = QLabel('<a href="https://www.facebook.com/share/14k6Lz96gTN/" style="color: #1877f2; text-decoration: none; font-size: 16px;">📘 Facebook Profile</a>')
        facebook.setOpenExternalLinks(True)
        facebook.setAlignment(Qt.AlignmentFlag.AlignCenter)
        discord = QLabel('🎮 Discord: <span style="color: #5865F2; font-size: 16px;">moussadz4458</span>')
        discord.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(dev_label)
        layout.addSpacing(10)
        layout.addWidget(telegram)
        layout.addWidget(facebook)
        layout.addWidget(discord)

class GameWindow(QMainWindow):
    def __init__(self, title, html_path):
        super().__init__()
        self.setWindowTitle(f"Dz game - {title}")
        self.setMinimumSize(1024, 768)
        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))
            
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl.fromLocalFile(html_path))
        self.setCentralWidget(self.browser)

class AddGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة لعبة جديدة")
        self.setFixedSize(550, 450)
        self.setStyleSheet(STYLESHEET)
        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        # --- HTML Tab ---
        self.html_tab = QWidget()
        html_layout = QVBoxLayout(self.html_tab)
        self.html_name = QLineEdit()
        self.html_name.setPlaceholderText("أدخل اسم اللعبة هنا...")
        self.btn_html_file = QPushButton("تصفح ملف اللعبة (.html)")
        self.btn_html_file.setIcon(QIcon(os.path.join(ICONS_DIR, "folder.svg")))
        self.btn_html_file.clicked.connect(self.select_html)
        self.lbl_html_path = QLabel("لم يتم اختيار ملف")
        self.lbl_html_path.setStyleSheet("color: #888; font-size: 12px;")
        self.btn_html_cover = QPushButton("تصفح صورة الغلاف (اختياري)")
        self.btn_html_cover.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.svg")))
        self.btn_html_cover.clicked.connect(self.select_cover_html)
        self.lbl_html_cover = QLabel("لم يتم اختيار صورة")
        self.lbl_html_cover.setStyleSheet("color: #888; font-size: 12px;")
        self.btn_submit_html = QPushButton("حفظ وإضافة اللعبة")
        self.btn_submit_html.clicked.connect(self.add_html_game)
        
        html_layout.addWidget(QLabel("اسم اللعبة:"))
        html_layout.addWidget(self.html_name)
        html_layout.addWidget(self.btn_html_file)
        html_layout.addWidget(self.lbl_html_path)
        html_layout.addWidget(self.btn_html_cover)
        html_layout.addWidget(self.lbl_html_cover)
        html_layout.addStretch()
        html_layout.addWidget(self.btn_submit_html)
        
        # --- ZIP/RAR Tab ---
        self.zip_tab = QWidget()
        zip_layout = QVBoxLayout(self.zip_tab)
        self.zip_name = QLineEdit()
        self.zip_name.setPlaceholderText("أدخل اسم اللعبة هنا...")
        self.btn_zip_file = QPushButton("تصفح ملف مضغوط (.zip, .rar)")
        self.btn_zip_file.setIcon(QIcon(os.path.join(ICONS_DIR, "folder.svg")))
        self.btn_zip_file.clicked.connect(self.select_zip)
        self.lbl_zip_path = QLabel("لم يتم اختيار ملف")
        self.lbl_zip_path.setStyleSheet("color: #888; font-size: 12px;")
        self.btn_zip_cover = QPushButton("تصفح صورة الغلاف (اختياري)")
        self.btn_zip_cover.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.svg")))
        self.btn_zip_cover.clicked.connect(self.select_cover_zip)
        self.lbl_zip_cover = QLabel("لم يتم اختيار صورة")
        self.lbl_zip_cover.setStyleSheet("color: #888; font-size: 12px;")
        self.btn_submit_zip = QPushButton("فك الضغط وإضافة اللعبة")
        self.btn_submit_zip.clicked.connect(self.add_zip_game)
        
        zip_layout.addWidget(QLabel("اسم اللعبة:"))
        zip_layout.addWidget(self.zip_name)
        zip_layout.addWidget(self.btn_zip_file)
        zip_layout.addWidget(self.lbl_zip_path)
        zip_layout.addWidget(self.btn_zip_cover)
        zip_layout.addWidget(self.lbl_zip_cover)
        zip_layout.addStretch()
        zip_layout.addWidget(self.btn_submit_zip)
        
        self.tabs.addTab(self.html_tab, "لعبة HTML مفردة")
        self.tabs.addTab(self.zip_tab, "لعبة مضغوطة (ZIP/RAR)")
        self.layout.addWidget(self.tabs)

        self.selected_html, self.selected_html_cover = "", ""
        self.selected_zip, self.selected_zip_cover = "", ""

    def select_html(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختر ملف HTML", "", "HTML Files (*.html)")
        if path:
            self.selected_html = path
            self.lbl_html_path.setText(os.path.basename(path))

    def select_cover_html(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختر صورة", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.selected_html_cover = path
            self.lbl_html_cover.setText(os.path.basename(path))

    def select_zip(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختر ملف مضغوط", "", "Archives (*.zip *.rar)")
        if path:
            self.selected_zip = path
            self.lbl_zip_path.setText(os.path.basename(path))

    def select_cover_zip(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختر صورة", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.selected_zip_cover = path
            self.lbl_zip_cover.setText(os.path.basename(path))

    def add_html_game(self):
        name = self.html_name.text().strip()
        if not name or not self.selected_html: return QMessageBox.warning(self, "تنبيه", "أكمل البيانات.")
        self.process_game(name, self.selected_html, self.selected_html_cover, is_zip=False)

    def add_zip_game(self):
        name = self.zip_name.text().strip()
        if not name or not self.selected_zip: return QMessageBox.warning(self, "تنبيه", "أكمل البيانات.")
        self.process_game(name, self.selected_zip, self.selected_zip_cover, is_zip=True)

    def process_game(self, name, source_file, cover_file, is_zip):
        game_folder = os.path.join(GAMES_DIR, str(uuid.uuid4()))
        os.makedirs(game_folder, exist_ok=True)
        try:
            if is_zip:
                if source_file.endswith('.zip'):
                    with zipfile.ZipFile(source_file, 'r') as z: z.extractall(game_folder)
                elif source_file.endswith('.rar'):
                    if rarfile:
                        with rarfile.RarFile(source_file, 'r') as r: r.extractall(game_folder)
                    else: raise Exception("مكتبة rarfile غير مفعلة.")
                files = [f for f in os.listdir(game_folder) if f.endswith('.html')]
                entry = "index.html" if "index.html" in files else (files[0] if files else "index.html")
            else:
                entry = os.path.basename(source_file)
                shutil.copy(source_file, os.path.join(game_folder, entry))

            cover_name = ""
            if cover_file:
                cover_name = "cover" + os.path.splitext(cover_file)[1]
                shutil.copy(cover_file, os.path.join(game_folder, cover_name))
                
            with open(os.path.join(game_folder, "metadata.json"), 'w', encoding='utf-8') as f:
                json.dump({"title": name, "entryHtml": entry, "image": cover_name}, f, ensure_ascii=False)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
            shutil.rmtree(game_folder)

class DzGameLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dz game")
        self.setMinimumSize(1100, 750)
        self.setStyleSheet(STYLESHEET)
        
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))
            
        os.makedirs(GAMES_DIR, exist_ok=True)
        self.init_ui(central)
        self.load_library()

    def init_ui(self, central):
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)

        header_layout = QHBoxLayout()
        logo_label = QLabel("Dz game")
        logo_label.setStyleSheet("font-size: 30px; font-weight: 900; color: #ffffff;")
        
        self.btn_add = QPushButton(" إضافة لعبة")
        self.btn_add.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg")))
        self.btn_add.clicked.connect(self.open_add_dialog)
        
        self.btn_refresh = QPushButton()
        self.btn_refresh.setIcon(QIcon(os.path.join(ICONS_DIR, "refresh.svg")))
        self.btn_refresh.setFixedSize(40, 40)
        self.btn_refresh.setStyleSheet("background-color: #1a1a24; border: 1px solid #333344;")
        self.btn_refresh.clicked.connect(self.load_library)

        self.btn_about = QPushButton(" المطور")
        self.btn_about.setIcon(QIcon(os.path.join(ICONS_DIR, "settings.svg")))
        self.btn_about.setStyleSheet("background-color: #1a1a24; border: 1px solid #333344;")
        self.btn_about.clicked.connect(lambda: AboutDialog().exec())
        
        header_layout.addWidget(logo_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_refresh)
        header_layout.addWidget(self.btn_add)
        header_layout.addWidget(self.btn_about)
        main_layout.addLayout(header_layout)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.setSpacing(25)
        self.scroll.setWidget(self.grid_widget)
        main_layout.addWidget(self.scroll)

    def load_library(self):
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget: widget.setParent(None)
                
        row, col = 0, 0
        if not os.path.exists(GAMES_DIR): return

        for folder_name in os.listdir(GAMES_DIR):
            folder_path = os.path.join(GAMES_DIR, folder_name)
            meta_path = os.path.join(folder_path, "metadata.json")
            if os.path.isdir(folder_path) and os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                card = self.create_game_card(folder_path, meta)
                self.grid_layout.addWidget(card, row, col)
                col += 1
                if col >= 4:
                    col, row = 0, row + 1

    def create_game_card(self, folder_path, meta):
        card = QWidget()
        card.setObjectName("GameCard")
        card.setFixedSize(240, 310)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        cover_lbl = QLabel()
        cover_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover_lbl.setFixedSize(210, 190)
        cover_lbl.setStyleSheet("background-color: #0d0d12; border-radius: 8px;")
        
        cover_path = os.path.join(folder_path, meta.get("image", ""))
        if meta.get("image") and os.path.exists(cover_path):
            pix = QPixmap(cover_path).scaled(210, 190, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            cover_lbl.setPixmap(pix)
        else:
            cover_lbl.setText("بدون غلاف")
            
        title_lbl = QLabel(meta.get("title", "Unknown"))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        play_btn = QPushButton(" تشغيل اللعبة")
        play_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "play.svg")))
        play_btn.setStyleSheet("background-color: #03dac6; color: #000; font-weight: bold;")
        
        html_path = os.path.join(folder_path, meta.get("entryHtml", "index.html"))
        play_btn.clicked.connect(lambda checked, t=meta.get("title"), p=html_path: self.launch_game(t, p))
        
        layout.addWidget(cover_lbl)
        layout.addWidget(title_lbl)
        layout.addStretch()
        layout.addWidget(play_btn)
        return card

    def open_add_dialog(self):
        if AddGameDialog(self).exec(): self.load_library()

    def launch_game(self, title, path):
        if not os.path.exists(path): return QMessageBox.critical(self, "خطأ", "لم يتم العثور على ملف التشغيل.")
        self.player_window = GameWindow(title, path)
        self.player_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DzGameLauncher()
    window.show()
    sys.exit(app.exec())
