import pandas as pd
from datetime import datetime
import QuantLib as ql

def read_sofr(data_path):
    sofr_data = pd.read_excel(data_path)
    sofr_data['Effective Date'] = sofr_data['Effective Date'].apply(lambda x: to_date(x, fmt='%m/%d/%Y'))
    return sofr_data

def to_date(d, fmt):
    d = pd.to_datetime(d, format=fmt)
    return ql.Date(d.day, d.month, d.year)

def fetchRFRFixing(rfr_data, rfr_curve, start_date, end_date, dc, cal):
    '''
    Calculate (forward-approximated) fixing rate
    @ rfr_data: historical rfr rates 
    @ start_date: start date of the interest period
    @ end_date: end date of the interest period
    @ cal: calendar
    '''
    # start_date should be smaller than end_date
    if start_date >= end_date:
        return 0.

    ## rfr curve will be used for interest period outside of rfr_data
    #flat_rate = rfr_data['Rate'].values[-1]/100 # use last available historical rate as flat rate
    #rfr_curve = ql.YieldTermStructureHandle(ql.FlatForward(start_date, flat_rate, dc)) # use flat curve for now

    maxDataDate = max(rfr_data['Effective Date'])
    # accumulating interest rate
    calendarDays = 0. # dc / N, where dc is sum of nb
    R = 0. # Rb = Mult(1+rb*nb/N)-1

    end_date = cal.advance(end_date, -1, ql.Days)
    while start_date <= end_date:
        # get nb: yearFraction between 2 dates
        next_date = cal.advance(start_date, 1, ql.Days)
        nb = dc.yearFraction(start_date, next_date)
        calendarDays += nb

        # get rate r
        #try:
        if start_date <= maxDataDate:
            # Start - Now (past): use historical data
            fetch_date = start_date
            while fetch_date not in rfr_data['Effective Date'].values: # if date is not in the file, use previsous date
                fetch_date = fetch_date - ql.Period(1, ql.Days)

            rb = rfr_data[rfr_data['Effective Date'] == fetch_date]['Rate'].values[0]
        #except KeyError:
        else:
            # Now - End (future): use forward rate
            rb = rfr_curve.forwardRate(start_date, next_date, dc, ql.Simple).rate()

        # update accumulated interest
        R = (R+1)*(1+rb*nb)-1
        start_date = next_date

    return R / calendarDays

#def fetchMultiRFRFixing(rfr_data, rfr_curve, start_date, end_dates, dc, cal):
#    '''
#    Calculate (forward-approximated) fixing rate
#    @ rfr_data: historical rfr rates 
#    @ start_date: start date of the interest period
#    @ end_dates: end dates of the interest period
#    @ cal: calendar
#    '''
#    maxEndDate = max(end_dates)
#    results = {}


#    # rfr curve will be used for interest period outside of rfr_data
#    #flat_rate = rfr_data['Rate'].values[-1]/100 # use last available historical rate as flat rate
#    #rfr_curve = ql.YieldTermStructureHandle(ql.FlatForward(start_date, flat_rate, dc)) # use flat curve for now

#    # accumulating interest rate
#    calendarDays = 0 # dc / N, where dc is sum of nb
#    R = 0 # Rb = Mult(1+rb*nb/N)-1

#    maxEndDate = cal.advance(maxEndDate, -1, ql.Days)
#    while start_date <= maxEndDate:
#        # get nb: yearFraction between 2 dates
#        next_date = cal.advance(start_date, 1, ql.Days)
#        nb = dc.yearFraction(start_date, next_date)
#        calendarDays += nb

#        # get rate r
#        try:
#            # Start - Now (past): use historical data
#            rb = rfr_data[rfr_data['Effective Date'] == start_date]['Rate'].values[0]
#        except IndexError:
#            # Now - End (future): use forward rate
#            rb = rfr_curve.forwardRate(start_date, next_date, dc, ql.Continuous).rate()

#        # update accumulated interest
#        R = (R+1)*(1+rb*nb)-1
#        start_date = next_date
#        results[next_date] = R / calendarDays

#    return [results[i] if i in results else 0 for i in end_dates]

## input
#sofr_data = pd.read_excel("./market/20231115/SOFR01012023_20112023.xlsx")
#sofr_data['Effective Date'] = sofr_data['Effective Date'].apply(lambda x: to_date(x, fmt='%m/%d/%Y'))
#dc = ql.Actual365Fixed()
#cal = ql.JointCalendar(ql.UnitedStates(ql.UnitedStates.LiborImpact), ql.TARGET())

## parameters
#start_date = ql.Date(5, ql.April, 2023)
#end_date = [ql.Date(5, ql.April, 2023), ql.Date(5, ql.October, 2023), ql.Date(5, ql.July, 2023)]
#print(fetchMultiRFRFixing(sofr_data, start_date, end_date, dc, cal))