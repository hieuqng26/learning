import matplotlib.pyplot as plt

from project.qld.trade.ir.callable_ccs import CallableCCS


def test1():
    #####################################
    ###          INPUT                ###
    #####################################
    eval_date = "2024-12-31"
    start_date = "2021-06-09"
    end_date = '2066-06-09'
    cal = ['TARGET', 'NY', 'LDN']
    bdc = 'FOLLOWING'
    termination_bdc = 'FOLLOWING'
    settlement_lag = 2
    dc1 = 'ACTUAL/360'
    dc2 = '30/360'
    ccy1 = 'USD'
    ccy2 = 'EUR'

    notional_exchange = True
    interim_exchange = False
    notional_reset = False
    notionals1 = [73440000.00, 73440000.00, 74428502.40, 74428502.40, 75430310.05, 75430310.05, 76445602.03, 76445602.03,
                  77474559.83, 77474559.83, 78517367.40, 78517367.40, 79574211.17, 79574211.17, 80645280.05, 80645280.05,
                  81730765.52, 81730765.52, 82830861.63, 82830861.63, 83945765.02, 83945765.02, 85075675.02, 85075675.02,
                  86220793.60, 86220793.60, 87381325.48, 87381325.48, 88557478.12, 88557478.12, 89749461.78, 89749461.78,
                  90957489.54, 90957489.54, 92181777.35, 92181777.35, 93422544.07, 93422544.07, 94680011.51, 94680011.51,
                  95954404.46, 95954404.46, 97245950.74, 97245950.74, 98554881.24, 98554881.24, 99881429.94, 99881429.94,
                  101225833.99, 101225833.99, 102588333.71, 102588333.71, 103969172.68, 103969172.68, 105368597.74, 105368597.74,
                  106786859.06, 106786859.06, 108224210.18, 108224210.18, 109680908.05, 109680908.05, 111157213.07, 111157213.07,
                  112653389.15, 112653389.15, 114169703.77, 114169703.77, 115706427.98, 115706427.98, 117263836.50, 117263836.50,
                  118842207.74, 118842207.74, 120441823.86, 120441823.86, 122062970.80, 122062970.80, 123705938.39, 123705938.39,
                  125371020.32, 125371020.32, 127058514.24, 127058514.24, 128768721.84, 128768721.84, 130501948.84, 130501948.84,
                  132258505.07, 132258505.07]
    notionals2 = [60000000.00, 60807600.00, 61626070.30, 62455557.21, 63296209.01, 64148175.98, 65011610.43, 65886666.71,
                  66773501.24, 67672272.57, 68583141.36, 69506270.44, 70441824.84, 71389971.80, 72350880.82, 73324723.68,
                  74311674.46, 75311909.60, 76325607.90, 77352950.58, 78394121.29, 79449306.16, 80518693.82, 81602475.44,
                  82700844.76, 83813998.13, 84942134.54, 86085455.67, 87244165.90, 88418472.37, 89608585.01, 90814716.56,
                  92037082.64, 93275901.77, 94531395.41, 95803787.99, 97093306.98, 98400182.89, 99724649.35, 101066943.13,
                  102427304.18, 103805975.69, 105203204.12, 106619239.25, 108054334.21]
    # notionals1 = [73440000.00]
    # notionals2 = [60000000.00]

    interim_exchange_notionals1 = [988502.40, 1001807.65, 1015291.98, 1028957.80, 1042807.57, 1056843.77, 1071068.88,
                                   1085485.47, 1100096.11, 1114903.39, 1129910.00, 1145118.58, 1160531.88, 1176152.64,
                                   1191983.66, 1208027.76, 1224287.81, 1240766.72, 1257467.44, 1274392.95, 1291546.28,
                                   1308930.50, 1326548.70, 1344404.05, 1362499.72, 1380838.97, 1399425.06, 1418261.32,
                                   1437351.12, 1456697.87, 1476305.02, 1496176.08, 1516314.62, 1536724.21, 1557408.52,
                                   1578371.24, 1599616.12, 1621146.94, 1642967.59, 1665081.93, 1687493.92, 1710207.60,
                                   1733227.00, 1756556.23, 1780199.48]
    interim_exchange_notionals2 = [0] * len(interim_exchange_notionals1)
    interim_exchange_notionals1 = sum(([0, i] for i in interim_exchange_notionals1), [])
    # interim_exchange_notionals1 = [0]
    # interim_exchange_notionals2 = [0]

    redemption_notionals1 = [89749461.78]
    redemption_notionals2 = [73324723.68]
    option_tenors = ['15Y']
    exercise_lag = 20
    freq1 = '6M'
    freq2 = '12M'
    spread_or_fixed_rate1 = 0.0042826 - 0.0002  # https://www.newyorkfed.org/medialibrary/Microsites/arrc/files/2021/spread-adjustments-narrative-oct-6-2021
    spread_or_fixed_rate2 = 0.0  # no EUR coupon
    final_notional1 = 134038704.55
    final_notional2 = 109508745.55

    #####################################
    ###          TRADE                ###
    #####################################
    test_ccs = CallableCCS(
        eval_date, start_date, end_date, cal, bdc, termination_bdc, settlement_lag,
        dc1, dc2, ccy1, ccy2, notional_exchange, interim_exchange, notional_reset,
        notionals1, redemption_notionals1, interim_exchange_notionals1,
        notionals2, redemption_notionals2, interim_exchange_notionals2,
        option_tenors, exercise_lag, freq1, freq2,
        spread_or_fixed_rate1, spread_or_fixed_rate2, final_notional1, final_notional2
    )

    test_ccs.price()

    return


