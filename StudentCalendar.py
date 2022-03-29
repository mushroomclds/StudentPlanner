from __future__ import print_function
import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
###############################################################
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os.path
from datetime import datetime
from datetime import timedelta
####################################################################
# kivy imports
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.button import Button
###############################################################
listTitles = []  # global variables to share blackboard information
listDay = []
listTime = []
listClass = []


# ------------------------------Blackboard Navigation & Scraping------------------------------------------------
def BBEvents(user, password):
    chrome_options = webdriver.ChromeOptions()  # options for chrome driver

    chrome_options.add_experimental_option("detach", True)  # make chrome always open
    driver = webdriver.Chrome(ChromeDriverManager().install()
                              , options=chrome_options)  # driver, download and open chrome driver

    driver.get("https://utsa.blackboard.com")  # open link
    # print(driver.page_source)
    wait = WebDriverWait(driver, 10)
    wait0 = wait.until(lambda d: d.find_element(By.NAME, "j_username"))

    search = driver.find_element(By.NAME, "j_username")  # search for username text box
    search.send_keys(user)
    search = driver.find_element(By.NAME, "j_password")
    search.send_keys(password)
    search.send_keys(Keys.RETURN)
    time.sleep(6)  # sleep, wait for blackboard to load main page
    textCheck = driver.page_source
    if not textCheck.find("password") == -1:  # if password is inocorrect, will close chrome driver after 6 seconds
        driver.quit()
        return 0
    wait1 = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Calendar")))
    driver.find_element(By.LINK_TEXT, "Calendar").click()
    # time.sleep(5)
    wait2 = wait.until(EC.element_to_be_clickable((By.ID, "bb-calendar1-deadline")))
    driver.find_element(By.ID, "bb-calendar1-deadline").click()
    # time.sleep(5)
    wait3 = wait.until(lambda d: d.find_element(By.CLASS_NAME, "name"))  # wait till element present before continuing
    text = driver.find_element(By.CLASS_NAME, "deadlines")  # find info needed for assignments
    info = text.find_elements(By.CLASS_NAME, "name")
    info2 = text.find_elements(By.CLASS_NAME, "content")

    for i in range(len(info)):  # loop through html code and info manipulation
        listTitles.append(info[i].text)
        indexComma = info2[i].text.find(',')
        indexColon1 = info2[i].text.find(':')
        indexColon2 = info2[i].text.find(':', indexColon1 + 1)
        indexColon3 = info2[i].text.find(':', indexColon2 + 1)
        listDay.append(info2[i].text[10:indexComma])
        listTime.append(info2[i].text[indexComma + 2:indexComma + 10])  # adding to global lists of info
        listClass.append(info2[i].text[indexColon3 + 2:])
        print(listTitles[i])
        print(listDay[i])
        print(listTime[i])
        print(listClass[i] + "\n")

    driver.quit()  # close chrome driver


# ------------------------------GOOGLE CALENDAR API-------------------------------------------------------------
SCOPES = ['https://www.googleapis.com/auth/calendar']

def googleAPI(title, course, date, desciption, attendees):
    newTitle = title + " " + course
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)  # main function to call calendar API

    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=30, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    if not events:
        print('No upcoming events found.')

    for event in events:  # check if assignment is present in calendar
        check = event['summary']
        if check == newTitle:
            print("Event already present: ", check)
            return 0
    event = {
        'summary': newTitle,  # enter assignment title
        'description': desciption,
        'start': {
            'dateTime': date,  # same start and end time and day
            'timeZone': 'America/Chicago',
        },
        'end': {
            'dateTime': date,
            'timeZone': 'America/Chicago',
        },
        # 'attendees': [
        #     {'email': attendees },
        #     # {'email': None},
        #     # {'email': attendees[1]},# allows for one attendee to get event invite via email
        # ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},  # email reminder 1 day before event
                {'method': 'popup', 'minutes': 30},  # phone or desktop reminder 30 min before event
            ],
        },
    }
    # event[1] = "d"
    if attendees != None:  # this is for BB, where no attendees, removes from dict^
        # event.pop('attendees', None)
        attendeesDict = {'attendees': [
            {'email': attendees },],}
        event.update(attendeesDict)
        if len(attendees) == 2:
            updateDict = {'attendees': [{'email': attendees}, {'email': attendees[1]}, ]}
            event.update(updateDict)
        if len(attendees) == 3:
            updateDict = {'attendees': [{'email': attendees}, {'email': attendees[1]},{'email': attendees[2]}, ]}
            event.update(updateDict)

    service.events().insert(calendarId='primary', body=event).execute()  # add event to Google Calendar


