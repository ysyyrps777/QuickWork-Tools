import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QTimeEdit, QDialog, QShortcut, QLabel, QSpacerItem, QSizePolicy, QDesktopWidget,
    QSystemTrayIcon, QMenu
)
from PyQt5.QtCore import Qt, QTimer, QTime, QPoint, QDate, QRect
from PyQt5.QtNetwork import QLocalSocket, QLocalServer  
from PyQt5.QtGui import QFont, QPalette, QKeySequence, QIcon

os.environ["LIBPNG_WARNINGS"] = "0"

TASKS_FILE = "tasks.json"

class TaskItem(QListWidgetItem):
    def __init__(self, time_str, text):
        super().__init__(f"{time_str}  {text}")
        self.time_str = time_str
        self.text = text
        self.notified = False

class CustomMessageBox(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(message)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel(message)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("""
        color: #1565C0;
        font-size: 22px;
        font-weight: bold;
        font-family: 'Microsoft YaHei';
        qproperty-alignment: AlignCenter;
        padding: 8px 16px;
        border-radius: 8px;
        background-color: rgba(230, 242, 255, 0.8);
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.25);
    """)

        ok_button = QPushButton("确定")
        ok_button.setFixedSize(250, 40)
        ok_button.clicked.connect(self.accept)
        ok_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4FC3F7, stop:1 #29B6F6);
                border: none;
                border-radius: 15px;
                color: white;
                font-size: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #81D4FA, stop:1 #4FC3F7);
            }
        """)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E1F5FE, stop:1 #B3E5FC);
                border-radius: 10px;
                border: 1px solid #4FC3F7;
            }
        """)
        
        self.center_on_screen()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

class ToDoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ToDo List")
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)
        self.resize(500, 750)
        self.setFont(QFont("微软雅黑", 12))

        try:
            self.setWindowIcon(QIcon("icon.png"))
        except:
            pass

        self.oldPos = self.pos()
        self.dragging = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        clock_layout = QHBoxLayout()
        clock_label = QLabel(self)
        clock_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 36px;
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            padding: 15px;
            qproperty-alignment: AlignCenter;
        """)
        clock_layout.addWidget(clock_label)
        self.update_clock()
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        input_layout = QHBoxLayout()
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setStyleSheet("""
            font-size: 18px;
            color: #333333;
            background: rgba(255, 255, 255, 0.6);
        """)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入任务内容")
        self.input_field.setStyleSheet("""
            font-size: 18px;
            color: #333333;
            background: rgba(255, 255, 255, 0.6);
        """)
        self.add_btn = QPushButton("添加")
        self.add_btn.setFixedSize(100, 50)
        self.add_btn.clicked.connect(self.add_task)
        input_layout.addWidget(self.time_edit)
        input_layout.addWidget(self.input_field, 1)
        input_layout.addWidget(self.add_btn)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            background: transparent;
            border: none;
            color: #FFFFFF;
            padding: 10px;
        """)
        self.list_widget.setSpacing(1)
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.model().rowsMoved.connect(self.save_tasks)

        self.clear_btn = QPushButton("🗑 删除选中")
        self.clear_btn.clicked.connect(self.remove_selected)

        self.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.5);
                border-radius: 20px;
                border: 1px solid #666;
            }
            QTimeEdit, QLineEdit {
                background: rgba(255, 255, 255, 0.3);
                border: 1px solid #888;
                border-radius: 15px;
                padding: 8px;
                color: #FFFFFF;
                font-size: 16px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4CAF50, stop:1 #45A049);
                border: none;
                border-radius: 15px;
                color: white;
                padding: 8px 15px;
                font-size: 18px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #66BB6A, stop:1 #4CAF50);
            }
            QListWidget::item {
                background: rgba(255, 69, 0, 0.3);
                border-radius: 15px;
                margin: 2px 0;
                padding: 10px;
                border: 1px solid #888;
                color: #FFFFFF;
                font-size: 16px;
            }
            QListWidget::item:selected {
                background: rgba(255, 69, 0, 0.5);
            }
        """)

        layout.addLayout(clock_layout)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addLayout(input_layout)
        layout.addWidget(self.list_widget, 1)
        layout.addWidget(self.clear_btn)
        self.setLayout(layout)

        self.setMouseTracking(True)

        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.add_task)
        QShortcut(QKeySequence("Ctrl+Del"), self).activated.connect(self.remove_selected)

        self.load_tasks()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(1000)

        self.move_to_top_right()

        try:
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon("icon.png"))
            tray_menu = QMenu()
            show_action = tray_menu.addAction("显示")
            show_action.triggered.connect(self.show)
            quit_action = tray_menu.addAction("退出")
            quit_action.triggered.connect(app.quit)
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
        except:
            pass

    def move_to_top_right(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        window_width = self.width()
        window_height = self.height()
        margin = 10
        x = screen_width - window_width - margin
        y = margin
        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.pos() + delta)
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def update_clock(self):
        current_time = QTime.currentTime().toString("hh:mm:ss")
        current_date = QDate.currentDate().toString("MM/dd")
        weekday = datetime.now().strftime("%A")
        weekday_cn = {
            "Monday": "星期一",
            "Tuesday": "星期二",
            "Wednesday": "星期三",
            "Thursday": "星期四",
            "Friday": "星期五",
            "Saturday": "星期六",
            "Sunday": "星期日"
        }
        clock_text = f"{current_time}\n{current_date} {weekday_cn[weekday]}"
        self.findChild(QLabel).setText(clock_text)

    def add_task(self):
        time_str = self.time_edit.time().toString("HH:mm")
        text = self.input_field.text().strip()
        if not text:
            return
        item = TaskItem(time_str, text)
        self.list_widget.addItem(item)
        self.input_field.clear()
        self.save_tasks()

    def remove_selected(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))
        self.save_tasks()

    def check_reminders(self):
        now = QTime.currentTime().toString("HH:mm")
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if isinstance(item, TaskItem):
                if item.time_str == now and not item.notified:
                    dialog = CustomMessageBox(item.text, self)
                    dialog.show()
                    dialog.exec_()
                    item.notified = True
                    self.save_tasks()

    def save_tasks(self):
        tasks = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if isinstance(item, TaskItem):
                tasks.append({"time": item.time_str, "text": item.text, "notified": item.notified})
        try:
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
        except:
            pass

    def load_tasks(self):
        if os.path.exists(TASKS_FILE):
            try:
                with open(TASKS_FILE, "r", encoding="utf-8") as f:
                    tasks = json.load(f)
                    for task in tasks:
                        item = TaskItem(task["time"], task["text"])
                        item.notified = task.get("notified", False)
                        self.list_widget.addItem(item)
            except:
                pass

class SingleInstanceApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.server_name = "ToDoList_SingleInstance"
        self.local_socket = QLocalSocket()
        self.local_socket.connectToServer(self.server_name)
        if self.local_socket.waitForConnected(500):
            self.is_running = True
            self.local_socket.write(b"show")
            self.local_socket.waitForBytesWritten()
            self.local_socket.disconnectFromServer()
        else:
            self.is_running = False
            self.local_server = QLocalServer()
            self.local_server.newConnection.connect(self.handle_message)
            self.local_server.listen(self.server_name)

    def handle_message(self):
        socket = self.local_server.nextPendingConnection()
        if socket.waitForReadyRead():
            data = socket.readAll().data()
            if data == b"show" and hasattr(self, 'window'):
                self.window.show()
                self.window.raise_()
                self.window.activateWindow()
        socket.disconnectFromServer()

if __name__ == "__main__":
    app = SingleInstanceApp(sys.argv)
    if app.is_running:
        sys.exit(0)
    window = ToDoApp()
    app.window = window
    window.show()
    sys.exit(app.exec_())