from project.qld.engine.utils.foundation.date import customCalendar

holidayNameList = [  # note that one entry could correspond to multiple days (Hari Raya Puasa has a few days)
    "New Year's Day",
    "Lunar New Year",
    "Second Day of Lunar New Year",
    "Special Public Holiday",
    "Good Friday",
    "Hari Raya Puasa",
    "Labour Day",
    "Vesak Day",
    "Hari Raya Haji",
    "National Day",
    "Diwali/Deepavali",
    "Christmas Day",
    "Polling"
]

exceptionNameList = []

customCalendar.createCustomCalendar(holidayNameList=holidayNameList, exceptionNameList=exceptionNameList,
                                    calendarName="Singapore")