# ------------------------------KIVY GUI ---------------------------------------------------------------------
class MyGridLayout(GridLayout):  # The MyGridLayout class inherits the GridLayout class
    username = ""
    password = ""

    def __init__(self, **kwargs):
        super(MyGridLayout, self).__init__(**kwargs)  # Call the grid layout constructor

        self.cols = 1

        # Header, columns
        self.topGrid = GridLayout()
        self.topGrid.cols = 4
        self.add_widget(self.topGrid)  # Add the new top grid to the app
        Button.background_normal = ""

        Button.background_color = [.89, 0.53, .2, 1]
        # Create an 'Add Event' button (1st column in top grid)
        self.addEvent = Button(text='Add Event', font_size=22)
        self.addEvent.bind(on_press=self.pressAddEvent)  # Bind the add event button to make it do something
        self.topGrid.add_widget(self.addEvent)  # adding it to the topgrid, entire thing.

        self.addBlackboard = Button(text='Login to BB', font_size=22)  # creating variable of class button
        self.addBlackboard.bind(on_press=self.pressBB)
        self.topGrid.add_widget(self.addBlackboard)  # Add variable to widgets

        # Create a 'Calendar View' button
        self.calendarView = Button(text='Calendar View')
        self.calendarView.bind(on_press=self.pressCalendar1)  # Bind the calendar view button
        self.topGrid.add_widget(self.calendarView)

        # Add widgets to the bottom grid. Should be a list of the events
        self.add_widget(Label(text='Assignments Due: '))
        self.now = datetime.now()

        # Schedule the self.update_clock function to be called once a second
        Clock.schedule_interval(self.update_clock, 1)
        self.my_label = Label(text=self.now.strftime('%H:%M:%S'))
        self.topGrid.add_widget(self.my_label)

    def update_clock(self, *args):
        # Called once a second using the kivy.clock module
        # Add one second to the current time and display it on the label
        self.now = self.now + timedelta(seconds=1)
        self.my_label.text = self.now.strftime('%H:%M:%S')

    # creates the functionality for the 'log into bb' button
    def pressBB(self, instance):

        layout = GridLayout(cols=2, padding=10)

        closeButton = Button(text="Close the pop-up")
        layout.add_widget(closeButton)
        submit = Button(text='Submit')
        layout.add_widget(submit)

        layout.add_widget(Label(text='User Name'))
        self.username = TextInput(multiline=False)
        layout.add_widget(self.username)

        layout.add_widget(Label(text='password'))
        self.password = TextInput(password=True, multiline=False)
        layout.add_widget(self.password)
        # Instantiate the modal popup and display
        popup = Popup(title='Blackboard Login', #creates popup window
                      content=layout)
        popup.open()
        # Attach close button press with popup.dismiss action
        submit.bind(on_press=self.submitBB)  # Bind the calendar view button
        closeButton.bind(on_press=popup.dismiss)

    def submitBB(self, instance):

        BBEvents(self.username.text, self.password.text) #call BBevents function at beginning with input credentials
        for i in range(len(listTitles)):
            info = listTitles[i] + '\n' + listDay[i] + ' ' + listTime[i] + ' ' + listClass[i]
            self.add_widget(Label(text=info)) #add event to GUI front page

        def convert_to_RFC_datetime(year, month, day, hour, minute): #takes date info and formats it
            dt = datetime(year, month, day, hour, minute, 0).isoformat()
            return dt

        for i in range(len(listTitles)): #uses BB info and slices info accordingly
            indexHyphen = listClass[i].find('-')
            course = listClass[i][indexHyphen + 1:indexHyphen + 5]
            indexSlash = listDay[i].find("/")
            indexSlash2 = listDay[i].find("/", indexSlash + 1)
            month = listDay[i][:indexSlash]
            day = listDay[i][indexSlash + 1:indexSlash2]
            year = "20" + str(listDay[i][indexSlash2 + 1:])
            indexColon = listTime[i].find(':')
            hour = listTime[i][:indexColon]
            minute = listTime[i][indexColon + 1:indexColon + 3]
            print('listTIme: ' + listTime[i])
            indexTimeFormat = listTime[i].find('M')
            format = listTime[i][indexTimeFormat - 1:indexTimeFormat + 1]

            if format == "PM": #if afternoon event, adds 12 to convert to 24 hour format
                hour = int(hour) + 12
            dateConvert = convert_to_RFC_datetime(int(year), int(month), int(day), int(hour), int(minute))
            description = listClass[i] + "\n" + listTitles[i] + "\n" + listTime[i]
            print(course, month, day, year, hour, minute, end=" ")
            # print(description)
            # print(dateConvert)
            # print(dateStart)
            # attendees = []
            googleAPI(listTitles[i], course, dateConvert,
                      description, attendees=None) #call google cal api to add events

    def pressAddEvent(self, instance): # creates the functionality for the 'add event' function

        layout = GridLayout(cols=2, padding=10)

        closeButton = Button(text="Close the pop-up")
        layout.add_widget(closeButton)  # location [0, 0]
        submit = Button(text='Submit')
        layout.add_widget(submit)  # location [1, 0]

        layout.add_widget(Label(text='Event Title'))  # [0, 1]
        self.title = TextInput(multiline=False)
        layout.add_widget(self.title)  # [1, 1]
        # choose day
        layout.add_widget(Label(text='Day'))  # [0, 2]
        self.day = TextInput(multiline=False)
        layout.add_widget(self.day)  # [1, 2]
        # month
        layout.add_widget(Label(text='Month'))  # [0, 3]
        self.month = TextInput(multiline=False)
        layout.add_widget(self.month)  # [1, 3]
        # year
        layout.add_widget(Label(text='Year'))  # [0, 4]
        self.year = TextInput(multiline=False)
        layout.add_widget(self.year)  # [1, 4]
        # hour
        layout.add_widget(Label(text='Hour'))  # [0, 5]
        self.hour = TextInput(multiline=False)
        layout.add_widget(self.hour)  # [1, 5]
        # minute
        layout.add_widget(Label(text='Minute'))  # [0, 6]
        self.minute = TextInput(multiline=False)
        layout.add_widget(self.minute)  # [1, 6]
        # email
        layout.add_widget(Label(text='Attendees Emails'))
        self.attendees = TextInput(multiline=True)
        layout.add_widget(self.attendees)
        # description
        layout.add_widget(Label(text='Description'))
        self.description = TextInput(multiline=True)
        layout.add_widget(self.description)

        popup = Popup(title='Add Event',# Instantiate the model popup and display
                      content=layout)
        popup.open()

        # Attach close button press with popup.dismiss action
        submit.bind(on_press=self.submitEvent)  # Bind the calendar view button
        closeButton.bind(on_press=popup.dismiss)

    def submitEvent(self, instance): #manually add event button function
        title = self.title.text
        day = self.day.text
        month = self.month.text
        year = self.year.text
        hour = self.hour.text
        minute = self.minute.text
        email = self.attendees.text
        description = self.description.text
        # Print to the screen
        listAttendees = email.split("\n")
        print(listAttendees)
        if len(listAttendees[0]) == 0:
            listAttendees = None
        def convert_to_RFC_datetime(year, month, day, hour, minute):
            dt = datetime(year, month, day, hour, minute, 0).isoformat()
            return dt

        dateConvert = convert_to_RFC_datetime(int(year), int(month), int(day), int(hour), int(minute))
        googleAPI(title=title, course="", date=dateConvert, desciption=description, attendees=listAttendees)
        self.add_widget((Label(text=f'{title + " " + month + "/" + day + "/" + year + " " + hour + ":" + minute}')))

        # Clear the input boxes
        self.title.text = ''
        self.day.text = ''
        self.month.text = ''
        self.year.text = ''
        self.hour.text = ''
        self.minute.text = ''
        self.attendees.text = ''
        self.description.text = ''



    def pressCalendar1(self, instance): #opens monthly view
        layout = GridLayout(cols=2, padding=10)

        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        for i in range(12):
            # i = i + 1
            month = months[i]
            self.monthButton = Button(text=month)
            self.monthButton.bind(on_press=self.pressCalendar2)

            layout.add_widget(self.monthButton)
            # if monthButton.text == "january":
            #     print("yes")
            # print(self.monthButton.text)
        closeButton = Button(text="Close the pop-up")
        layout.add_widget(closeButton)

        popup = Popup(title='Calendar View',
                      content=layout)
        popup.open()
        closeButton.bind(on_press=popup.dismiss)

    def pressCalendar2(self, instance): #opens month from monthly view^ and shows gui of events per day
        layout = GridLayout(cols=7, padding=10)
        courseList = []
        monthList = []
        dayList = []
        for counter in range(len(listTitles)):
            indexHyphen = listClass[counter].find('-')
            course = listClass[counter][indexHyphen + 1:indexHyphen + 5]
            indexSlash = listDay[counter].find("/")
            indexSlash2 = listDay[counter].find("/", indexSlash + 1)
            month = listDay[counter][:indexSlash]
            day = listDay[counter][indexSlash + 1:indexSlash2]
            courseList.append(course)
            monthList.append(month)
            dayList.append(day)
        for i in range(len(monthList)):
            print(courseList[i], monthList[i], dayList[i], end=" ")

        for i in range(31): #add numbers of days
            i += 1
            string = str(i) + " "
            for counter in range(len(listTitles)): #all events for day concatencated
                if int(dayList[counter]) == i:
                    # dayCalendar = str(i)
                    if len(listTitles[counter]) > 25:
                        newLine = listTitles[counter][25:]
                        newString = listTitles[counter][:25] + "\n" + newLine
                        string = string + "\n" + courseList[counter] + " " + newString

                    else:
                        string = string + "\n" + courseList[counter] + " " + listTitles[counter]

            layout.add_widget(Label(text=string))  # info for day assignments

        closeButton = Button(text="Close the pop-up")
        layout.add_widget(closeButton)

        popup = Popup(title='Calendar View',
                      content=layout)
        popup.open()
        closeButton.bind(on_press=popup.dismiss)

class MyApp(App):# The MyApp class inherits the App class
    def build(self):
        Window.clearcolor = (.031, .054, .172, 1)
        return MyGridLayout()

if __name__ == "__main__": #main function calls GUI and other functions
    MyApp().run()
