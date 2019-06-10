import time
import os
import re
import datetime

import telepot.api
from proxy_funcs import get_proxy

PROXY = get_proxy('proxy_telegram.txt')
print('Proxy: ', PROXY)
telepot.api.set_proxy('https://' + PROXY)

TOKEN = '836566144:AAErfPxlHsr1lZo1WMu5G7CO4u6WR1zmawQ'

import telepot
import telepot.helper
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telepot.delegate import (
    per_chat_id, create_open, pave_event_space, call)

from exercises_info import exercises_info_text

IMAGES_DIR = 'images'

muscles_groups_info = dict()

muscles_groups_exercises = {
        "Legs - Thighs (Quadriceps)":
            ["Leg Press", "Front Squat", "Forward Lunge", "Wide-stance Barbell Squat"],
        "Legs - Back of Thighs (Hamstrings)": 
            ["Stiff-Legged Barbell Deadlift", "Hack Squat",
             "Low Bar Squat", "Barbell Deadlift", "Good Morning"],
        "Legs - calves":
            ["Calf Press On Leg Press Machine ", "Standing Calf Raises", "Squat Leg Raise",
             "Squat Knee Raise", "Seated Calf Raise", "Reverse Calf Raise"],
        "Buttocks": 
            ["Glute Kickback", "One-Legged Cable Kickback", "Pelvic Lift", "Heel Beats"],
        "Back": 
            ["Pull-up", "Chin-up", "Bent Over Barbell Row", "Barbell Shrug", 
             "Rope Straight-Arm Pulldown", "Straight-Arm Dumbbell Pullover"],
        "Chest":
            ["Overhead Press", "Cable Crossover", "Butterfly",
             "Incline Dumbbell Flyes", "Decline Dumbbell Flyes"],
        "Shoulders": 
            ["Handstand Push-Up", "Overhead Press",
             "Incline Bench Press", "Push Press", "Front Dumbbell Raise",
             "Barbell Front Raise", "Side Lateral Raise", "Rear Lateral Raise", 
             "Upright Barbell Row"],
        "Arms - triceps":
            ["Dips Triceps Version", "Barbell Bench Press", "Overhead Press", 
             "Close-Grip Barbell Bench Press", "Reverse Triceps Bench Press",
             "Parallel Bar Dip"],
        "Arms - biceps": 
            ["Chin Ups", "Pull Ups", "Rows", "Barbell Curls", "Hammer Curls",
             "Concentration Curls", "Incline Dumbbell Curl", "Preacher Curls"],
        "Arms - forearms": 
            ["Chin-Up", "Wrist Curls", "Reverse Wrist Curls",
             "Bicep Curls", "Hammer Curls", "Zottman Curls"],
        "Abdominals":
            ["Chin Up", "Overhead Press", "Ab Roller", "Cable Crunch", 
             "Sit Up", "Hanging Leg Raise", "Plank"]
        }

    

muscle_groups = ["Legs - Thighs (Quadriceps)",
                "Legs - Back of Thighs (Hamstrings)",
                "Legs - calves",
                "Buttocks",
                "Back",
                "Chest",
                "Shoulders",
                "Arms - forearms",
                "Arms - biceps",
                "Arms - triceps",
                "Abdominals"]

