#!/usr/bin/python3

import datetime, pickle, sys, os
from pathlib import Path


# if running script for the first time
# gather all necessary garbage
def first_run():
	import re	# RegEx

	print("Initial setup started...\n")
	print("When was your last garbage day?")
	if sys.stdout.isatty() is True:
		while True:
			while True:

				day = input('Type "Today", "Tomorrow", "Yesterday" or MM-DD (Month-Day)\nEnter: ').lower()
				match = re.search("^([0][1-9]|[1][0-2])-([0][1-9]|[1-2][0-9]|[3][0-1])$", day)
				
				if'tod' in day:
					day = datetime.date.today()
					break

				elif 'tom' in day:
					day = datetime.date.today() + datetime.timedelta(days=1)
					break

				elif 'yes' in day:
					day = datetime.date.today() - datetime.timedelta(days=1)
					break

				elif match is not None:
					day = day.split("-")
					day[0] = int(day[0])
					day[1] = int(day[1])
					day = datetime.date(int(datetime.date.today().strftime("%Y")), day[0], day[1])
					break

				else:
					print("\tWrong entry: "+day+"\n\tPlease try again\n")

			if 'y' in input("Is "+day.strftime("%A, %b-%d")+" correct? (yes/no) ").lower():
				break

			else:
				print("\tThen please try again\n")

		while True:		
			garbage_type = input("Was it Recycle Only? or both Recycle & Waste?\nType 'waste' or 'both': ").lower()

			if 'both' in garbage_type:
				garbage_type = 'Both Recycle & Waste'
				break

			elif 'was' in garbage_type:
				garbage_type = 'Waste Only'
				break

			else:
				print("\tWrong entry: "+garbage_type+"\n\tPlease try again\n")

		sender = input('Send email notifications from?: ')
		password = input('Password: ')
		receiver = input('Recipient: ')

		garbage = {
			"day": day,
			"type": garbage_type,
			"sender": sender,
			"password": password,
			"receiver": receiver 
		}

		configFile = str(Path.home())+'/GarbageReminder/trash_data.pkl'
		os.makedirs(os.path.dirname(configFile), exist_ok=True)

		with open(configFile, 'wb') as file:
			pickle.dump(garbage, file)

		return garbage

	else:
		print('Interactive shell not found')
		return None


# check if garbage data exists
def initialize(api=False):
	try:
		configFile = str(Path.home())+'/GarbageReminder/trash_data.pkl'
		with open(configFile, 'rb') as file:
			return pickle.load(file)
	except:
		print('No datafile found')
		if api:
			return None
		else:
			return first_run()


# notify user about current email
def send_email(garbage, msg):
	import smtplib, ssl

	port = 465  # For SSL
	smtp_server = "smtp.gmail.com"
	sender_email = garbage['sender']  # Enter your address
	receiver_email = garbage['receiver']  # Enter receiver address
	password = garbage['password']
	if 'Subject:' in msg:
		message = msg
	else:
		message = "Subject: Garbage Notification\n\n"+msg

	context = ssl.create_default_context()
	with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
		server.login(sender_email, password)
		server.sendmail(sender_email, receiver_email, message)

# check if garbage day
def check_garbage_day(garbage, api=False):
	today = datetime.date.today()

	# update year if changed (prevent calc error of 52 weeks/year)
	year_diff = today.year - garbage['day'].year
	if year_diff > 0:
		garbage['day'] = garbage['day'] + datetime.timedelta(weeks=52*year_diff)

	# update garbage DAY based on weeks past since last
	delta_weeks = today.isocalendar()[1] - garbage['day'].isocalendar()[1]
	garbage['day'] = garbage['day'] + datetime.timedelta(weeks=delta_weeks)

	# update garbage TYPE based on odd/even weeks past
	score = delta_weeks % 2
	if score >= 1:	# change (no change if < 1)
		if garbage['type'] == 'Both Recycle & Waste':
			garbage['type'] = 'Waste Only'
		else:
			garbage['type'] = 'Both Recycle & Waste'

	# variable to return
	if api:
		api_return = {}
	else:
		msg = ""

	# if today
	if garbage['day'] == today:
		if api:
			api_return['date'] = garbage['day']
			api_return['type'] = garbage['type']
		else:
			msg = "Today: "+garbage['type']

	# if tomorrow
	elif garbage['day'] == today + datetime.timedelta(days=1):
		if api:
			api_return['date'] = garbage['day']
			api_return['type'] = garbage['type']
		else:
			msg = "Tomorrow: "+garbage['type']

	# if not today or tomorrow
	else:
		if garbage['day'] > today:
			if api:
				api_return['date'] = garbage['day']
				api_return['type'] = garbage['type']
			else:
				msg = "Next garbage day is: "+garbage['day'].strftime("%A, %B %d, %Y")+"\n"
				msg += garbage['type']

		else:
			next_garbage_day = garbage['day'] + datetime.timedelta(weeks=1)
			if api:
				api_return['date'] = next_garbage_day
			else:
				msg = "Next garbage day is: "+next_garbage_day.strftime("%A, %B %d, %Y")+"\n"

			# find NEXT garbage day TYPE
			if garbage['type'] == 'Waste Only':
				if api:
					api_return['type'] = 'Both Recycle & Waste'
				else:
					msg += 'Both Recycle & Waste'
			else:
				if api:
					api_return['type'] = 'Waste Only'
				else:
					msg += 'Waste Only'

	# return here
	if api:
		return api_return
	else:
		return msg


# NOT USING (UNDER TESTING)
# function to check if desktop enviroment is present
# def is_desktop():
    
# 	# The command you want to execute   
# 	cmd = 'echo'
# 	temp = subprocess.Popen([cmd, '$DESKTOP_SESSION'], stdout = subprocess.PIPE)
# 	output = str(temp.communicate())
# 	print(output)
# 	# return output


# run
# is_desktop()
if __name__ == '__main__':
	garbage = initialize()
	if garbage is not None:
		msg = check_garbage_day(garbage)
		if sys.stdout.isatty() is True:
			try:
				import PySimpleGUI as sg
				print(msg)
				layout = [[sg.Text(msg)], [sg.Button("OK")]]
				window = sg.Window("Garbage Day Reminder", layout)
				# Create an event loop
				while True:
					event, values = window.read()
					# End program if user closes window or
					# presses the OK button
					if event == "OK" or event == sg.WIN_CLOSED:
						break
				window.close()
			except ModuleNotFoundError:
				print(msg)
		else:
			send_email(garbage, msg)
