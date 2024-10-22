import sys
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget
from PyQt5.QtGui import QPixmap, QPalette, QBrush
from PyQt5.QtCore import Qt

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 設置主視窗尺寸和標題
        self.setWindowTitle('Solving Interface')
        self.setGeometry(100, 100, 1024, 768)  # 可根據屏幕大小調整

        # 設置背景圖片
        self.set_background_image('/Users/linchengyu/Downloads/113-1_interface_app_version-2.png')

        # 創建按鈕
        self.create_buttons()

    def set_background_image(self, image_path):
        # 載入圖片
        background_image = QPixmap(image_path)

        # 使用調色板設定背景圖片
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(background_image.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

    def create_buttons(self):
        # 創建並定位按鈕，根據圖片的佈局
        self.button1 = QPushButton(' ', self)
        self.button2 = QPushButton(' ', self)
        self.button3 = QPushButton(' ', self)
        self.button4 = QPushButton(' ', self)
        self.button5 = QPushButton(' ', self)

        # 為按鈕設置點擊事件
        self.button1.clicked.connect(lambda: self.on_button_click('國文'))
        self.button2.clicked.connect(lambda: self.on_button_click('英文'))
        self.button3.clicked.connect(lambda: self.on_button_click('數學'))
        self.button4.clicked.connect(lambda: self.on_button_click('自然'))
        self.button5.clicked.connect(lambda: self.on_button_click('社會'))

    def resizeEvent(self, event):
        # 當窗口大小改變時更新背景圖片的大小
        self.set_background_image('/Users/linchengyu/Downloads/113-1_interface_app_version-2.png')

        # 計算按鈕的位置和尺寸
        width = self.width()
        height = self.height()

        button_width = int(width * 0.15)
        button_height = int(height * 0.25)

        # 設置按鈕位置與尺寸
        # 國文、英文在第一行
        self.button1.setGeometry(int(width * 0.425), int(height * 0.26), button_width, button_height)  # 國文
        self.button2.setGeometry(int(width * 0.675), int(height * 0.26), button_width, button_height)  # 英文

        # 數學、自然、社會在第二行
        self.button3.setGeometry(int(width * 0.18), int(height * 0.61), button_width, button_height)  # 數學
        self.button4.setGeometry(int(width * 0.425), int(height * 0.61), button_width, button_height)  # 自然
        self.button5.setGeometry(int(width * 0.675), int(height * 0.61), button_width, button_height)  # 社會


        self.button1.setStyleSheet('background-color: transparent;')
        self.button2.setStyleSheet('background-color: transparent;')
        self.button3.setStyleSheet('background-color: transparent;')
        self.button4.setStyleSheet('background-color: transparent;')
        self.button5.setStyleSheet('background-color: transparent;')

    def on_button_click(self, button_name):
        print(f"{button_name} 按鈕被點擊！")
        # 可以在這裡添加相應的功能

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


