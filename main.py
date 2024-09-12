import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QComboBox, QPushButton, QLineEdit, QLabel, QMessageBox, QDateEdit
from PyQt6.QtCore import Qt, QDate
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.dates as mdates

class WeightTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weight Tracker")
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        main_layout = QHBoxLayout()

        # Left side (list, filter, and input form)
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # Add input form
        input_layout = QHBoxLayout()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)  # Enable calendar popup
        self.date_input.setDate(QDate.currentDate())  # Set default to current date
        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText("Weight")  # Changed from "Weight in kg"
        add_button = QPushButton("Add Entry")
        add_button.clicked.connect(self.add_entry)
        
        input_layout.addWidget(QLabel("Date:"))
        input_layout.addWidget(self.date_input)
        input_layout.addWidget(QLabel("Weight:"))
        input_layout.addWidget(self.weight_input)
        input_layout.addWidget(add_button)
        
        left_layout.addLayout(input_layout)
        
        # Initialize weight_list
        self.weight_list = QListWidget()
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Ascending", "Descending"])
        self.sort_combo.currentIndexChanged.connect(self.update_list)

        # Add delete button
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_entry)

        left_layout.addWidget(self.sort_combo)
        left_layout.addWidget(self.weight_list)
        left_layout.addWidget(delete_button)
        
        # Add timeframe filter
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["Daily", "Weekly", "Monthly"])
        self.timeframe_combo.currentIndexChanged.connect(self.update_chart)

        left_layout.addWidget(QLabel("Timeframe:"))
        left_layout.addWidget(self.timeframe_combo)

        left_widget.setLayout(left_layout)

        # Right side (chart)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        # Add widgets to main layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(self.canvas)

        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Load data and update UI
        self.data_file = 'weight_data.csv'
        self.load_data()
        self.update_list()
        self.update_chart()

    def add_entry(self):
        date = pd.Timestamp(self.date_input.date().toPyDate())
        weight_str = self.weight_input.text()
        
        try:
            weight = float(weight_str)
            
            # Check if an entry for this date already exists
            date_str = date.strftime('%Y-%m-%d')
            if date_str in self.data['date'].dt.strftime('%Y-%m-%d').values:
                QMessageBox.warning(self, "Duplicate Entry", 
                                    f"An entry for {date_str} already exists. "
                                    "Please choose a different date or edit the existing entry.")
                return
            
            new_entry = pd.DataFrame({'date': [date], 'weight': [weight]})
            self.data = pd.concat([self.data, new_entry]).sort_values('date')
            
            self.update_list()
            self.update_chart()
            self.save_data()  # Save data after adding new entry
            
            self.date_input.setDate(QDate.currentDate())  # Reset to current date
            self.weight_input.clear()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid weight.")

    def delete_entry(self):
        selected_items = self.weight_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            date_str = item.text().split(":")[0].strip()
            self.data = self.data[self.data['date'].dt.strftime('%Y-%m-%d') != date_str]

        self.update_list()
        self.update_chart()
        self.save_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            self.data = pd.read_csv(self.data_file)
            self.data['date'] = pd.to_datetime(self.data['date'])
        else:
            self.data = pd.DataFrame(columns=['date', 'weight'])

    def save_data(self):
        self.data.to_csv(self.data_file, index=False)

    def update_list(self):
        self.weight_list.clear()
        sort_order = self.sort_combo.currentText()
        sorted_data = self.data.sort_values('date', ascending=(sort_order == "Ascending"))
        
        for _, row in sorted_data.iterrows():
            self.weight_list.addItem(f"{row['date'].strftime('%Y-%m-%d')}: {row['weight']}")  # Removed " kg"

    def update_chart(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        timeframe = self.timeframe_combo.currentText()

        if timeframe == "Daily":
            data = self.data
        elif timeframe == "Weekly":
            data = self.data.resample('W', on='date').mean().reset_index()
        elif timeframe == "Monthly":
            data = self.data.resample('M', on='date').mean().reset_index()

        ax.plot(data['date'], data['weight'])
        ax.set_xlabel('Date')
        ax.set_ylabel('Weight')  # Removed "(kg)"
        ax.set_title(f'Weight Trend ({timeframe})')

        # Adjust x-axis ticks based on timeframe
        if timeframe == "Daily":
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        elif timeframe == "Weekly":
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        elif timeframe == "Monthly":
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        self.figure.tight_layout()
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WeightTracker()
    window.show()
    sys.exit(app.exec())