class ExercisesBot(telepot.helper.ChatHandler):
    def __init__(self, seed_tuple, include_callback_query=True, **kwargs):
        super().__init__(seed_tuple=seed_tuple, include_callback_query=True, **kwargs)
        self.tg_commands = {}  # команды (начинаются с /)
        self.add_command("/start", self.start_bot)
        self.notification_end_datetime = None
        self.next_notification_datetime = None
        self.exercise_for_notifications = None
        
    def parse_cmd(self, cmd_string):
        text_split = cmd_string.split()
        return text_split[0], text_split[1:]
    
    def add_command(self, cmd, func):
        self.tg_commands[cmd] = func
    
    def remove_command(self, cmd):
        del self.tg_commands[cmd]

    def start_bot(self, chat_id, params):
        values_in_row = 2
        muscle_groups_for_keyboard = [muscle_groups[i:i+values_in_row] for i in range(0, len(muscle_groups), values_in_row)]
        keyboard = ReplyKeyboardMarkup(keyboard=muscle_groups_for_keyboard)
        self.step = 'choose_muscles_group'
        self.sender.sendMessage(
            "Choose muscle group",
            reply_markup=keyboard
            )

    def send_muscles_group_info(self, muscles_group):
        info = muscles_groups_info[muscles_group]
        self.sender.sendMessage(info, reply_markup=ReplyKeyboardRemove())

    def send_exercises(self, muscles_group):
        send_str = f'Exercises for {muscles_group}:\n'
        for exercise in muscles_groups_exercises[muscles_group]:
            exercise_command = '/exercise\\_' + '\\_'.join(exercise.lower().split(' '))
            print(exercise_command)
            send_str += exercise + ' ' + exercise_command + '\n'
        self.sender.sendMessage(send_str, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

    def send_exercise_info(self, exercise):
        send_str = exercises_info_text.get(exercise, None)
        if send_str is None:
            self.sender.sendMessage('Exercise not found', parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
            return
        
        def filter_exercises_images(filename, exercise):
            return re.search('^%s' % exercise, filename) is not None
        exercises_images = list(filter(lambda filename: filter_exercises_images(filename, exercise), os.listdir(IMAGES_DIR)))

        for imagename in exercises_images:
            print(imagename)
            img_path = os.path.join(IMAGES_DIR, imagename)
            with open(img_path, 'rb') as f:
                img = f
                self.sender.sendPhoto(('image.jpg', img))
        self.step = 'send_exercise_info'
        self.current_exercise = exercise
        keyboard = ReplyKeyboardMarkup(keyboard=[['Set notification']])
        self.sender.sendMessage(send_str, parse_mode="Markdown", reply_markup=keyboard)

    def on_chat_message(self, message):
        content_type, chat_type, chat_id = telepot.glance(message)
    
        if content_type == "text":
            msg_text = message['text']
            chat_id = message['chat']['id']
            
            # выводим входящие сообщения
            print("[MSG] {uid} : {msg}".format(uid=message['from']['id'], msg=msg_text))
    
            if msg_text[0] == '/':
                # если начинается с /, то команда
                cmd, params = self.parse_cmd(msg_text)
                print(cmd)
                if cmd.startswith('/exercise'):
                    exercise = cmd.replace('/exercise_', '')
                    self.send_exercise_info(exercise)
                    return
                try:
                    self.tg_commands[cmd](chat_id, params)
                except KeyError:
                    self.sender.sendMessage("Unknown command: {cmd}".format(cmd=cmd))
               
            #  когда пользователь нажимает на кнопки в keyboard,
            #  в зависимости от текущего шага вызываем функцию
            elif self.step == 'choose_muscles_group':
                muscles_group = msg_text
                #self.send_muscles_group_info(muscles_group)
                self.send_exercises(muscles_group)
            elif self.step == 'send_exercise_info':
                if msg_text == 'Set notification':
                    self.set_notification(self.current_exercise)
        
    def set_notification(self, exercise):
        exercise_unformatted = exercise.replace('_', ' ').capitalize()
        
        self.bot._scheduler.event_later(10, lambda: self.send_notificaton(exercise_unformatted))
        
        for i in range(1, 8):
            self.bot._scheduler.event_later(i*60*60*24, lambda: self.send_notificaton(exercise_unformatted))

    def send_notificaton(self, exercise):
        self.sender.sendMessage("Notification about exercise {0}".format(exercise))



    '''
    def set_notification(self, exercise):
        exercise_unformatted = exercise.replace('_', ' ').capitalize()
        self.exercise_for_notifications = exercise_unformatted
        now = datetime.datetime.now()
        self.next_notification_datetime = now + datetime.timedelta(days=1)
        self.notification_end_datetime = now + datetime.timedelta(days=7)
        
    def check_notification(self):
        print('check_notification')
        now = datetime.datetime.now()
        if self.exercise_for_notifications is not None:
            if now > self.next_notification_datetime and now < self.notification_end_datetime:
                self.sender.sendMessage("Notification about exercise {0}".format(self.exercise_for_notifications))
            if now > self.notification_end_datetime:
                self.notification_end_datetime = None
                self.next_notification_datetime = None
                self.exercise_for_notifications = None
        time.sleep(2)
        #self.check_notification()
    '''
            
def shit():
    print('shit')
    time.sleep(2)
    shit()
     
bot = telepot.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(), create_open, ExercisesBot, timeout=1000000000000000000),
])

MessageLoop(bot).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(2)