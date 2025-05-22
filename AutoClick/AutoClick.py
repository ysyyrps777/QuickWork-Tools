import sys
import time
import pyautogui
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox

class ClickerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('鼠标连点器')
        self.resize(530, 540)  # 增加窗口大小

        # 创建标签和输入框
        self.label_interval = QLabel('点击间隔（秒）：', self)
        self.entry_interval = QLineEdit(self)
        self.entry_interval.setText("0.1")  # 设置默认值为0.1秒
        self.entry_interval.setMinimumWidth(300)  # 设置输入框最小宽度

        self.label_duration = QLabel('连点持续时间（秒）：', self)
        self.entry_duration = QLineEdit(self)
        self.entry_duration.setText("5")  # 设置默认值为5秒
        self.entry_duration.setMinimumWidth(300)

        self.label_start_delay = QLabel('开始延迟（秒）：', self)
        self.entry_start_delay = QLineEdit(self)
        self.entry_start_delay.setText("3")  # 设置默认值为3秒
        self.entry_start_delay.setMinimumWidth(300)

        # 创建开始按钮
        self.start_button = QPushButton('开始连点', self)
        self.start_button.clicked.connect(self.start_clicking)
        self.start_button.setMinimumWidth(300)  # 设置按钮最小宽度

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.label_interval)
        layout.addWidget(self.entry_interval)
        layout.addWidget(self.label_duration)
        layout.addWidget(self.entry_duration)
        layout.addWidget(self.label_start_delay)
        layout.addWidget(self.entry_start_delay)
        layout.addWidget(self.start_button)
        self.setLayout(layout)

    def start_clicking(self):
        try:
            # 获取输入的参数
            interval = float(self.entry_interval.text())
            duration = float(self.entry_duration.text())
            start_delay = float(self.entry_start_delay.text())

            # 检查输入有效性
            if interval <= 0 or duration <= 0 or start_delay < 0:
                raise ValueError

            # 开始前延迟
            QMessageBox.information(self, "提示", f"将在 {start_delay} 秒后开始连点...")
            time.sleep(start_delay)

            # 连点操作
            end_time = time.time() + duration
            while time.time() < end_time:
                pyautogui.click()
                time.sleep(interval)

            QMessageBox.information(self, "提示", "连点结束")

        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的数字（正数）")

# 主程序入口
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ClickerApp()
    window.show()
    sys.exit(app.exec_())
