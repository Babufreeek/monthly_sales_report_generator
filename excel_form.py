import sys
import openpyxl
import os
from monthly_sales_calculations import total_sales
import styles
from helpers import LoadingScreen, FileProcessor
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QVBoxLayout, QComboBox, QCheckBox, QMessageBox

class ExcelForm(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Set default width and height of window
        self.resize(styles.width, styles.height)

        # Set default font size and dimensions of buttons and text
        self.setStyleSheet(styles.style_sheet)

        # Select Excel File
        self.excel_file_label = QLabel('Select Excel File:')
        self.excel_file_edit = QLineEdit()
        self.excel_file_button = QPushButton('Browse')
        self.excel_file_button.clicked.connect(self.get_excel_file)

        # Select Worksheet
        self.worksheet_label = QLabel('Select Worksheet:')
        self.worksheet_combo = QComboBox()

        # Translation Source File
        self.translation_source_label = QLabel('Select Translation Source Excel File:')
        # Search for translation source and autofill if possible
        search_results = ExcelForm.autofill_translation_source()
        self.translation_source_edit = QLineEdit(search_results if search_results else '')
        self.translation_source_button = QPushButton('Browse')
        self.translation_source_button.clicked.connect(self.get_translation_source)

        # Option to specify if raw data is already translated
        self.already_translated_checkbox = QCheckBox('Raw Data in English')
        self.already_translated_checkbox.stateChanged.connect(self.toggle_already_translated)

        # Option to save translated table as a new worksheet in the existing file
        self.save_translations_checkbox = QCheckBox('Save Translation of Raw Data')

        # Option to just translate the worksheet without needing to process the data further
        self.translate_only_checkbox = QCheckBox('Translate Raw Data Only')
        self.translate_only_checkbox.stateChanged.connect(self.toggle_translate_only)

        self.output_method_label = QLabel('Select Output Method Below:')

        # Option to add the data into the existing spreadsheet
        self.add_to_existing_checkbox = QCheckBox('Add to Existing Spreadsheet')
        self.add_to_existing_checkbox.stateChanged.connect(self.toggle_add_to_existing)

        # Name of new worksheet to be added
        self.worksheet_to_add_label = QLabel('Worksheet to Add:')
        self.worksheet_to_add_edit = QLineEdit()
        self.worksheet_to_add_edit.setEnabled(False)

        # Option to output the data in the brand new spreadsheet (selected by default)
        self.create_new_spreadsheet_checkbox = QCheckBox('Create New Spreadsheet')
        self.create_new_spreadsheet_checkbox.setChecked(True)  # Checked by default
        self.create_new_spreadsheet_checkbox.stateChanged.connect(self.toggle_create_new_spreadsheet)

        # Filename of new spreadsheet
        self.new_filename_label = QLabel('New Filename:')
        self.new_filename_edit = QLineEdit('Result.xlsx')
        self.new_filename_edit.setEnabled(True)

        # Folder to save output in
        self.output_location_label = QLabel('Output Location:')
        self.output_location_edit = QLineEdit()
        self.output_location_edit.setEnabled(True)

        self.browse_location_button = QPushButton('Browse')
        self.browse_location_button.setEnabled(True)
        self.browse_location_button.clicked.connect(self.get_output_location)

        # Worksheet name in the new file
        self.new_worksheet_label = QLabel('New Worksheet Name:')
        self.new_worksheet_edit = QLineEdit('Sheet1')
        self.new_worksheet_edit.setEnabled(True)

        # Submit button
        self.submit_button = QPushButton('Submit')
        self.submit_button.clicked.connect(self.submit_form)

        # Set default value for Worksheet to Add
        self.worksheet_to_add_edit.setText('Monthly Sales Calculations')

        # Loading screen
        self.loading_screen = LoadingScreen()

        layout = QVBoxLayout()
        layout.addWidget(self.excel_file_label)
        layout.addWidget(self.excel_file_edit)
        layout.addWidget(self.excel_file_button)

        layout.addWidget(self.worksheet_label)
        layout.addWidget(self.worksheet_combo)

        layout.addWidget(self.translation_source_label)
        layout.addWidget(self.translation_source_edit)
        layout.addWidget(self.translation_source_button)

        layout.addWidget(self.already_translated_checkbox)
        layout.addWidget(self.save_translations_checkbox)
        layout.addWidget(self.translate_only_checkbox)

        layout.addWidget(self.output_method_label)

        layout.addWidget(self.add_to_existing_checkbox)
        layout.addWidget(self.worksheet_to_add_label)
        layout.addWidget(self.worksheet_to_add_edit)

        layout.addWidget(self.create_new_spreadsheet_checkbox)

        layout.addWidget(self.new_filename_label)
        layout.addWidget(self.new_filename_edit)

        layout.addWidget(self.output_location_label)
        layout.addWidget(self.output_location_edit)

        layout.addWidget(self.browse_location_button)

        layout.addWidget(self.new_worksheet_label)
        layout.addWidget(self.new_worksheet_edit)

        layout.addWidget(self.submit_button)

        self.setLayout(layout)
    
    def toggle_translate_only(self, state):
        if state == 2:  # Checked
            # Disable already translated field
            self.already_translated_checkbox.setChecked(False)
            self.already_translated_checkbox.setEnabled(False)

            # Check save translations field and disable it
            self.save_translations_checkbox.setChecked(True)
            self.save_translations_checkbox.setEnabled(False)

            # Disable add to existing spreadsheet checkbox
            self.add_to_existing_checkbox.setChecked(False)
            self.add_to_existing_checkbox.setEnabled(False)
            self.toggle_add_to_existing(self.add_to_existing_checkbox.stateChanged)

            # Disable create new spreadsheet checkbox
            self.create_new_spreadsheet_checkbox.setChecked(False)
            self.create_new_spreadsheet_checkbox.setEnabled(False)
            self.toggle_create_new_spreadsheet(self.create_new_spreadsheet_checkbox.stateChanged)
        else:
            # Enable already translated checkbox
            self.already_translated_checkbox.setEnabled(True)

            # Enable save translations checkbox
            self.save_translations_checkbox.setChecked(False)
            self.save_translations_checkbox.setEnabled(True)

            # Enable Create New Spreadsheet and Add to Existing Spreadsheet checkboxes
            self.add_to_existing_checkbox.setEnabled(True)
            self.create_new_spreadsheet_checkbox.setEnabled(True)

            # Check Create New Spreadsheet checkbox
            self.create_new_spreadsheet_checkbox.setChecked(True)
    
    def toggle_already_translated(self, state):
        if state == 2:  # Checked
            self.save_translations_checkbox.setChecked(False)
            self.save_translations_checkbox.setEnabled(False)
            self.translate_only_checkbox.setChecked(False)
            self.translate_only_checkbox.setEnabled(False)
        else:
            self.save_translations_checkbox.setEnabled(True)
            self.translate_only_checkbox.setEnabled(True)
        
    def get_excel_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setNameFilter('Excel Files (*.xlsx *.xls *.xlsm)')
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.excel_file_edit.setText(selected_file)

            # Processor for loading worksheets into the combo box
            self.worksheet_processor = FileProcessor(self.load_worksheets, selected_file)

            # Temporarily disable submit button
            self.submit_button.setEnabled(False)

            # Show loading screen before starting processing and start processor
            self.loading_screen.show()
            self.worksheet_processor.start()

            # After processor is finished, close loading screen
            self.worksheet_processor.finished.connect(self.loading_screen.close)

            # Autofill output location field with path for folder of the selected file
            self.output_location_edit.setText(os.path.dirname(selected_file))

    @classmethod
    def autofill_translation_source(cls):
        """
        Look in the present working directory for the translation file
        """
        # Get list of files in all the directory and subdirectory
        for root, dirs, files in os.walk(os.getcwd()):
            for file in files:
                # Return file path if a matching file is found
                if "language translation" in file.lower():
                    return os.path.join(root, file)
        # Else return None at the end
        return None
    
    def get_translation_source(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setNameFilter('Excel Files (*.xlsx *.xls *.xlsm)')
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.translation_source_edit.setText(selected_file)

    def load_worksheets(self, excel_file):
        self.worksheet_combo.clear()

        print("Loading worksheets...")

        try:
            workbook = openpyxl.load_workbook(excel_file, read_only=True)
            self.worksheet_combo.addItems(workbook.sheetnames)
        except Exception as e:
            print(f"Error loading worksheets: {e}")

        print("Worksheets loaded!")

        # Re-enable submit button after processor is finished
        self.submit_button.setEnabled(True)

    def toggle_add_to_existing(self, state):
        self.worksheet_to_add_edit.setEnabled(state == 2)  # 2 is checked, 0 is unchecked

    def toggle_create_new_spreadsheet(self, state):
        self.new_filename_edit.setEnabled(state == 2)  # 2 is checked, 0 is unchecked
        self.browse_location_button.setEnabled(state == 2)  # 2 is checked, 0 is unchecked
        self.output_location_edit.setEnabled(state == 2)  # 2 is checked, 0 is unchecked
        self.new_worksheet_edit.setEnabled(state == 2)  # 2 is checked, 0 is unchecked

    def get_output_location(self):
        folder_dialog = QFileDialog()
        folder_dialog.setFileMode(QFileDialog.Directory)
        if folder_dialog.exec_():
            selected_folder = folder_dialog.selectedFiles()[0]
            self.output_location_edit.setText(selected_folder)

    def submit_form(self):
        excel_file = self.excel_file_edit.text()
        worksheet_name = self.worksheet_combo.currentText()
        translation_source = self.translation_source_edit.text()

        already_translated = self.already_translated_checkbox.isChecked()
        save_translations = self.save_translations_checkbox.isChecked()
        translate_only = self.translate_only_checkbox.isChecked()

        add_to_existing = self.add_to_existing_checkbox.isChecked()
        worksheet_to_add = self.worksheet_to_add_edit.text() if add_to_existing else None

        create_new_spreadsheet = self.create_new_spreadsheet_checkbox.isChecked()
        new_filename = self.new_filename_edit.text().strip() if create_new_spreadsheet else None
        output_location = self.output_location_edit.text() if create_new_spreadsheet else None
        new_worksheet_name = self.new_worksheet_edit.text() if create_new_spreadsheet else None

        # Check that all relevant fields are filled up and show error messages if needed
        if not excel_file or not worksheet_name or not translation_source:
            self.show_message("Missing Fields", "Excel file, worksheet, and translation file fields cannot be blank.")
            return

        if not add_to_existing and not create_new_spreadsheet and not translate_only:
            self.show_message("Missing Fields", "Either 'Add to Existing Spreadsheet' or 'Create New Spreadsheet' must be checked.")
            return

        if create_new_spreadsheet and (not new_filename or not output_location or not new_worksheet_name):
            self.show_message("Missing Fields", "If 'Create New Spreadsheet' is checked, filename, location, and worksheet fields cannot be blank.")
            return

        if add_to_existing and not worksheet_to_add:
            self.show_message("Missing Fields", "If 'Add to Existing Spreadsheet' is checked, 'Worksheet to Add' field cannot be blank.")
            return

        # Add xlsx extension to new filename if not present
        if new_filename and not new_filename.endswith(".xlsx"):
            new_filename += ".xlsx"

        print("Generating Report...")
        
        # Disable submit button temporarily
        self.submit_button.setEnabled(False)

        # Save variables needed for running calculations
        myvariables = (
            excel_file,
            worksheet_name,
            translation_source,
            already_translated,
            save_translations,
            translate_only,
            add_to_existing,
            worksheet_to_add,
            create_new_spreadsheet,
            os.path.join(output_location, new_filename) if new_filename else "",
            new_worksheet_name,
        )
        # Create processor for running code
        self.report_processor = FileProcessor(total_sales, *myvariables)

        # Show loading screen before starting processing
        self.loading_screen.show()
        # Start running total sales function
        self.report_processor.start()

        # Afterwards, close loading screen and show processed message
        self.report_processor.finished.connect(self.loading_screen.close)
        self.report_processor.finished.connect(self.show_processed_message)
        self.report_processor.finished.connect(lambda: print("Report generated!"))


    def show_message(self, title, text):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.exec_()

    def show_processed_message(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Files Processed")
        msg_box.setText("Files have been processed!")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.finished.connect(self.clear_fields)
        msg_box.exec_()

    def clear_fields(self):
        # Clear all fields
        self.excel_file_edit.clear()
        self.worksheet_combo.clear()
        self.translation_source_edit.clear()

        self.already_translated_checkbox.setChecked(False)

        self.save_translations_checkbox.setEnabled(True)
        self.save_translations_checkbox.setChecked(False)

        self.translate_only_checkbox.setEnabled(True)
        self.translate_only_checkbox.setChecked(False)

        self.add_to_existing_checkbox.setEnabled(True)
        self.add_to_existing_checkbox.setChecked(False)
        self.worksheet_to_add_edit.clear()
        self.worksheet_to_add_edit.setEnabled(False)
        
        self.create_new_spreadsheet_checkbox.setEnabled(True) 
        self.create_new_spreadsheet_checkbox.setChecked(True)  # Set back to default state
        self.new_filename_edit.clear()
        self.output_location_edit.clear()
        self.new_worksheet_edit.clear()

        # Set default values for specific fields
        search_results = ExcelForm.autofill_translation_source()
        self.translation_source_edit.setText(search_results if search_results else '')
        self.new_filename_edit.setText('Result.xlsx')
        self.worksheet_to_add_edit.setText('Monthly Sales Calculation')
        self.new_worksheet_edit.setText('Sheet1')
        
        # Re-enable submit button
        self.submit_button.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    excel_form = ExcelForm()
    excel_form.show()
    sys.exit(app.exec_())