def test2():
    trade_data = {
        'evaluation_date': '2024-12-31', 'start_date': '2021-06-09', 'end_date': '2066-06-09',
        'calendar': ['US', 'TARGET', 'UK'], 'business_day_convention': 'Following',
        'termination_business_day_convention': 'Following', 'settlement_lag': 2,
        'currency1': 'USD', 'notionals1': [200], 'day_count_convention1': 'ACTUAL360', 'frequency1': '6M',
        'spread_or_fixed_rate1': 0, 'final_notional1': 0, 'currency2': 'EUR',
        'notionals2': [550], 'day_count_convention2': '30/360', 'frequency2': '1Y',
        'spread_or_fixed_rate2': 0, 'final_notional2': 0, 'redemption_notionals1': [0],
        'redemption_notionals2': [0], 'interim_exchange_notionals1': [0], 'interim_exchange_notionals2': [0],
        'option_tenors': ['15Y'], 'exercise_lag': 20,
        'notional_exchange': True, 'interim_exchange': False, 'notional_reset': False}
    trade = CallableCCS(
        evaluation_date=trade_data.get('evaluation_date'),
        start_date=trade_data.get('start_date'),
        end_date=trade_data.get('end_date'),
        cal=trade_data.get('calendar'),
        bdc=trade_data.get('business_day_convention'),
        termination_bdc=trade_data.get('termination_business_day_convention'),
        settlement_lag=trade_data.get('settlement_lag'),
        dc1=trade_data.get('day_count_convention1'),
        dc2=trade_data.get('day_count_convention2'),
        ccy1=trade_data.get('currency1'),
        ccy2=trade_data.get('currency2'),
        notional_exchange=trade_data.get('notional_exchange'),
        interim_exchange=trade_data.get('interim_exchange'),
        notional_reset=trade_data.get('notional_reset'),
        notionals1=trade_data.get('notionals1'),
        redemption_notionals1=trade_data.get('redemption_notionals1'),
        interim_exchange_notionals1=trade_data.get('interim_exchange_notionals1'),
        notionals2=trade_data.get('notionals2'),
        redemption_notionals2=trade_data.get('redemption_notionals2'),
        interim_exchange_notionals2=trade_data.get('interim_exchange_notionals2'),
        option_tenors=trade_data.get('option_tenors'),
        exercise_lag=trade_data.get('exercise_lag'),
        freq1=trade_data.get('frequency1'),
        freq2=trade_data.get('frequency2'),
        spread_or_fixed_rate1=trade_data.get('spread_or_fixed_rate1'),
        spread_or_fixed_rate2=trade_data.get('spread_or_fixed_rate2'),
        final_notional1=trade_data.get('final_notional1'),
        final_notional2=trade_data.get('final_notional2')
    )
    trade.price()
    print(trade.result)


