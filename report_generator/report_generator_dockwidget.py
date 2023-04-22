# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PointReportGeneratorDockWidget
                                 A QGIS plugin
 Plugin generates raport based on values from table of vetor layer
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-04-13
        git sha              : $Format:%H$
        copyright            : (C) 2023 by IMAGEN KG
        email                : adimagen@protonmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt.QtWidgets import QLineEdit, QPushButton, QGroupBox, QLabel, QWidget, QVBoxLayout, QMessageBox
from qgis.PyQt import QtGui, QtWidgets, uic, QtCore
from qgis.PyQt.QtCore import pyqtSignal
from fpdf import FPDF
from reportlab.lib.units import inch
from PyQt5.QtWidgets import QCheckBox, QScrollArea, QComboBox
from reportlab.pdfbase import pdfmetrics

from .authentication import Authentication
from qgis.PyQt.QtWidgets import QFileDialog

from qgis.core import *
import csv
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'report_generator_dockwidget_base.ui'))


class PointReportGeneratorDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(PointReportGeneratorDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.username_input = self.findChild(QLineEdit, 'username_input')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input = self.findChild(QLineEdit, 'password_input')
        self.attributes_combo_box = self.findChild(QComboBox, 'attributes_combo_box')
        self.attributes_combo_box.setVisible(False)
        self.filter_combo_box = self.findChild(QComboBox, 'filter_combo_box')
        self.filter_combo_box.setVisible(False)

        # Find the login_box
        self.login_box = self.findChild(QGroupBox, 'Login_box')

        # Create the plugin options and logout button (initially hidden)
        self.plugin_options = QLabel("Plugin options go here...")
        self.plugin_options.setMaximumHeight(100)
        # self.logout_button = QPushButton("Logout")
        self.plugin_options.setVisible(False)
        self.logout_button.setVisible(False)

        # # Connect the logout button to a function
        # self.logout_button.clicked.connect(self.logout)

        # Create a QWidget and set its layout
        self.container_widget = QWidget()
        self.container_layout = QVBoxLayout()
        self.container_widget.setLayout(self.container_layout)

        # Add the login_box, plugin_options, and logout_button to the container_layout
        self.container_layout.addWidget(self.login_box)
        self.container_layout.addWidget(self.attributes_combo_box)
        self.container_layout.addWidget(self.filter_combo_box)


        # self.container_layout.addWidget(self.message_label)
        self.container_layout.addWidget(self.plugin_options)
        self.layer_combo_box.setVisible(False)
        self.layer_combo_box.clear()
        vector_layers = [layer for layer in QgsProject.instance().mapLayers().values() if
                         layer.type() == QgsMapLayer.VectorLayer]
        self.layer_combo_box.addItems([layer.name() for layer in vector_layers])

        # Connect the "Export" button to the export method
        self.export_button.setVisible(False)

        self.export_button.clicked.connect(self.export_table)
        self.container_layout.addWidget(self.export_button)
        self.container_layout.addWidget(self.layer_combo_box)
        self.container_layout.addWidget(self.logout_button)
        # Populate the combo box with the names of all layers

        # Set the container_widget as the central widget of the QDockWidget
        self.setWidget(self.container_widget)

        # Initially hide logout button
        self.logout_button.setVisible(False)

        # Connect the "Login" button to the login method
        self.login_button.clicked.connect(self.login)

        # Connect the "Logout" button to the logout method
        self.logout_button.clicked.connect(self.logout)



        self.attribute_checkboxes = []
        self.connect_combo_boxes()


    def populate_attributes_combo_box(self):
        layer_name = self.layer_combo_box.currentText()
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        fields = layer.fields()

        self.attributes_combo_box.clear()
        self.attributes_combo_box.addItems([field.name() for field in fields])

    def populate_filter_values(self, field_name):
        layer_name = self.layer_combo_box.currentText()
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        field_index = layer.fields().lookupField(field_name)

        unique_values = set()
        for feature in layer.getFeatures():
            unique_values.add(feature.attributes()[field_index])

        self.filter_combo_box.clear()
        self.filter_combo_box.addItems(sorted(unique_values, key=lambda x: str(x)))

    def connect_combo_boxes(self):
        self.attributes_combo_box.currentTextChanged.connect(self.populate_filter_values)

    def export_table(self):
        # Get the selected layer from the combo box
        layer_name = self.layer_combo_box.currentText()
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]

        # Get the selected attribute and filter values from the combo boxes
        attribute_name = self.attributes_combo_box.currentText()
        filter_value = self.filter_combo_box.currentText()

        # Get the indexes of the checked attributes
        checked_attributes = [checkbox.text() for checkbox in self.attribute_checkboxes if checkbox.isChecked()]
        field_indexes = [layer.fields().indexFromName(attr_name) for attr_name in checked_attributes]

        # Filter the layer by the selected attribute and filter value
        filtered_features = [feature for feature in layer.getFeatures() if feature[attribute_name] == filter_value]
        if not filtered_features:
            QMessageBox.warning(self, "No records found",
                                "No records found for the selected attribute and filter value.")
            return

        # Create a list of lists containing the attribute values for the selected features
        attribute_values = [[feature[index] for index in field_indexes] for feature in filtered_features]

        # Show a file dialog to let the user choose the output file and format
        file_name, filter = QFileDialog.getSaveFileName(self, "Export Attribute Table", f"{layer_name}_attributes",
                                                        "CSV Files (*.csv);;PDF Files (*.pdf)")

        if file_name:
            if filter == "CSV Files (*.csv)":
                # Write the CSV file with only the checked columns
                with open(file_name, "w", newline="", encoding="utf-8") as csv_file:
                    import os
                    import csv

                    writer = csv.writer(csv_file)
                    writer.writerow(checked_attributes)  # Write header row with checked attribute names
                    for row in attribute_values:
                        writer.writerow(row)

                # Show a message box to indicate success
                QMessageBox.information(self, "Export Complete",
                                        f"Attribute table for layer '{layer_name}' has been exported successfully as a CSV file.")

            elif filter == "PDF Files (*.pdf)":
                import os
                import csv
                # Write the CSV file with only the checked columns
                with open(file_name, "w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(checked_attributes)  # Write header row with checked attribute names
                    for row in attribute_values:
                        writer.writerow(row)

                # Generate the PDF file name
                pdf_file_name = f"{os.path.splitext(file_name)[0]}.pdf"

                # Generate the PDF
                with open(file_name, "r", encoding="utf-8") as csv_file:
                    reader = csv.reader(csv_file)
                    data = [row for row in reader]

                    # Calculate column widths based on maximum content width
                    col_widths = [max(pdfmetrics.stringWidth(str(cell), 'Helvetica', 10) for cell in col) for col in
                                  zip(*data)]
                    col_widths = [w * 2 for w in
                                  col_widths]  # Multiply by a scaling factor (e.g., 6) to set the width in points

                    # Calculate table and page width
                    table_width = sum(col_widths)
                    page_width = table_width + 2 * inch  # Add some margin to the page

                    # Create a PDF file with the reportlab package
                    doc = SimpleDocTemplate(pdf_file_name, pagesize=(page_width, 11 * inch))

                    # Add the data to the PDF
                    table = Table(data, colWidths=col_widths)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    doc.build([table])

                # Show a message box to indicate success
                QMessageBox.information(self, "Export Complete",
                                        f"Attribute table for layer '{layer_name}' has been exported successfully as a PDF file.")
    def create_attribute_checkboxes(self, layer):
        fields = layer.fields()

        # Create a new widget for the checkboxes and add them to it
        checkboxes_widget = QWidget()
        checkboxes_layout = QVBoxLayout()
        checkboxes_widget.setLayout(checkboxes_layout)
        for field in fields:
            checkbox = QCheckBox(field.name())
            checkbox.setChecked(True)
            self.attribute_checkboxes.append(checkbox)
            checkboxes_layout.addWidget(checkbox)

        # Create a new scroll area and set the checkboxes widget as its widget
        self.scroll_area = QScrollArea()
        self.scroll_area.setMaximumHeight(200)
        self.scroll_area.setWidget(checkboxes_widget)

        # Add the scroll area to the container_layout
        self.container_layout.addWidget(self.scroll_area)
        self.container_layout.setAlignment(self.scroll_area, QtCore.Qt.AlignTop)

    def login(self):
        # Validate the credentials using the Authentication class's validate_credentials method
        Authentication.validate_credentials(self, username=self.username_input.text(),
                                            password=self.password_input.text())

        # Get the selected layer from the combo box
        layer_name = self.layer_combo_box.currentText()
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]

        # Create the attribute checkboxes
        self.create_attribute_checkboxes(layer)
        self.populate_attributes_combo_box()
        self.attributes_combo_box.setVisible(True)
        self.filter_combo_box.setVisible(True)

    def show_error_message(self, message):
        QMessageBox.critical(self, "Error", message)

    def logout(self):
        # Hide the plugin options and logout button
        self.layer_combo_box.setVisible(False)
        self.export_button.setVisible(False)
        self.plugin_options.setVisible(False)
        self.logout_button.setVisible(False)
        self.attributes_combo_box.setVisible(False)

        # Remove and clear attribute checkboxes and the scroll area
        for checkbox in self.attribute_checkboxes:
            self.container_layout.removeWidget(checkbox)
            checkbox.setParent(None)
        self.attribute_checkboxes.clear()
        self.container_layout.removeWidget(self.scroll_area)
        self.scroll_area.setVisible(False)

        # Show the login box and clear the input fields
        self.login_box.setVisible(True)
        self.username_input.setText('')
        self.password_input.setText('')
        self.username_input.setFocus()


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
