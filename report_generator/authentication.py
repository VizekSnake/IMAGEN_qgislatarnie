from qgis.PyQt import Qt
from qgis.PyQt.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QDockWidget, QWidget, QGroupBox, \
    QMessageBox
from qgis._core import QgsProject

# from qgis.PyQt.QtWidgets import QApplication
#
# from qgis.PyQt.QtWidgets import QDialog, QLineEdit, QPushButton
# from qgis.PyQt.uic import loadUi
import psycopg2
import bcrypt
import ssl

from PyQt5.QtWidgets import QScrollArea, QCheckBox


class Authentication(QDockWidget):

    def validate_credentials(self, username, password):
        password = password.encode('utf-8')
        try:
            # Connect to the PostgreSQL database with SSL
            # ssl_context = ssl.create_default_context(cafile='path/to/server-ca.pem')
            # ssl_context.check_hostname = False
            # ssl_context.verify_mode = ssl.CERT_NONE
            conn = psycopg2.connect(
                dbname="name",
                user="user",
                password="password",
                host="host",
                # sslmode="require",
                # sslrootcert="path/to/server-ca.pem",
                # sslcontext=ssl_context
            )
            cur = conn.cursor()

            # Query the database for the user with the given username
            with conn.cursor() as cur:
                # Fetch the stored password hash for the provided username
                cur.execute("SELECT password_hash FROM test_users WHERE username=%s", (username,))
                result = cur.fetchone()

                if result:
                    stored_password_hash = result[0].encode('utf-8')  # Encode the stored password hash to bytes

                    # Verify the provided password against the stored password hash
                    if bcrypt.checkpw(password, stored_password_hash):
                        # Authentication successful
                        # self.message_label.setText("Zalogowano pomyślnie.")
                        self.login_box.setVisible(False)  # Hide the login form
                        self.plugin_options.setVisible(False)  # Show the plugin options
                        self.logout_button.setVisible(True)  # Show the logout button
                        self.layer_combo_box.setVisible(True)
                        self.export_button.setVisible(True)
                        layer_name = self.layer_combo_box.currentText()
                        layer = QgsProject.instance().mapLayersByName(layer_name)[0]

                        # Get the attributes of the selected layer
                        attributes = [f.name() for f in layer.fields()]

                        # Remove all existing checkboxes
                        for checkbox in self.findChildren(QCheckBox):
                            checkbox.setParent(None)

                        # Create a new widget for the checkboxes and add them to it
                        checkboxes_widget = QWidget()
                        checkboxes_layout = QVBoxLayout()
                        checkboxes_widget.setLayout(checkboxes_layout)
                        for attribute in attributes:
                            checkbox = QCheckBox(attribute)
                            checkbox.setObjectName(attribute)
                            checkbox.setChecked(True)
                            checkboxes_layout.addWidget(checkbox)

                        # Create a new scroll area and set the checkboxes widget as its widget
                        scroll_area = QScrollArea()
                        # scroll_area.setWidgetResizable(True)
                        scroll_area.setMaximumHeight(200)
                        scroll_area.setWidget(checkboxes_widget)

                        # Show the export button and scroll area
                        self.export_button.setVisible(True)
                        self.layer_combo_box.setVisible(True)
                        scroll_area.setVisible(True)

                        # Set the scroll area as the central widget for the dock widget
                        self.container_layout.addWidget(scroll_area)
                        self.container_layout.setAlignment(scroll_area, Qt.AlignTop)

                        # Hide the login box and clear the input fields
                        self.login_box.setVisible(False)
                        self.username_input.setText('')
                        self.password_input.setText('')
                        self.username_input.setFocus()
                    else:
                        self.show_error_message("Nieprawidłowe dane logowania")
                else:
                    self.show_error_message("Invalid username or password")

                cur.close()
                conn.close()

        except Exception as e:
            print("Error:", e)
            self.show_error_message("Error connecting to the database")


