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
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFont, QCursor, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView

# --- إعدادات المسارات الأساسية ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GAMES_DIR = os.path.join(BASE_DIR, "Games")
ASSETS_DIR = os.path.join(BASE_DIR, "src", "assets")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
APP_ICON_PATH = os.path.join(IMAGES_DIR, "app-icon.png")

# --- ملف التصميم QSS (Premium Dark Theme) ---
STYLESHEET = """
QMainWindow, QDialog {
    background-color: #0d0d12;
}
QLabel {
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QPushButton {
    background-color: #6200ea;
    color: white;
    border: none;
    padding: 10px 18px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: bold;
    font-family: 'Segoe UI', Arial;
}
QPushButton:hover {
    background-color: #7b1fa2;
}
QPushButton:pressed {
    background-color: #4a00b0;
}
QLineEdit {
    background-color: #1a1a24;
    border: 1px solid #333344;
    border-radius: 8px;
    padding: 12px;
    color: white;
    font-size: 14px;
}
QLineEdit:focus {
    border: 1px solid #6200ea;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}
QTabWidget::pane {
    border: 1px solid #2a2a35;
    border-radius: 8px;
    background: #15151e;
    margin-top: -1px;
}
QTabBar::tab {
    background: #1a1a24;
    color: #888;
    padding: 12px 25px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
    font-size: 14px;
}
QTabBar::tab:selected {
    background: #6200ea;
    color: white;
}
/* ستايل بطاقة اللعبة */
QWidget#GameCard {
    background-color: #15151e;
    border-radius: 12px;
    border: 1px solid #2a2a35;
}
QWidget#GameCard:hover {
    background-color: #1c1c28;
    border: 1px solid #6200ea;
}
"""

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("حول Dz game")
        self.setFixedSize(450, 300)
        self.setStyleSheet(STYLESHEET)
        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        # اللوجو والاسم
        title = QLabel("Dz game")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #6200ea;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dev_label = QLabel("المطور: Moussa")
        dev_label.setStyleSheet("font-size: 18px; color: #aaaaaa;")
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # روابط التواصل الاجتماعية
        telegram = QLabel('<a href="https://t.me/MoussaCHRF07" style="color: #0088cc; text-decoration: none; font-size: 16px;">💬 Telegram: @MoussaCHRF07</a>')
        telegram.setOpenExternalLinks(True)
        telegram.setAlignment(Qt.AlignmentFlag.AlignCenter)

        facebook = QLabel('<a href="https://www.facebook.com/share/14k6Lz96gTN/" style="color: #1877f2; text-decoration: none; font-size: 16px;">📘 Facebook Profile</a>')
        facebook.setOpenExternalLinks(True)
        facebook.setAlignment(Qt.AlignmentFlag.AlignCenter)

        discord = QLabel('🎮 Discord: <span style="color: #5865F2; font-size: 16px;">moussadz4458</span>')
        discord.setStyleSheet("font-size: 16px;")
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
        self.setMinimumSize(1024, 768) # نافذة واسعة وقابلة للتمديد
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
        
        # --- تاب إضافة HTML ---
        self.html_tab = QWidget()
        html_layout = QVBoxLayout(self.html_tab)
        html_layout.setSpacing(15)
        
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
        self.btn_submit_html.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg")))
        self.btn_submit_html.clicked.connect(self.add_html_game)
        
        html_layout.addWidget(QLabel("اسم اللعبة:"))
        html_layout.addWidget(self.html_name)
        html_layout.addWidget(self.btn_html_file)
        html_layout.addWidget(self.lbl_html_path)
        html_layout.addWidget(self.btn_html_cover)
        html_layout.addWidget(self.lbl_html_cover)
        html_layout.addStretch()
        html_layout.addWidget(self.btn_submit_html)
        
        # --- تاب إضافة ZIP/RAR ---
        self.zip_tab = QWidget()
        zip_layout = QVBoxLayout(self.zip_tab)
        zip_layout.setSpacing(15)
        
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
        self.btn_submit_zip.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg")))
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

        self.selected_html = ""
        self.selected_html_cover = ""
        self.selected_zip = ""
        self.selected_zip_cover = ""

    def select_html(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختر ملف HTML", "", "HTML Files (*.html)")
        if path:
            self.selected_html = path
            self.lbl_html_path.setText(os.path.basename(path))

    def select_cover_html(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختر صورة الغلاف", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.selected_html_cover = path
            self.lbl_html_cover.setText(os.path.basename(path))

    def select_zip(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختر ملف مضغوط", "", "Archives (*.zip *.rar)")
        if path:
            self.selected_zip = path
            self.lbl_zip_path.setText(os.path.basename(path))

    def select_cover_zip(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختر صورة الغلاف", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.selected_zip_cover = path
            self.lbl_zip_cover.setText(os.path.basename(path))

    def add_html_game(self):
        name = self.html_name.text().strip()
        if not name or not self.selected_html:
            QMessageBox.warning(self, "تنبيه", "يجب كتابة اسم اللعبة واختيار ملف HTML.")
            return
            
        game_id = str(uuid.uuid4())
        game_folder = os.path.join(GAMES_DIR, game_id)
        os.makedirs(game_folder, exist_ok=True)
        
        dest_html = os.path.join(game_folder, os.path.basename(self.selected_html))
        shutil.copy(self.selected_html, dest_html)
        
        cover_name = ""
        if self.selected_html_cover:
            cover_name = "cover" + os.path.splitext(self.selected_html_cover)[1]
            shutil.copy(self.selected_html_cover, os.path.join(game_folder, cover_name))
            
        self.save_meta(game_folder, name, os.path.basename(dest_html), cover_name)
        self.accept()

    def add_zip_game(self):
        name = self.zip_name.text().strip()
        if not name or not self.selected_zip:
            QMessageBox.warning(self, "تنبيه", "يجب كتابة اسم اللعبة واختيار الملف المضغوط.")
            return
            
        game_id = str(uuid.uuid4())
        game_folder = os.path.join(GAMES_DIR, game_id)
        os.makedirs(game_folder, exist_ok=True)
        
        try:
            if self.selected_zip.endswith('.zip'):
                with zipfile.ZipFile(self.selected_zip, 'r') as zip_ref:
                    zip_ref.extractall(game_folder)
            elif self.selected_zip.endswith('.rar'):
                if rarfile is None:
                    raise Exception("مكتبة rarfile غير متوفرة. الرجاء تثبيتها لتشغيل ملفات RAR.")
                with rarfile.RarFile(self.selected_zip, 'r') as rar_ref:
                    rar_ref.extractall(game_folder)
        except Exception as e:
            QMessageBox.critical(self, "خطأ في فك الضغط", f"حدث خطأ أثناء فك الضغط:\n{str(e)}")
            shutil.rmtree(game_folder)
            return

        entry_html = "index.html"
        html_files = [f for f in os.listdir(game_folder) if f.endswith('.html')]
        if html_files:
            entry_html = "index.html" if "index.html" in html_files else html_files[0]
            
        cover_name = ""
        if self.selected_zip_cover:
            cover_name = "cover" + os.path.splitext(self.selected_zip_cover)[1]
            shutil.copy(self.selected_zip_cover, os.path.join(game_folder, cover_name))
            
        self.save_meta(game_folder, name, entry_html, cover_name)
        self.accept()

    def save_meta(self, folder, title, entry, cover):
        metadata = {"title": title, "entryHtml": entry, "image": cover}
        with open(os.path.join(folder, "metadata.json"), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)

class DzGameLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dz game")
        self.setMinimumSize(1100, 750)
        self.setStyleSheet(STYLESHEET)
        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))
            
        os.makedirs(GAMES_DIR, exist_ok=True)
        self.init_ui()
        self.load_library()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # --- الهيدر (الشريط العلوي) ---
        header_layout = QHBoxLayout()
        
        # اللوجو والاسم
        logo_label = QLabel("Dz game")
        logo_label.setStyleSheet("font-size: 30px; font-weight: 900; color: #ffffff; letter-spacing: 1px;")
        
        # أزرار الهيدر
        self.btn_add = QPushButton(" إضافة لعبة")
        self.btn_add.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg")))
        self.btn_add.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add.setFixedSize(140, 45)
        self.btn_add.clicked.connect(self.open_add_dialog)
        
        self.btn_refresh = QPushButton()
        self.btn_refresh.setIcon(QIcon(os.path.join(ICONS_DIR, "refresh.svg")))
        self.btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_refresh.setFixedSize(45, 45)
        self.btn_refresh.setStyleSheet("background-color: #1a1a24; border: 1px solid #333344;")
        self.btn_refresh.clicked.connect(self.load_library)

        self.btn_about = QPushButton(" المطور")
        self.btn_about.setIcon(QIcon(os.path.join(ICONS_DIR, "settings.svg")))
        self.btn_about.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_about.setFixedSize(120, 45)
        self.btn_about.setStyleSheet("background-color: #1a1a24; border: 1px solid #333344; color: white;")
        self.btn_about.clicked.connect(self.open_about_dialog)
        
        header_layout.addWidget(logo_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_refresh)
        header_layout.addWidget(self.btn_add)
        header_layout.addWidget(self.btn_about)
        main_layout.addLayout(header_layout)
        
        # --- شبكة الألعاب ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.setSpacing(25)
        self.scroll.setWidget(self.grid_widget)
        
        main_layout.addWidget(self.scroll)

    def load_library(self):
        # إزالة الويدجتس السابقة لتحديث القائمة
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                
        row, col = 0, 0
        max_cols = 4 # عدد الأعمدة الافتراضي

        if not os.path.exists(GAMES_DIR):
            return

        folders = os.listdir(GAMES_DIR)
        for folder_name in folders:
            folder_path = os.path.join(GAMES_DIR, folder_name)
            meta_path = os.path.join(folder_path, "metadata.json")
            
            if os.path.isdir(folder_path) and os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    
                card = self.create_game_card(folder_path, meta)
                self.grid_layout.addWidget(card, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

    def create_game_card(self, folder_path, meta):
        card = QWidget()
        card.setObjectName("GameCard")
        card.setFixedSize(240, 310)
        
        # إضافة تأثير الظل للبطاقة
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
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
            cover_lbl.setStyleSheet("background-color: #0d0d12; color: #555; border-radius: 8px; font-weight: bold;")
            
        title_lbl = QLabel(meta.get("title", "Unknown Game"))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        
        play_btn = QPushButton(" تشغيل اللعبة")
        play_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "play.svg")))
        play_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        play_btn.setStyleSheet("background-color: #03dac6; color: #000000; font-weight: bold; border-radius: 6px; padding: 8px;")
        
        html_path = os.path.join(folder_path, meta.get("entryHtml", "index.html"))
        play_btn.clicked.connect(lambda checked, t=meta.get("title"), p=html_path: self.launch_game(t, p))
        
        layout.addWidget(cover_lbl)
        layout.addWidget(title_lbl)
        layout.addStretch()
        layout.addWidget(play_btn)
        
        return card

    def open_add_dialog(self):
        dialog = AddGameDialog(self)
        if dialog.exec():
            self.load_library()

    def open_about_dialog(self):
        dialog = AboutDialog()
        dialog.exec()

    def launch_game(self, title, path):
        if not os.path.exists(path):
            QMessageBox.critical(self, "خطأ", "لم يتم العثور على ملف التشغيل (index.html). تأكد من سلامة ملفات اللعبة.")
            return
            
        self.player_window = GameWindow(title, path)
        self.player_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # لتوحيد المظهر على كل أنظمة التشغيل
    window = DzGameLauncher()
    window.show()
    sys.exit(app.exec())
