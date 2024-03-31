import sqlite3
import datetime
import time
from datetime import datetime
from textwrap import wrap
import io
import random
import requests
import gspread
from google.oauth2.service_account import Credentials

scopes = [
    "https://www.googleapis.com/auth/spreadsheets"
]

creds = Credentials.from_service_account_file("YOUR_CREDENTIALS_FILE.json", scopes=scopes)
client = gspread.authorize(creds)
sheet_id = "YOUR_SHEET_ID"
work_book = client.open_by_key(sheet_id)
sheets = work_book.worksheets()

class BotDB:

    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def get_google_list(self, sheet_id):
        values_list = sheets[sheet_id].get_values()
        return values_list

    def google_update_data(self, sheet_id, row, column, data):
        try:
            sheets[sheet_id].update_cell(row, column, data)
            return True
        except Exception as e:
            print(e)
            return False

    def validate(self, date_text):
        try:
            if date_text != datetime.strptime(date_text, "%d.%m.%Y").strftime('%d.%m.%Y'):
                raise ValueError
            return True
        except ValueError:
            return False

    def user_exists(self, user_id):
        """Проверяем, есть ли юзер в базе"""
        result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
        return bool(len(result.fetchall()))

    def get_user_id(self, user_id):
        """Достаем id юзера в базе по его user_id"""
        result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
        return result.fetchone()[0]

    def add_user(self, user_id, username):
        """Добавляем юзера в базу"""
        self.cursor.execute("INSERT INTO `users` (`user_id`, `username`) VALUES (?, ?)", (user_id, str(username)))
        return self.conn.commit()

    def add_record(self, user_id, value):
        """Создаем запись о доходах/расходах"""
        self.cursor.execute("INSERT INTO `records` (`users_id`, `value`) VALUES (?, ?)",
            (user_id,
            value))
        return self.conn.commit()

    def get_records(self, user_id, within = "all"):
        """Получаем историю о доходах/расходах"""

        if within == "day":
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = ? AND `date` BETWEEN datetime('now', 'start of day') AND datetime('now', 'localtime') ORDER BY `date`",
                (self.get_user_id(user_id),))
        elif within == "week":
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = ? AND `date` BETWEEN datetime('now', '-6 days') AND datetime('now', 'localtime') ORDER BY `date`",
                (self.get_user_id(user_id),))
        elif within == "month":
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = ? AND `date` BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime') ORDER BY `date`",
                (self.get_user_id(user_id),))
        else:
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = ?",
                (user_id))
        return result.fetchall()

    def get_users(self):
        result = self.cursor.execute("SELECT `user_id` FROM `users`")
        answer = result.fetchall()
        return answer

    def update_username(self, user_id, username):
        self.cursor.execute('UPDATE `users` SET username=? WHERE user_id=?', [username, user_id])
        # self.cursor.execute("REPLACE INTO `users` (`user_id`, `checks`)  VALUES (?, ?)", (user_id, available_checks))
        self.conn.commit()

    def update_info(self, user_id, row, data):
        self.cursor.execute(f'UPDATE `users` SET {str(row)}=? WHERE user_id=?', [data, user_id])
        self.conn.commit()

    def get_custom_info(self, user_id, row):
        data = self.cursor.execute(f"SELECT `{row}` from `users` WHERE user_id=?", [user_id])
        data = data.fetchall()
        return data

    def get_all_in_gym(self):
        data = self.cursor.execute(f"SELECT `in_gym` from `users`")
        data = data.fetchall()
        return data

    def get_user_info(self, user_id):
        name_surname = self.cursor.execute("SELECT `name_surname` from `users` WHERE user_id=?", [user_id])
        name_surname = name_surname.fetchall()
        adres = self.cursor.execute("SELECT `adres` from `users` WHERE user_id=?", [user_id])
        adres = adres.fetchall()
        payment_type = self.cursor.execute("SELECT `payment_type` from `users` WHERE user_id=?", [user_id])
        payment_type = payment_type.fetchall()
        return [name_surname[0][0], adres[0][0], payment_type[0][0]]

    def get_next_pay(self, user_id):
        next_pay = self.cursor.execute("SELECT `next_pay` from `users` WHERE user_id=?", [user_id])
        next_pay = next_pay.fetchall()
        return next_pay[0][0]

    def get_in_gym(self, user_id, move):
        self.cursor.execute("INSERT INTO `journal` (`user_id`, `movement`) VALUES (?, ?)", (user_id, str(move)))
        return self.conn.commit()

    def get_in_gym_info(self, user_id):
        data = self.cursor.execute("SELECT * from `journal` WHERE user_id=?", [user_id])
        data = data.fetchall()
        return data

    def get_remain_days(self, user_id):
        data = self.cursor.execute("SELECT `next_pay` from `users` WHERE user_id=?", [user_id])
        data = data.fetchall()
        return data

    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()

