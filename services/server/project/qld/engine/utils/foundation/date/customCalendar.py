from selenium import webdriver
from selenium.webdriver.common.by import By
from project.qld.engine.utils.foundation.date import date_utils as du
from datetime import datetime as dt
# https://www.timeanddate.com/holidays/malaysia/2022?hol=4194307


def createCustomCalendar(startYear=2020, endYear=2070,
                         holidayNameList=[], exceptionNameList=[], calendarName=""):
    monthDic = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

    calendarNameLowerCase = calendarName.lower()
    calendarNumber = {
        "singapore": 63,
        "malaysia": 69
    }

    dates = []
    datesStr = []
    holidayDetails = []
    allHolidayDetails = []

    driver = webdriver.Chrome()

    for year in range(startYear, endYear+1):
        driver.get("https://www.timeanddate.com/calendar/?year=" + str(year) + "&country=" + str(calendarNumber[calendarNameLowerCase]))
        table = driver.find_element(By.ID, "ch1")
        holidays = table.find_elements(By.TAG_NAME, "tr")
        for i, holiday in enumerate(holidays):
            if i > 0:
                cols = holiday.find_elements(By.TAG_NAME, "td")
                if len(cols) == 2:
                    dayMonthStr = cols[0].text
                    dayStr, monthStr = dayMonthStr.split(" ")
                    pythonDatetime = dt(year, monthDic[monthStr], int(dayStr))
                    dateSerial = du.pythonDateTime2ExcelSerial(pythonDatetime)
                    holidayDetail = cols[1].text

        #            allHolidayDetails.append(holidayDetail)
                    for holiday in holidayNameList:
                        if holiday in holidayDetail:
                            if any(exception in holidayDetail for exception in exceptionNameList):
                                break
                            dates.append(dateSerial)
                            datesStr.append(pythonDatetime.strftime("%d/%b/%Y"))
                            holidayDetails.append(holidayDetail)
                            break

    driver.close()

    with open("./foundation/date/calendarInc/" + calendarNameLowerCase + "Calendar.inc", 'w') as f:
        f.write("namespace QLD {\n")
        f.write("	int " + calendarName + "Calendar::holidays[] = {\n")
        for i in range(len(dates)-1):
            f.write("		" + str(dates[i]) + ", // " + datesStr[i] + ", " + holidayDetails[i] + "\n")
        i = len(dates)-1
        f.write("		" + str(dates[i]) + " // " + datesStr[i] + ", " + holidayDetails[i] + "\n")
        f.write("	};\n")
        f.write("}\n")
