#!/usr/bin/env python
# -*- coding: utf-8 -*-
import telebot, time, json, gdata # Библиотека для работы с Telegram Bot API, Со временем, с JSON, скрипт для работы с JSON файлом "data.json"
from multiprocessing import Process, freeze_support # библиотека для работы с процессами, многозадачностью
from datetime import datetime # библиотека для работы с датой и временем

TOKEN = "paste your token" # обозначения токена бота

# groupid : [status, votingstatus, votingpoll, [time1, time2], votingresult] - шаблон хранения данных в "data.json"
bot = telebot.TeleBot(TOKEN) # инициализация бота

# Обозначение Временных шаблонов:
global timeStamp
timeStamp = "%H:%M %d.%m.%Y"
tm = "%M"
tstam = "%H"
tstamd = "%d"
# ------------------------------

TZ = 0 # Временной сдвиг (в часах)
WAIT_TIME = 600 # время для голосования (в секундах)

def nowtime(): # функция для определения текущего времени с учетом временного сдвига. Выводимы объект класса datetime.datetime
	temp = int(datetime.today().strftime(tstam))+TZ
	if temp > 23:
		temp -= 24
		return (datetime.today()).replace(hour=temp, day=int(datetime.today().strftime(tstamd))+1)
	return (datetime.today()).replace(hour=temp)

def check_send_messages():
	while True:
		dictt = gdata.load() # считывание данных с файла "data.json"

		for i in dictt: # проход по всем группам в базе бота
			try: # начальная точка для ловли TypeError ошибки, во избежания неладок с NoneType
				if time.time() - dictt[i][5] >= WAIT_TIME: # проверка прошедшего времени с начала голосования
					poll = bot.stop_poll(i, dictt[i][2]) # остановка голосования если прошло необходимое время
					dictt[i][5] = 9999999999999 # сброс таймера голосования

					if dictt[i][1] and not(dictt[i][4]):
						# выгрузка результатов голосования:
						options = poll.options
						yes_votes_count = options[0].voter_count
						no_votes_count = options[1].voter_count
						# --------------------------------
						if yes_votes_count > no_votes_count:
							dictt[i][4] = True
							bot.send_message(i, "✔️*Голосование закончено.*✔️\n✅Комендантский час начнется в `"+str(dictt[i][3][0])+"` и закончится в `"+str(dictt[i][3][1])+"`.✅", reply_to_message_id=dictt[i][2], parse_mode="Markdown")
							dictt[i][1] = True
						else:
							bot.send_message(i, "✔️*Голосование закончено.*✔️\n❌Комендантский час _не будет начат_❌", reply_to_message_id=dictt[i][2], parse_mode="Markdown")
							# сброс контрольных данных голосования:
							dictt[i][3] = None
							dictt[i][1] = False
							# ------------------------------------
						dictt[i][2] = None # сброс контрольных данных голосования
						
					gdata.update(dictt) # загрузка данных в "data.json"
			
				dictt = gdata.load()
				if dictt[i][4]:
					# загрузка времени и перевод в обьект класса datetime.datetime:
					start_time_RAW = dictt[i][3][0] 
					start_time = datetime.strptime(start_time_RAW, timeStamp)
					# ------------------------------------------------------------
					if nowtime() >= start_time:
						dictt[i][0] = True
						dictt[i][1] = False
						dictt[i][4] = None
						bot.send_message(i, "⛔️*Комендантский час начат!*⛔️\n🔜Он продлится до `"+str(dictt[i][3][1])+"`.", parse_mode="Markdown")
					gdata.update(dictt)
				if dictt[i][0]:
					end_time_RAW = dictt[i][3][1]
					end_time = datetime.strptime(end_time_RAW, timeStamp)
					if nowtime() >= end_time:
						dictt[i][0] = False
						dictt[i][1] = False
						dictt[i][2] = None
						dictt[i][3] = None
						dictt[i][4] = False
						bot.send_message(i, "*Комендантский час окончен!*\n 🔙     🔙     🔙     🔙     🔙     🔙", parse_mode="Markdown")
					gdata.update(dictt)
			except TypeError: # Вылов TypeError в случае если контрольные данные еще не успели обновиться
				pass
	
		time.sleep(10) # Задержка процесса для уменьшения загруженности


