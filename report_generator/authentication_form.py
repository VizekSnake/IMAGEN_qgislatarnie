from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QDockWidget, QWidget, QGroupBox, \
    QMessageBox
from PyQt5.QtWidgets import QApplication

from PyQt5.QtWidgets import QDialog, QLineEdit, QPushButton
from PyQt5.uic import loadUi
import psycopg2
import bcrypt
import ssl


class AuthenticationForm(QDockWidget):

    def __init__(self):
        super().__init__()
        loadUi("path to UI", self)

        self.username_input = self.findChild(QLineEdit, 'username_input')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input = self.findChild(QLineEdit, 'password_input')
        self.submit_button = self.findChild(QPushButton, 'login_button')

        # Connect submit button to a function
        self.submit_button.clicked.connect(self.validate_credentials)

        # Find the login_box
        self.login_box = self.findChild(QGroupBox, 'Login_box')

        # Create the plugin options and logout button (initially hidden)
        self.plugin_options = QLabel("Plugin options go here...")
        self.logout_button = QPushButton("Logout")
        self.plugin_options.setVisible(False)
        self.logout_button.setVisible(False)

        # Connect the logout button to a function
        self.logout_button.clicked.connect(self.logout)

        # Create a QWidget and set its layout
        self.container_widget = QWidget()
        self.container_layout = QVBoxLayout()
        self.container_widget.setLayout(self.container_layout)

        # Add the login_box, plugin_options, and logout_button to the container_layout
        self.container_layout.addWidget(self.login_box)
        self.container_layout.addWidget(self.plugin_options)
        self.container_layout.addWidget(self.logout_button)

        # Set the container_widget as the central widget of the QDockWidget
        self.setWidget(self.container_widget)

    def validate_credentials(self):
        username = self.username_input.text()
        password = self.password_input.text().encode('utf-8')

        try:
            ssl_context = ssl.create_default_context(cafile='path/to/server-ca.pem')
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            conn = psycopg2.connect(
                dbname="database",
                user="user",
                password="password",
                host="host",
                sslmode="require",
                sslrootcert="path/to/server-ca.pem",
                sslcontext=ssl_context
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
                        self.message_label.setText("Access granted.")
                        self.login_box.setVisible(False)
                        self.plugin_options.setVisible(True)
                        self.logout_button.setVisible(True)
                    else:
                        self.show_error_message("Nieprawidłowa nazwa użytkownika lub hasło")
                else:
                    self.show_error_message("Nieprawidłowa nazwa użytkownika lub hasło")

                cur.close()
                conn.close()

        except Exception as e:
            print("Error:", e)
            self.show_error_message("Błąd połączenia z bazą danych")

    def show_error_message(self, message):
        QMessageBox.warning(self, "Error", message)

    def logout(self):
        # Hide the plugin options and logout button
        self.plugin_options.setVisible(False)
        self.logout_button.setVisible(False)

        # Show the login_box and clear the input fields
        self.login_box.setVisible(True)
        self.username_input.setText('')
        self.password_input.setText('')
        self.username_input.setFocus()


if __name__ == '__main__':
    app = QApplication([])
    form = AuthenticationForm()
    form.show()
    app.exec_()