def test_risk_sensitivity():
    eval_date = "2024-12-31"
    start_date = "2021-06-09"
    end_date = '2066-06-09'
    cal = ['TARGET', 'NY', 'LDN']
    bdc = 'FOLLOWING'
    termination_bdc = 'FOLLOWING'
    settlement_lag = 2
    dc1 = 'ACTUAL/360'
    dc2 = '30/360'
    ccy1 = 'USD'
    ccy2 = 'EUR'

    notional_exchange = True
    interim_exchange = False
    notional_reset = False
    notionals1 = [73440000.00, 73440000.00, 74428502.40, 74428502.40, 75430310.05, 75430310.05, 76445602.03, 76445602.03,
                  77474559.83, 77474559.83, 78517367.40, 78517367.40, 79574211.17, 79574211.17, 80645280.05, 80645280.05,
                  81730765.52, 81730765.52, 82830861.63, 82830861.63, 83945765.02, 83945765.02, 85075675.02, 85075675.02,
                  86220793.60, 86220793.60, 87381325.48, 87381325.48, 88557478.12, 88557478.12, 89749461.78, 89749461.78,
                  90957489.54, 90957489.54, 92181777.35, 92181777.35, 93422544.07, 93422544.07, 94680011.51, 94680011.51,
                  95954404.46, 95954404.46, 97245950.74, 97245950.74, 98554881.24, 98554881.24, 99881429.94, 99881429.94,
                  101225833.99, 101225833.99, 102588333.71, 102588333.71, 103969172.68, 103969172.68, 105368597.74, 105368597.74,
                  106786859.06, 106786859.06, 108224210.18, 108224210.18, 109680908.05, 109680908.05, 111157213.07, 111157213.07,
                  112653389.15, 112653389.15, 114169703.77, 114169703.77, 115706427.98, 115706427.98, 117263836.50, 117263836.50,
                  118842207.74, 118842207.74, 120441823.86, 120441823.86, 122062970.80, 122062970.80, 123705938.39, 123705938.39,
                  125371020.32, 125371020.32, 127058514.24, 127058514.24, 128768721.84, 128768721.84, 130501948.84, 130501948.84,
                  132258505.07, 132258505.07]
    notionals2 = [60000000.00, 60807600.00, 61626070.30, 62455557.21, 63296209.01, 64148175.98, 65011610.43, 65886666.71,
                  66773501.24, 67672272.57, 68583141.36, 69506270.44, 70441824.84, 71389971.80, 72350880.82, 73324723.68,
                  74311674.46, 75311909.60, 76325607.90, 77352950.58, 78394121.29, 79449306.16, 80518693.82, 81602475.44,
                  82700844.76, 83813998.13, 84942134.54, 86085455.67, 87244165.90, 88418472.37, 89608585.01, 90814716.56,
                  92037082.64, 93275901.77, 94531395.41, 95803787.99, 97093306.98, 98400182.89, 99724649.35, 101066943.13,
                  102427304.18, 103805975.69, 105203204.12, 106619239.25, 108054334.21]
    # notionals1 = [73440000.00]
    # notionals2 = [60000000.00]

    interim_exchange_notionals1 = [988502.40, 1001807.65, 1015291.98, 1028957.80, 1042807.57, 1056843.77, 1071068.88,
                                   1085485.47, 1100096.11, 1114903.39, 1129910.00, 1145118.58, 1160531.88, 1176152.64,
                                   1191983.66, 1208027.76, 1224287.81, 1240766.72, 1257467.44, 1274392.95, 1291546.28,
                                   1308930.50, 1326548.70, 1344404.05, 1362499.72, 1380838.97, 1399425.06, 1418261.32,
                                   1437351.12, 1456697.87, 1476305.02, 1496176.08, 1516314.62, 1536724.21, 1557408.52,
                                   1578371.24, 1599616.12, 1621146.94, 1642967.59, 1665081.93, 1687493.92, 1710207.60,
                                   1733227.00, 1756556.23, 1780199.48]
    interim_exchange_notionals2 = [0] * len(interim_exchange_notionals1)
    interim_exchange_notionals1 = sum(([0, i] for i in interim_exchange_notionals1), [])
    # interim_exchange_notionals1 = [0]
    # interim_exchange_notionals2 = [0]

    redemption_notionals1 = [89749461.78]
    redemption_notionals2 = [73324723.68]
    option_tenors = ['15Y']
    exercise_lag = 20
    freq1 = '6M'
    freq2 = '12M'
    spread_or_fixed_rate1 = 0.0042826 - 0.0002  # https://www.newyorkfed.org/medialibrary/Microsites/arrc/files/2021/spread-adjustments-narrative-oct-6-2021
    spread_or_fixed_rate2 = 0.0  # no EUR coupon
    final_notional1 = 134038704.55
    final_notional2 = 109508745.55

    #####################################
    ###          TRADE                ###
    #####################################
    trade = CallableCCS(
        eval_date, start_date, end_date, cal, bdc, termination_bdc, settlement_lag,
        dc1, dc2, ccy1, ccy2, notional_exchange, interim_exchange, notional_reset,
        notionals1, redemption_notionals1, interim_exchange_notionals1,
        notionals2, redemption_notionals2, interim_exchange_notionals2,
        option_tenors, exercise_lag, freq1, freq2,
        spread_or_fixed_rate1, spread_or_fixed_rate2, final_notional1, final_notional2
    )

    # Use the new risk sensitivity methods
    bump_points = [1, 5, 10, 15, 20, 25, 30, 50]
    risk_results = trade.calculate_risk_sensitivity(bump_points=bump_points, curve_name='USD.SOFR.CSA_USD')

    # Prepare data for plotting (include base case with 0bp bump)
    risk_dict = {
        'BP': [0] + risk_results['bump_points'],
        'NPV': [risk_results['base_npv']] + risk_results['npv_values']
    }

    plt.figure(figsize=(6, 4))
    plt.plot(risk_dict['BP'], risk_dict['NPV'], marker='o')  # line plot with markers
    plt.xlabel('Basis points')
    plt.ylabel('NPV')
    plt.title('Risk Sensitivity')
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    # test1()
    # test2()
    test_risk_sensitivity()