if __name__ == "__main__": # Проверка на исполняемость кода именно главным файлом, нужна для многозадачности
	@bot.message_handler(func=lambda message: message.chat.type in ["group", "supergroup"], commands=['curfew']) # Вылов команды /curfew
	def echo(message):
		dictt = gdata.load()
		chatid = str(message.chat.id) # вынесение id чата в отдельную переменную
		if not(chatid in dictt):
			dictt.update({chatid:[False, False, None, None, False, 999999999999999]}) # занесение группы в базу бота если ее там нет
		if dictt[chatid][0]:
			bot.delete_message(message.chat.id, message.message_id) # удаление сообщения если идет комендантский час
		else:
			if not(dictt[chatid][0]):
				if dictt[chatid][1] or dictt[chatid][4]: 
					markup = telebot.types.InlineKeyboardMarkup() # инициализация markup'а для создания inline кнопок
					if not(dictt[chatid][4]):
						btn = telebot.types.InlineKeyboardButton("Показать", url="t.me/c/"+str(chatid[4:])+"/"+str(dictt[chatid][2])) # создание кнопки и указание url сообщения с голосованием 
						markup.row(btn) # расстановка копок по рядам для вывода. В данном случае одной кнопки в единственный ряд.
						bot.reply_to(message, "❌*Голосование на начало комендантского часа уже создано!*❌", reply_markup=markup, parse_mode="Markdown")
					else:
						bot.reply_to(message, "🔒*Комендантский час начнется в* `"+str(dictt[chatid][3][0])+"`.🔒", parse_mode="Markdown")
				else:
					msg = bot.reply_to(message, "*Введите время начала и конца комендантского часа.*🕐\nФормат:\n`HH:MM DD.MM.YYYY` - `HH:MM DD.MM.YYYY`", parse_mode="Markdown")
					bot.register_next_step_handler(msg, add_date) # вылов ответного сообщения пользователя. Указывается сообщение, на которое надо ответить и функция, исполняемая при ответе
		gdata.update(dictt)

	# Функция удаления сообщения, если комендантский час идет (status = True):
	@bot.message_handler(content_types=['text', 'audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'location', 'contact', 'new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo', 'delete_chat_photo', 'group_chat_created', 'supergroup_chat_created', 'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id', 'pinned_message'], func=lambda message: True)
	def delete_mess(message):
		chatid = str(message.chat.id)
		dictt = gdata.load()
		if not(chatid in dictt):
			dictt.update({chatid:[False, False, None, None, False, 999999999999999]})
		if dictt[chatid][0]:
			bot.delete_message(message.chat.id, message.message_id)
	# -----------------------------------------------------------------------

	# Функция, исполняемая при вводе времени комчаса. Она инициализирует голосование на комендантский час:
	def add_date(message):
		try:
			# отделение и запись в отдельные переменные времена начала и конца комчаса:
			arr = list(map(str, message.text.split(" - "))) 
			time1 = datetime.strptime(arr[0], timeStamp).strftime(timeStamp)
			time2 = datetime.strptime(arr[1], timeStamp).strftime(timeStamp)
			# ------------------------------------------------------------------------
			dictt = gdata.load()
			chatid = str(message.chat.id)
			dictt[chatid][3] = [time1, time2] # сохранение дат начала и конца комчаса
			dictt[chatid][1] = True 
			poll = telebot.types.Poll("🛡Включить ли комендантский час с "+str(time1)+" по "+str(time2)+"?🛡") # создание объекта класса Poll
			# Добавление вариантов ответа в poll:
			poll.add("Да")
			poll.add("Нет")
			# ----------------------------------
			dictt[chatid][2] = str(bot.send_poll(chatid, poll).message_id) # отправка poll в группу и сохранение message_id отправленного голосования
			dictt[chatid][5] = time.time() # сохранение времени отправки для будущего определения конца голосования
			gdata.update(dictt)
		except: # вылов ValueError, в случае если пользователь ввел время не по формату.
			bot.reply_to(message, "❌*Неверный формат времени.*❌", parse_mode="Markdown") # Вывод ошибки пользователю
	# ---------------------------------------------------------------------------------------------------


	freeze_support() # функция, необходимая для работы мультипроцессинга
	p1 = Process(target=check_send_messages, args=()) # инициализация процесса функции check_send_messages
	p1.start() # запуск процесса p1

	while True:
		try:
			bot.polling(none_stop=True) # запуск бота, с аргументом none_stop=True, т.е. бот не будет крашится при ошибке от telegram API
		# вылов критической ошибки telegram API и задержка 15 секунд, воизбежание недоступности серверов:
		except Exception as e: 
			if e == KeyboardInterrupt: # вылов вмешательства в консоли и выключение скрипта
				break
			print(e) # вывод ошибки
			time.sleep(15)
		# ----------------------------------------------------------------------------------------------