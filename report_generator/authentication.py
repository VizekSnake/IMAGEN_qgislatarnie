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
from qgis.PyQt import QtCore
from PyQt5.QtWidgets import QScrollArea, QCheckBox


class Authentication(QDockWidget):
    @staticmethod
    def validate_credentials(dock_widget, username, password):
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
                        dock_widget.login_box.setVisible(False)  # Hide the login form
                        dock_widget.plugin_options.setVisible(False)  # Show the plugin options
                        dock_widget.logout_button.setVisible(True)  # Show the logout button
                        dock_widget.layer_combo_box.setVisible(True)
                        dock_widget.export_button.setVisible(True)
                        dock_widget.export_button.setVisible(True)
                        dock_widget.layer_combo_box.setVisible(True)
                        # Hide the login box and clear the input fields
                        dock_widget.login_box.setVisible(False)
                        dock_widget.username_input.setText('')
                        dock_widget.password_input.setText('')
                        dock_widget.username_input.setFocus()
                    else:
                        dock_widget.show_error_message("Nieprawidłowe dane logowania")
                else:
                    dock_widget.show_error_message("Invalid username or password")

                cur.close()
                conn.close()

        except Exception as e:
            print("Error:", e)
            dock_widget.show_error_message("Error connecting to the database")


