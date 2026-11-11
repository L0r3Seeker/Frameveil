STYLE = """
* { font-family: 'Microsoft YaHei UI', 'Segoe UI'; font-size: 13px; color: #e9eaf1; }
QMainWindow, QDialog { background: #101116; }
QWidget#root { background: #101116; }
QFrame#panel { background: #181a22; border: 1px solid #292c38; border-radius: 16px; }
QFrame#header { background: transparent; border-bottom: 1px solid #262934; }
QLabel { background: transparent; border: none; }
QLabel#brand { font-size: 24px; font-weight: 700; letter-spacing: 2px; }
QLabel#muted { color: #8e94a8; font-size: 12px; }
QLabel#section { color: #a5abc0; font-size: 11px; font-weight: 600; letter-spacing: 2px; }
QLabel#title { font-size: 21px; font-weight: 600; }
QLabel#badge { color: #a69bff; background: #28243d; padding: 5px 10px; border-radius: 8px; font-size: 11px; }
QLabel#status { color: #9fa8c0; background: #202430; border: 1px solid #33394a; padding: 7px 13px; border-radius: 12px; }
QPushButton { background: #242733; border: 1px solid #333849; border-radius: 9px; padding: 9px 13px; font-weight: 500; }
QPushButton:hover { background: #303546; border-color: #616884; }
QPushButton:pressed { background: #383e52; }
QPushButton:disabled { color: #5e6578; background: #1c1f29; border-color: #272b36; }
QPushButton#primary { color: #101b18; background: #a5f3cf; border: none; font-size: 14px; font-weight: 700; padding: 14px; }
QPushButton#primary:hover { background: #c5ffe5; }
QPushButton#danger { color: #ffb7c4; background: #382330; border-color: #684051; }
QPushButton#quiet { background: transparent; border-color: #303543; color: #b7bdd0; }
QPushButton:checked { background: #393153; border-color: #9d8de8; color: #e0d7ff; }
QComboBox, QDoubleSpinBox, QSpinBox { background: #11141c; border: 1px solid #33394a; border-radius: 7px; padding: 7px 9px; min-height: 20px; selection-background-color: #514b76; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView { background: #202430; border: 1px solid #434960; selection-background-color: #3c3657; padding: 5px; }
QCheckBox { spacing: 9px; color: #b8bfd1; padding: 5px 0px; }
QCheckBox::indicator { width: 17px; height: 17px; border: 1px solid #515970; border-radius: 5px; background: #151923; }
QCheckBox::indicator:checked { background: #a5f3cf; border-color: #a5f3cf; image: url(CHECK_PATH); }
QListWidget { background: transparent; border: none; outline: 0; padding: 1px; }
QListWidget::item { border: 1px solid transparent; border-radius: 10px; margin: 4px 0; padding: 9px 7px; color: #b8c0d4; }
QListWidget::item:selected { background: #2c2941; border: 1px solid #62588d; color: #eeeaff; }
QListWidget::item:hover { background: #222634; }
QSlider::groove:horizontal { height: 4px; background: #343a4c; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #ae9df8; border-radius: 2px; }
QSlider::handle:horizontal { background: #e3daff; border: 3px solid #6c608e; width: 10px; margin: -5px 0; border-radius: 7px; }
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: transparent; width: 6px; margin: 3px; }
QScrollBar::handle:vertical { background: #42485c; border-radius: 3px; min-height: 25px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { color: #e5e7f2; background: #292d3b; border: 1px solid #555c71; padding: 6px; }
QMessageBox { background: #181a22; }
"""
