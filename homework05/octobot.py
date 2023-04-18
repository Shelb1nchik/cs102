import json
import re
import typing as tp
from datetime import datetime, timedelta

import gspread  # type: ignore
import pandas as pd  # type: ignore
import requests  # type: ignore
import telebot  # type: ignore

bot = telebot.TeleBot("5834439815:AAHW9o2l0oOjohq5siXOZ08nIZ-_eZXbP9U")


def is_valid_date(date: str = "01/01/00", divider: str = "/") -> bool:
    """Проверяем, что дата дедлайна валидна:
    - дата не может быть до текущей
    - не может быть позже, чем через год
    - не может быть такой, которой нет в календаре
    - может быть сегодняшним числом
    - пользователь не должен быть обязан вводить конкретный формат даты
    (например, только через точку или только через слеш)"""

    try:
        parsed_date = datetime.strptime(date, f"%d{divider}%m{divider}%y").date()
    except ValueError:
        return False

    today_date = datetime.now().date()
    if parsed_date < today_date:
        return False
    if parsed_date > today_date + timedelta(days=365):
        return False

    return True


def is_valid_url(url: str = "") -> bool:
    """Проверяем, что ссылка рабочая"""
    url = url if ("https://" in url or "http://" in url) else ("https://" + url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False


def convert_date(date: str = "01/01/00"):
    """Конвертируем дату из строки в datetime"""
    d, m, y = list(map(int, re.split(r"[/.]", date, maxsplit=2)))
    try:
        date = datetime(2000 + y, m, d)  # type: ignore
        return date
    except ValueError:
        return False


def connect_table(message):
    """Подключаемся к Google-таблице"""
    url = message.text
    sheet_id = "1Bp8XxBxX4vz6AWRLf_s_yuSlSGH5lQpBrq-uZMcoq_M/edit#gid=0"
    try:
        with open("tables.json") as json_file:
            tables = json.load(json_file)
        title = len(tables) + 1
        tables[title] = {"url": url, "id": sheet_id}
    except FileNotFoundError:
        tables = {0: {"url": url, "id": sheet_id}}
    with open("tables.json", "w") as json_file:
        json.dump(tables, json_file)
    bot.send_message(message.chat.id, "Таблица подключена!")


def access_current_sheet():
    """Обращаемся к Google-таблице"""
    with open("tables.json") as json_file:
        tables = json.load(json_file)
    sheet_id = tables[max(tables)]["id"]
    gc = gspread.service_account(filename="credentials.json")
    sh = gc.open_by_key(sheet_id)
    worksheet = sh.sheet1
    df = pd.DataFrame(worksheet.get_all_records())
    return worksheet, tables[max(tables)]["url"], df


def choose_action(message):
    """Обрабатываем действия верхнего уровня"""
    if message.text == "Подключить Google-таблицу":
        connect_table(message)

    elif message.text == "Редактировать предметы":
        subj_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        subj_markup.row("Добавить новый предмет")
        subj_markup.row("Обновить предмет")
        subj_markup.row("Удалить предмет")
        subj_markup.row("Удалить таблицу")
        subj_markup.row("Назад")
        info = bot.send_message(message.chat.id, "Что хотите сделать?", reply_markup=subj_markup)
        bot.register_next_step_handler(info, choose_subject_action)

    elif message.text == "Редактировать дедлайн":
        deadline_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        deadline_markup.row("Добавить новый дедлайн")
        deadline_markup.row("Изменить дедлайн")
        deadline_markup.row("Назад")
        info = bot.send_message(message.chat.id, "Что хотите сделать?", reply_markup=deadline_markup)
        bot.register_next_step_handler(info, choose_deadline_action)

    elif message.text == "Посмотреть дедлайны на этой неделе":
        next_week_deadlines(message)

    else:
        start(message)


def choose_subject_action(message):
    """Выбираем действие в разделе редактировать предметы"""
    if message.text == "Добавить новый предмет":
        subj = bot.send_message(message.chat.id, "Введите название предмета: ")
        bot.register_next_step_handler(subj, add_new_subject)

    elif message.text == "Обновить предмет":
        subject_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        worksheet, url, df = access_current_sheet()

        subject_list = worksheet.col_values(1)
        subject_list.pop(0)

        for subject in subject_list:
            subject_markup.row(str(subject))
        upd = bot.send_message(message.chat.id, "Выберите название обновляемо предмета", reply_markup=subject_markup)
        bot.register_next_step_handler(upd, update_subject)

    elif message.text == "Удалить предмет":
        deleted = bot.send_message(message.chat.id, "Введите название удаляемого предмета: ")
        bot.register_next_step_handler(deleted, delete_subject)

    elif message.text == "Удалить таблицу":
        choose_removal_option(message)

    elif message.text == "Назад":
        start(message)

    else:
        choose_subject_action(message)


def choose_deadline_action(message):
    """Выбираем действие в разделе редактировать дедлайн"""
    if message.text == "Добавить новый дедлайн" or message.text == "Изменить дедлайн":
        subj = bot.send_message(message.chat.id, "Введите название предмета: ")
        bot.register_next_step_handler(subj, choose_subject)

    elif message.text == "Назад":
        start(message)

    else:
        choose_deadline_action(message)


def next_week_deadlines(message):
    today = datetime.today()
    week = today + timedelta(days=7)
    deadline_message = ""
    worksheet, url, df = access_current_sheet()

    for i in range(2, len(worksheet.col_values(1)) + 1):
        for deadline in worksheet.row_values(i)[2:]:
            try:
                if today <= convert_date(deadline) <= week:
                    deadline_message += f"{worksheet.cell(i, 1).value}: {deadline}\n"
            except ValueError:
                continue

    if not deadline_message:
        deadline_message = "На данной неделе дедлайнов нет"

    bot.send_message(message.chat.id, deadline_message)
    start(message)


def choose_removal_option(message):
    """Уточняем, точно ли надо удалить все"""
    delete_all = bot.send_message(message.chat.id, "Уверены ли вы в удалении всей таблицы? Да/Нет")
    bot.register_next_step_handler(delete_all, clear_subject_list)


def choose_subject(message):
    """Выбираем предмет, у которого надо отредактировать дедлайн"""
    subject = message.text
    info = bot.send_message(message.chat.id, "Введите дату дедлайна и номер работы")
    bot.register_next_step_handler(info, update_new_deadline, subject)


def update_new_deadline(message, subject):
    """Обновляем дедлайн"""
    worksheet, url, df = access_current_sheet()
    date, work_number = message.text.split()

    if is_valid_date(date):
        subject_cell = worksheet.find(subject)
        worksheet.update_cell(subject_cell.row, 2 + int(work_number), date)
        bot.send_message(message.chat.id, "Дедлайн добавлен")
        start(message)
    else:
        bot.send_message(message.chat.id, "Введена некорректная дата")
        choose_deadline_action(message)


def add_new_subject(message):
    """Вносим новое название предмета в Google-таблицу"""
    subject = message.text

    if not check_subject(subject):
        link = bot.send_message(message.chat.id, "Введите ссылку на таблицу: ")
        bot.register_next_step_handler(link, add_new_subject_url, subject)
    else:
        bot.send_message(message.chat.id, "Данный предмет уже есть в таблице")
        start(message)


def add_new_subject_url(message, subject):
    """Вносим новую ссылку на таблицу предмета в Google-таблицу"""
    url = message.text

    if is_valid_url(url):
        link = "" if url == "нет" else url
        worksheet, url, df = access_current_sheet()
        worksheet.append_row([subject, link])

        bot.send_message(message.chat.id, "Данные успешно внесены")
        start(message)

    else:
        bot.send_message(message.chat.id, "Ссылка некорректна")
        start(message)


def check_subject(checked_subject):
    worksheet, url, df = access_current_sheet()
    return checked_subject in worksheet.col_values(1)


def delete_subject(message):
    """Удаляем предмет в Google-таблице"""
    worksheet, url, df = access_current_sheet()
    deleted_cell = worksheet.find(message.text)
    worksheet.delete_row(deleted_cell.row)

    bot.send_message(message.chat.id, "Предмет удален из таблицы")
    start(message)


def clear_subject_list(message):
    """Удаляем все из Google-таблицы"""
    if message.text == "Да" or message.text == "да":
        worksheet, url, df = access_current_sheet()
        worksheet.delete_rows(2, 20)
        bot.send_message(message.chat.id, "Действие выполнено")
        start(message)

    elif message.text == "Нет" or message.text == "нет":
        bot.send_message(message.chat.id, "Действие отменено")
        start(message)

    else:
        bot.send_message(message.chat.id, "Введена некорректная опция")
        start(message)


def update_subject(message):
    """Получаю новое название предмета и ссылку на его таблицу"""
    subject_new = bot.send_message(message.chat.id, "Введите название предмета и ссылку на таблицу(через пробел)")
    bot.register_next_step_handler(subject_new, _update_subject, message.text)


def _update_subject(message, subject_old):
    """Ввожу полученные данные из прошлой функции"""
    subject_new, table = message.text.split()

    if is_valid_url(table):
        worksheet, url, df = access_current_sheet()
        subject_old_cell = worksheet.find(subject_old)

        worksheet.update_cell(subject_old_cell.row, 1, subject_new)
        worksheet.update_cell(subject_old_cell.row, 2, table)

        bot.send_message(message.chat.id, "Данные успешно обновлены")
        start(message)

    else:
        bot.send_message(message.chat.id, "Введена некорректная ссылка")
        start(message)


@bot.message_handler(commands=["start"])
def start(message):
    start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    try:
        json_file = open("tables.json")
    except FileNotFoundError:
        start_markup.row("Подключить Google-таблицу")
        start_markup.row("Посмотреть дедлайны на этой неделе")
        start_markup.row("Редактировать дедлайн")
        start_markup.row("Редактировать предметы")
    else:
        start_markup.row("Посмотреть дедлайны на этой неделе")
        start_markup.row("Редактировать дедлайн")
        start_markup.row("Редактировать предметы")
    info = bot.send_message(message.chat.id, "Что хотите сделать?", reply_markup=start_markup)
    bot.register_next_step_handler(info, choose_action)


# bot.infinity_polling()
