from project.qld.engine.utils.foundation.date import customCalendar

holidayNameList = [  # note that one entry could correspond to multiple days (Hari Raya Puasa has a few days)
    "New Year's Day",
    "Lunar New Year",
    "Second Day of Lunar New Year",
    "Federal Territory Day",
    "Thaipusam",
    "Nuzul Al-Quran",
    "Special Public Holiday",
    "Hari Raya Puasa",
    "Labour Day",
    "Wesak Day",
    "The Yang di-Pertuan Agong's Birthday",
    "Hari Raya Haji",
    "Muharram/New Year",
    "Malaysia's National Day",
    "Malaysia Day",
    "The Prophet Muhammad's Birthday",
    "Diwali/Deepavali",
    "Christmas Day",
    "Election"
]

exceptionNameList = [
    "Hari Raya Haji (Day 2)"
]

customCalendar.createCustomCalendar(holidayNameList=holidayNameList, exceptionNameList=exceptionNameList,
                                    calendarName="Malaysia")
