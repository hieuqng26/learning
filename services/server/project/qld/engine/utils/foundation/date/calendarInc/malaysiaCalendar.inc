namespace QLD {
	int MalaysiaCalendar::holidays[] = {
		43831, // 01/Jan/2020, New Year's Day (Many regions)
		43855, // 25/Jan/2020, Lunar New Year's Day
		43856, // 26/Jan/2020, Second Day of Lunar New Year (Most regions)
		43856, // 26/Jan/2020, Lunar New Year Holiday (Kelantan, Terengganu)
		43857, // 27/Jan/2020, Lunar New Year Holiday (Many regions)
		43857, // 27/Jan/2020, 'Lunar New Year Holiday' day off (Kelantan, Terengganu)
		43862, // 01/Feb/2020, Federal Territory Day (KUL, LBN, PJY)
		43869, // 08/Feb/2020, Thaipusam (Many regions)
		43952, // 01/May/2020, Labour Day
		43958, // 07/May/2020, Wesak Day
		43961, // 10/May/2020, Nuzul Al-Quran (Most regions)
		43975, // 24/May/2020, Hari Raya Puasa
		43976, // 25/May/2020, Hari Raya Puasa Day 2
		43977, // 26/May/2020, Hari Raya Puasa (Many regions)
		43990, // 08/Jun/2020, The Yang di-Pertuan Agong's Birthday
		44043, // 31/Jul/2020, Hari Raya Haji
		44045, // 02/Aug/2020, Hari Raya Haji holiday (Many regions)
		44063, // 20/Aug/2020, Muharram/New Year
		44074, // 31/Aug/2020, Malaysia's National Day
		44090, // 16/Sep/2020, Malaysia Day
		44133, // 29/Oct/2020, The Prophet Muhammad's Birthday
		44149, // 14/Nov/2020, Diwali/Deepavali (Most regions)
		44190, // 25/Dec/2020, Christmas Day
		44197, // 01/Jan/2021, New Year's Day (Many regions)
		44224, // 28/Jan/2021, Thaipusam (Many regions)
		44228, // 01/Feb/2021, Federal Territory Day (KUL, LBN, PJY)
		44239, // 12/Feb/2021, Lunar New Year's Day
		44240, // 13/Feb/2021, Second Day of Lunar New Year (Most regions)
		44240, // 13/Feb/2021, Lunar New Year Holiday (Kelantan, Terengganu)
		44315, // 29/Apr/2021, Nuzul Al-Quran (Most regions)
		44317, // 01/May/2021, Labour Day
		44329, // 13/May/2021, Hari Raya Puasa
		44330, // 14/May/2021, Hari Raya Puasa Day 2
		44342, // 26/May/2021, Wesak Day
		44354, // 07/Jun/2021, The Yang di-Pertuan Agong's Birthday
		44397, // 20/Jul/2021, Hari Raya Haji
		44397, // 20/Jul/2021, Hari Raya Haji holiday
		44418, // 10/Aug/2021, Muharram/New Year
		44439, // 31/Aug/2021, Malaysia's National Day
		44455, // 16/Sep/2021, Malaysia Day
		44488, // 19/Oct/2021, The Prophet Muhammad's Birthday
		44504, // 04/Nov/2021, Diwali/Deepavali (Most regions)
		44520, // 20/Nov/2021, Malacca State Election Holiday (Malacca)
		44555, // 25/Dec/2021, Christmas Day
		44562, // 01/Jan/2022, New Year's Day (Many regions)
		44579, // 18/Jan/2022, Thaipusam (Many regions)
		44593, // 01/Feb/2022, Lunar New Year's Day
		44593, // 01/Feb/2022, Federal Territory Day (KUL, LBN, PJY)
		44594, // 02/Feb/2022, Second Day of Lunar New Year (Most regions)
		44594, // 02/Feb/2022, Lunar New Year Holiday (Kelantan, Terengganu)
		44670, // 19/Apr/2022, Nuzul Al-Quran (Most regions)
		44682, // 01/May/2022, Labour Day
		44683, // 02/May/2022, Hari Raya Puasa
		44684, // 03/May/2022, Hari Raya Puasa Day 2
		44685, // 04/May/2022, 'Labour Day' observed
		44696, // 15/May/2022, Wesak Day
		44718, // 06/Jun/2022, The Yang di-Pertuan Agong's Birthday
		44752, // 10/Jul/2022, Hari Raya Haji
		44752, // 10/Jul/2022, Hari Raya Haji holiday
		44772, // 30/Jul/2022, Muharram/New Year
		44804, // 31/Aug/2022, Malaysia's National Day
		44820, // 16/Sep/2022, Malaysia Day
		44843, // 09/Oct/2022, The Prophet Muhammad's Birthday
		44844, // 10/Oct/2022, The Prophet Muhammad's Birthday Holiday (Many regions)
		44858, // 24/Oct/2022, Diwali/Deepavali (Most regions)
		44883, // 18/Nov/2022, Election Eve Holiday (Many regions)
		44883, // 18/Nov/2022, Election Eve Holiday (JHR, KDH, KTN)
		44883, // 18/Nov/2022, Election Eve Holiday
		44884, // 19/Nov/2022, General Elections
		44884, // 19/Nov/2022, General Elections (Terengganu)
		44884, // 19/Nov/2022, General Elections (Many regions)
		44885, // 20/Nov/2022, 'General Elections' day off (Terengganu)
		44885, // 20/Nov/2022, 'Election Eve Holiday' day off (JHR, KDH, KTN)
		44893, // 28/Nov/2022, Elections Victory Public Holiday
		44920, // 25/Dec/2022, Christmas Day
		44921, // 26/Dec/2022, 'Christmas Day' observed
		44927, // 01/Jan/2023, New Year's Day (Many regions)
		44928, // 02/Jan/2023, 'New Year's Day' observed (Many regions)
		44948, // 22/Jan/2023, Lunar New Year's Day
		44949, // 23/Jan/2023, Second Day of Lunar New Year (Most regions)
		44949, // 23/Jan/2023, Lunar New Year Holiday (Kelantan, Terengganu)
		44958, // 01/Feb/2023, Federal Territory Day (KUL, LBN, PJY)
		44962, // 05/Feb/2023, Thaipusam (Many regions)
		45024, // 08/Apr/2023, Nuzul Al-Quran (Most regions)
		45037, // 21/Apr/2023, Hari Raya Puasa Holiday
		45038, // 22/Apr/2023, Hari Raya Puasa
		45039, // 23/Apr/2023, Hari Raya Puasa Day 2
		45047, // 01/May/2023, Labour Day
		45050, // 04/May/2023, Wesak Day
		45082, // 05/Jun/2023, The Yang di-Pertuan Agong's Birthday
		45106, // 29/Jun/2023, Hari Raya Haji
		45126, // 19/Jul/2023, Muharram/New Year
		45169, // 31/Aug/2023, Malaysia's National Day
		45185, // 16/Sep/2023, Malaysia Day
		45197, // 28/Sep/2023, The Prophet Muhammad's Birthday
		45242, // 12/Nov/2023, Diwali/Deepavali (Most regions)
		45285, // 25/Dec/2023, Christmas Day
		45292, // 01/Jan/2024, New Year's Day (Many regions)
		45316, // 25/Jan/2024, Thaipusam (Many regions)
		45323, // 01/Feb/2024, Federal Territory Day (KUL, LBN, PJY)
		45332, // 10/Feb/2024, Lunar New Year's Day
		45333, // 11/Feb/2024, Second Day of Lunar New Year (Most regions)
		45333, // 11/Feb/2024, Lunar New Year Holiday (Kelantan, Terengganu)
		45378, // 27/Mar/2024, Nuzul Al-Quran (Most regions)
		45392, // 10/Apr/2024, Hari Raya Puasa
		45393, // 11/Apr/2024, Hari Raya Puasa Day 2
		45413, // 01/May/2024, Labour Day
		45446, // 03/Jun/2024, The Yang di-Pertuan Agong's Birthday
		45460, // 17/Jun/2024, Hari Raya Haji
		45460, // 17/Jun/2024, Hari Raya Haji holiday
		45481, // 08/Jul/2024, Muharram/New Year
		45535, // 31/Aug/2024, Malaysia's National Day
		45551, // 16/Sep/2024, The Prophet Muhammad's Birthday
		45551, // 16/Sep/2024, Malaysia Day
		45651, // 25/Dec/2024, Christmas Day
		45658, // 01/Jan/2025, New Year's Day (Many regions)
		45686, // 29/Jan/2025, Lunar New Year's Day
		45687, // 30/Jan/2025, Second Day of Lunar New Year (Most regions)
		45687, // 30/Jan/2025, Lunar New Year Holiday (Kelantan, Terengganu)
		45689, // 01/Feb/2025, Federal Territory Day (KUL, LBN, PJY)
		45733, // 17/Mar/2025, Nuzul Al-Quran (Most regions)
		45747, // 31/Mar/2025, Hari Raya Puasa
		45748, // 01/Apr/2025, Hari Raya Puasa Day 2
		45778, // 01/May/2025, Labour Day
		45810, // 02/Jun/2025, The Yang di-Pertuan Agong's Birthday
		45815, // 07/Jun/2025, Hari Raya Haji
		45815, // 07/Jun/2025, Hari Raya Haji holiday
		45835, // 27/Jun/2025, Muharram/New Year
		45900, // 31/Aug/2025, Malaysia's National Day
		45901, // 01/Sep/2025, 'Malaysia's National Day' observed
		45905, // 05/Sep/2025, The Prophet Muhammad's Birthday
		45916, // 16/Sep/2025, Malaysia Day
		46016, // 25/Dec/2025, Christmas Day
		46023, // 01/Jan/2026, New Year's Day (Many regions)
		46054, // 01/Feb/2026, Federal Territory Day (KUL, LBN, PJY)
		46055, // 02/Feb/2026, 'Federal Territory Day' observed (KUL, LBN, PJY)
		46070, // 17/Feb/2026, Lunar New Year's Day
		46071, // 18/Feb/2026, Second Day of Lunar New Year (Most regions)
		46071, // 18/Feb/2026, Lunar New Year Holiday (Kelantan, Terengganu)
		46087, // 06/Mar/2026, Nuzul Al-Quran (Most regions)
		46101, // 20/Mar/2026, Hari Raya Puasa
		46102, // 21/Mar/2026, Hari Raya Puasa Day 2
		46143, // 01/May/2026, Labour Day
		46169, // 27/May/2026, Hari Raya Haji
		46169, // 27/May/2026, Hari Raya Haji holiday
		46174, // 01/Jun/2026, The Yang di-Pertuan Agong's Birthday
		46190, // 17/Jun/2026, Muharram/New Year
		46260, // 26/Aug/2026, The Prophet Muhammad's Birthday
		46265, // 31/Aug/2026, Malaysia's National Day
		46281, // 16/Sep/2026, Malaysia Day
		46381, // 25/Dec/2026, Christmas Day
		46388, // 01/Jan/2027, New Year's Day (Many regions)
		46419, // 01/Feb/2027, Federal Territory Day (KUL, LBN, PJY)
		46424, // 06/Feb/2027, Lunar New Year's Day
		46425, // 07/Feb/2027, Second Day of Lunar New Year (Most regions)
		46425, // 07/Feb/2027, Lunar New Year Holiday (Kelantan, Terengganu)
		46442, // 24/Feb/2027, Nuzul Al-Quran (Most regions)
		46456, // 10/Mar/2027, Hari Raya Puasa
		46457, // 11/Mar/2027, Hari Raya Puasa Day 2
		46508, // 01/May/2027, Labour Day
		46524, // 17/May/2027, Hari Raya Haji
		46524, // 17/May/2027, Hari Raya Haji holiday
		46544, // 06/Jun/2027, Muharram/New Year
		46545, // 07/Jun/2027, The Yang di-Pertuan Agong's Birthday
		46614, // 15/Aug/2027, The Prophet Muhammad's Birthday
		46630, // 31/Aug/2027, Malaysia's National Day
		46646, // 16/Sep/2027, Malaysia Day
		46746, // 25/Dec/2027, Christmas Day
		46753, // 01/Jan/2028, New Year's Day (Many regions)
		46778, // 26/Jan/2028, Lunar New Year's Day
		46779, // 27/Jan/2028, Second Day of Lunar New Year (Most regions)
		46779, // 27/Jan/2028, Lunar New Year Holiday (Kelantan, Terengganu)
		46784, // 01/Feb/2028, Federal Territory Day (KUL, LBN, PJY)
		46796, // 13/Feb/2028, Nuzul Al-Quran (Most regions)
		46810, // 27/Feb/2028, Hari Raya Puasa
		46811, // 28/Feb/2028, Hari Raya Puasa Day 2
		46874, // 01/May/2028, Labour Day
		46878, // 05/May/2028, Hari Raya Haji
		46878, // 05/May/2028, Hari Raya Haji holiday
		46898, // 25/May/2028, Muharram/New Year
		46909, // 05/Jun/2028, The Yang di-Pertuan Agong's Birthday
		46968, // 03/Aug/2028, The Prophet Muhammad's Birthday
		46996, // 31/Aug/2028, Malaysia's National Day
		47012, // 16/Sep/2028, Malaysia Day
		47112, // 25/Dec/2028, Christmas Day
		47119, // 01/Jan/2029, New Year's Day (Many regions)
		47150, // 01/Feb/2029, Federal Territory Day (KUL, LBN, PJY)
		47150, // 01/Feb/2029, Nuzul Al-Quran (Most regions)
		47162, // 13/Feb/2029, Lunar New Year's Day
		47163, // 14/Feb/2029, Second Day of Lunar New Year (Most regions)
		47163, // 14/Feb/2029, Lunar New Year Holiday (Kelantan, Terengganu)
		47164, // 15/Feb/2029, Hari Raya Puasa
		47165, // 16/Feb/2029, Hari Raya Puasa Day 2
		47232, // 24/Apr/2029, Hari Raya Haji
		47232, // 24/Apr/2029, Hari Raya Haji holiday
		47239, // 01/May/2029, Labour Day
		47253, // 15/May/2029, Muharram/New Year
		47273, // 04/Jun/2029, The Yang di-Pertuan Agong's Birthday
		47323, // 24/Jul/2029, The Prophet Muhammad's Birthday
		47361, // 31/Aug/2029, Malaysia's National Day
		47377, // 16/Sep/2029, Malaysia Day
		47477, // 25/Dec/2029, Christmas Day
		47484, // 01/Jan/2030, New Year's Day (Many regions)
		47505, // 22/Jan/2030, Nuzul Al-Quran (Most regions)
		47515, // 01/Feb/2030, Federal Territory Day (KUL, LBN, PJY)
		47517, // 03/Feb/2030, Lunar New Year's Day
		47518, // 04/Feb/2030, Second Day of Lunar New Year (Most regions)
		47518, // 04/Feb/2030, Lunar New Year Holiday (Kelantan, Terengganu)
		47519, // 05/Feb/2030, Hari Raya Puasa
		47520, // 06/Feb/2030, Hari Raya Puasa Day 2
		47587, // 14/Apr/2030, Hari Raya Haji
		47587, // 14/Apr/2030, Hari Raya Haji holiday
		47604, // 01/May/2030, Labour Day
		47607, // 04/May/2030, Muharram/New Year
		47637, // 03/Jun/2030, The Yang di-Pertuan Agong's Birthday
		47677, // 13/Jul/2030, The Prophet Muhammad's Birthday
		47726, // 31/Aug/2030, Malaysia's National Day
		47742, // 16/Sep/2030, Malaysia Day
		47842, // 25/Dec/2030, Christmas Day
		47849, // 01/Jan/2031, New Year's Day (Many regions)
		47859, // 11/Jan/2031, Nuzul Al-Quran (Most regions)
		47871, // 23/Jan/2031, Lunar New Year's Day
		47872, // 24/Jan/2031, Second Day of Lunar New Year (Most regions)
		47872, // 24/Jan/2031, Lunar New Year Holiday (Kelantan, Terengganu)
		47873, // 25/Jan/2031, Hari Raya Puasa
		47874, // 26/Jan/2031, Hari Raya Puasa Day 2
		47880, // 01/Feb/2031, Federal Territory Day (KUL, LBN, PJY)
		47941, // 03/Apr/2031, Hari Raya Haji
		47941, // 03/Apr/2031, Hari Raya Haji holiday
		47961, // 23/Apr/2031, Muharram/New Year
		47969, // 01/May/2031, Labour Day
		48001, // 02/Jun/2031, The Yang di-Pertuan Agong's Birthday
		48031, // 02/Jul/2031, The Prophet Muhammad's Birthday
		48091, // 31/Aug/2031, Malaysia's National Day
		48092, // 01/Sep/2031, 'Malaysia's National Day' observed
		48107, // 16/Sep/2031, Malaysia Day
		48207, // 25/Dec/2031, Christmas Day
		48213, // 31/Dec/2031, Nuzul Al-Quran (Most regions)
		48214, // 01/Jan/2032, New Year's Day (Many regions)
		48227, // 14/Jan/2032, Hari Raya Puasa
		48228, // 15/Jan/2032, Hari Raya Puasa Day 2
		48245, // 01/Feb/2032, Federal Territory Day (KUL, LBN, PJY)
		48246, // 02/Feb/2032, 'Federal Territory Day' observed (KUL, LBN, PJY)
		48255, // 11/Feb/2032, Lunar New Year's Day
		48256, // 12/Feb/2032, Second Day of Lunar New Year (Most regions)
		48256, // 12/Feb/2032, Lunar New Year Holiday (Kelantan, Terengganu)
		48295, // 22/Mar/2032, Hari Raya Haji
		48295, // 22/Mar/2032, Hari Raya Haji holiday
		48316, // 12/Apr/2032, Muharram/New Year
		48335, // 01/May/2032, Labour Day
		48372, // 07/Jun/2032, The Yang di-Pertuan Agong's Birthday
		48386, // 21/Jun/2032, The Prophet Muhammad's Birthday
		48457, // 31/Aug/2032, Malaysia's National Day
		48473, // 16/Sep/2032, Malaysia Day
		48568, // 20/Dec/2032, Nuzul Al-Quran (Most regions)
		48573, // 25/Dec/2032, Christmas Day
		48580, // 01/Jan/2033, New Year's Day (Many regions)
		48582, // 03/Jan/2033, Hari Raya Puasa
		48583, // 04/Jan/2033, Hari Raya Puasa Day 2
		48610, // 31/Jan/2033, Lunar New Year's Day
		48611, // 01/Feb/2033, Second Day of Lunar New Year (Most regions)
		48611, // 01/Feb/2033, Lunar New Year Holiday (Kelantan, Terengganu)
		48611, // 01/Feb/2033, Federal Territory Day (KUL, LBN, PJY)
		48650, // 12/Mar/2033, Hari Raya Haji
		48650, // 12/Mar/2033, Hari Raya Haji holiday
		48670, // 01/Apr/2033, Muharram/New Year
		48700, // 01/May/2033, Labour Day
		48701, // 02/May/2033, 'Labour Day' observed
		48736, // 06/Jun/2033, The Yang di-Pertuan Agong's Birthday
		48740, // 10/Jun/2033, The Prophet Muhammad's Birthday
		48822, // 31/Aug/2033, Malaysia's National Day
		48838, // 16/Sep/2033, Malaysia Day
		48922, // 09/Dec/2033, Nuzul Al-Quran (Most regions)
		48936, // 23/Dec/2033, Hari Raya Puasa
		48937, // 24/Dec/2033, Hari Raya Puasa Day 2
		48938, // 25/Dec/2033, Christmas Day
		48939, // 26/Dec/2033, 'Christmas Day' observed
		48945, // 01/Jan/2034, New Year's Day (Many regions)
		48946, // 02/Jan/2034, 'New Year's Day' observed (Many regions)
		48976, // 01/Feb/2034, Federal Territory Day (KUL, LBN, PJY)
		48994, // 19/Feb/2034, Lunar New Year's Day
		48995, // 20/Feb/2034, Second Day of Lunar New Year (Most regions)
		48995, // 20/Feb/2034, Lunar New Year Holiday (Kelantan, Terengganu)
		49004, // 01/Mar/2034, Hari Raya Haji
		49004, // 01/Mar/2034, Hari Raya Haji holiday
		49024, // 21/Mar/2034, Muharram/New Year
		49065, // 01/May/2034, Labour Day
		49094, // 30/May/2034, The Prophet Muhammad's Birthday
		49100, // 05/Jun/2034, The Yang di-Pertuan Agong's Birthday
		49187, // 31/Aug/2034, Malaysia's National Day
		49203, // 16/Sep/2034, Malaysia Day
		49276, // 28/Nov/2034, Nuzul Al-Quran (Most regions)
		49290, // 12/Dec/2034, Hari Raya Puasa
		49291, // 13/Dec/2034, Hari Raya Puasa Day 2
		49303, // 25/Dec/2034, Christmas Day
		49310, // 01/Jan/2035, New Year's Day (Many regions)
		49341, // 01/Feb/2035, Federal Territory Day (KUL, LBN, PJY)
		49348, // 08/Feb/2035, Lunar New Year's Day
		49349, // 09/Feb/2035, Second Day of Lunar New Year (Most regions)
		49349, // 09/Feb/2035, Lunar New Year Holiday (Kelantan, Terengganu)
		49358, // 18/Feb/2035, Hari Raya Haji
		49358, // 18/Feb/2035, Hari Raya Haji holiday
		49379, // 11/Mar/2035, Muharram/New Year
		49430, // 01/May/2035, Labour Day
		49449, // 20/May/2035, The Prophet Muhammad's Birthday
		49464, // 04/Jun/2035, The Yang di-Pertuan Agong's Birthday
		49552, // 31/Aug/2035, Malaysia's National Day
		49568, // 16/Sep/2035, Malaysia Day
		49631, // 18/Nov/2035, Nuzul Al-Quran (Most regions)
		49645, // 02/Dec/2035, Hari Raya Puasa
		49646, // 03/Dec/2035, Hari Raya Puasa Day 2
		49668, // 25/Dec/2035, Christmas Day
		49675, // 01/Jan/2036, New Year's Day (Many regions)
		49702, // 28/Jan/2036, Lunar New Year's Day
		49703, // 29/Jan/2036, Second Day of Lunar New Year (Most regions)
		49703, // 29/Jan/2036, Lunar New Year Holiday (Kelantan, Terengganu)
		49706, // 01/Feb/2036, Federal Territory Day (KUL, LBN, PJY)
		49713, // 08/Feb/2036, Hari Raya Haji
		49713, // 08/Feb/2036, Hari Raya Haji holiday
		49733, // 28/Feb/2036, Muharram/New Year
		49796, // 01/May/2036, Labour Day
		49803, // 08/May/2036, The Prophet Muhammad's Birthday
		49828, // 02/Jun/2036, The Yang di-Pertuan Agong's Birthday
		49918, // 31/Aug/2036, Malaysia's National Day
		49919, // 01/Sep/2036, 'Malaysia's National Day' observed
		49934, // 16/Sep/2036, Malaysia Day
		49985, // 06/Nov/2036, Nuzul Al-Quran (Most regions)
		49999, // 20/Nov/2036, Hari Raya Puasa
		50000, // 21/Nov/2036, Hari Raya Puasa Day 2
		50034, // 25/Dec/2036, Christmas Day
		50041, // 01/Jan/2037, New Year's Day (Many regions)
		50067, // 27/Jan/2037, Hari Raya Haji
		50067, // 27/Jan/2037, Hari Raya Haji holiday
		50072, // 01/Feb/2037, Federal Territory Day (KUL, LBN, PJY)
		50073, // 02/Feb/2037, 'Federal Territory Day' observed (KUL, LBN, PJY)
		50086, // 15/Feb/2037, Lunar New Year's Day
		50087, // 16/Feb/2037, Second Day of Lunar New Year (Most regions)
		50087, // 16/Feb/2037, Lunar New Year Holiday (Kelantan, Terengganu)
		50088, // 17/Feb/2037, Muharram/New Year
		50158, // 28/Apr/2037, The Prophet Muhammad's Birthday
		50161, // 01/May/2037, Labour Day
		50192, // 01/Jun/2037, The Yang di-Pertuan Agong's Birthday
		50283, // 31/Aug/2037, Malaysia's National Day
		50299, // 16/Sep/2037, Malaysia Day
		50340, // 27/Oct/2037, Nuzul Al-Quran (Most regions)
		50354, // 10/Nov/2037, Hari Raya Puasa
		50355, // 11/Nov/2037, Hari Raya Puasa Day 2
		50399, // 25/Dec/2037, Christmas Day
		50406, // 01/Jan/2038, New Year's Day (Many regions)
		50422, // 17/Jan/2038, Hari Raya Haji
		50422, // 17/Jan/2038, Hari Raya Haji holiday
		50437, // 01/Feb/2038, Federal Territory Day (KUL, LBN, PJY)
		50440, // 04/Feb/2038, Lunar New Year's Day
		50441, // 05/Feb/2038, Second Day of Lunar New Year (Most regions)
		50441, // 05/Feb/2038, Lunar New Year Holiday (Kelantan, Terengganu)
		50442, // 06/Feb/2038, Muharram/New Year
		50512, // 17/Apr/2038, The Prophet Muhammad's Birthday
		50526, // 01/May/2038, Labour Day
		50563, // 07/Jun/2038, The Yang di-Pertuan Agong's Birthday
		50648, // 31/Aug/2038, Malaysia's National Day
		50664, // 16/Sep/2038, Malaysia Day
		50694, // 16/Oct/2038, Nuzul Al-Quran (Most regions)
		50708, // 30/Oct/2038, Hari Raya Puasa
		50709, // 31/Oct/2038, Hari Raya Puasa Day 2
		50764, // 25/Dec/2038, Christmas Day
		50771, // 01/Jan/2039, New Year's Day (Many regions)
		50776, // 06/Jan/2039, Hari Raya Haji
		50776, // 06/Jan/2039, Hari Raya Haji holiday
		50794, // 24/Jan/2039, Lunar New Year's Day
		50795, // 25/Jan/2039, Second Day of Lunar New Year (Most regions)
		50795, // 25/Jan/2039, Lunar New Year Holiday (Kelantan, Terengganu)
		50796, // 26/Jan/2039, Muharram/New Year
		50802, // 01/Feb/2039, Federal Territory Day (KUL, LBN, PJY)
		50866, // 06/Apr/2039, The Prophet Muhammad's Birthday
		50891, // 01/May/2039, Labour Day
		50892, // 02/May/2039, 'Labour Day' observed
		50927, // 06/Jun/2039, The Yang di-Pertuan Agong's Birthday
		51013, // 31/Aug/2039, Malaysia's National Day
		51029, // 16/Sep/2039, Malaysia Day
		51048, // 05/Oct/2039, Nuzul Al-Quran (Most regions)
		51062, // 19/Oct/2039, Hari Raya Puasa
		51063, // 20/Oct/2039, Hari Raya Puasa Day 2
		51129, // 25/Dec/2039, Christmas Day
		51130, // 26/Dec/2039, Hari Raya Haji
		51130, // 26/Dec/2039, Hari Raya Haji holiday
		51130, // 26/Dec/2039, 'Christmas Day' observed
		51136, // 01/Jan/2040, New Year's Day (Many regions)
		51137, // 02/Jan/2040, 'New Year's Day' observed (Many regions)
		51151, // 16/Jan/2040, Muharram/New Year
		51167, // 01/Feb/2040, Federal Territory Day (KUL, LBN, PJY)
		51178, // 12/Feb/2040, Lunar New Year's Day
		51179, // 13/Feb/2040, Second Day of Lunar New Year (Most regions)
		51179, // 13/Feb/2040, Lunar New Year Holiday (Kelantan, Terengganu)
		51221, // 26/Mar/2040, The Prophet Muhammad's Birthday
		51257, // 01/May/2040, Labour Day
		51291, // 04/Jun/2040, The Yang di-Pertuan Agong's Birthday
		51379, // 31/Aug/2040, Malaysia's National Day
		51395, // 16/Sep/2040, Malaysia Day
		51403, // 24/Sep/2040, Nuzul Al-Quran (Most regions)
		51417, // 08/Oct/2040, Hari Raya Puasa
		51418, // 09/Oct/2040, Hari Raya Puasa Day 2
		51485, // 15/Dec/2040, Hari Raya Haji
		51485, // 15/Dec/2040, Hari Raya Haji holiday
		51495, // 25/Dec/2040, Christmas Day
		51502, // 01/Jan/2041, New Year's Day (Many regions)
		51505, // 04/Jan/2041, Muharram/New Year
		51533, // 01/Feb/2041, Lunar New Year's Day
		51533, // 01/Feb/2041, Federal Territory Day (KUL, LBN, PJY)
		51534, // 02/Feb/2041, Second Day of Lunar New Year (Most regions)
		51534, // 02/Feb/2041, Lunar New Year Holiday (Kelantan, Terengganu)
		51575, // 15/Mar/2041, The Prophet Muhammad's Birthday
		51622, // 01/May/2041, Labour Day
		51655, // 03/Jun/2041, The Yang di-Pertuan Agong's Birthday
		51744, // 31/Aug/2041, Malaysia's National Day
		51757, // 13/Sep/2041, Nuzul Al-Quran (Most regions)
		51760, // 16/Sep/2041, Malaysia Day
		51771, // 27/Sep/2041, Hari Raya Puasa
		51772, // 28/Sep/2041, Hari Raya Puasa Day 2
		51839, // 04/Dec/2041, Hari Raya Haji
		51839, // 04/Dec/2041, Hari Raya Haji holiday
		51859, // 24/Dec/2041, Muharram/New Year
		51860, // 25/Dec/2041, Christmas Day
		51867, // 01/Jan/2042, New Year's Day (Many regions)
		51888, // 22/Jan/2042, Lunar New Year's Day
		51889, // 23/Jan/2042, Second Day of Lunar New Year (Most regions)
		51889, // 23/Jan/2042, Lunar New Year Holiday (Kelantan, Terengganu)
		51898, // 01/Feb/2042, Federal Territory Day (KUL, LBN, PJY)
		51929, // 04/Mar/2042, The Prophet Muhammad's Birthday
		51987, // 01/May/2042, Labour Day
		52019, // 02/Jun/2042, The Yang di-Pertuan Agong's Birthday
		52109, // 31/Aug/2042, Malaysia's National Day
		52110, // 01/Sep/2042, 'Malaysia's National Day' observed
		52111, // 02/Sep/2042, Nuzul Al-Quran (Most regions)
		52125, // 16/Sep/2042, Hari Raya Puasa
		52125, // 16/Sep/2042, Malaysia Day
		52126, // 17/Sep/2042, Hari Raya Puasa Day 2
		52193, // 23/Nov/2042, Hari Raya Haji
		52193, // 23/Nov/2042, Hari Raya Haji holiday
		52214, // 14/Dec/2042, Muharram/New Year
		52225, // 25/Dec/2042, Christmas Day
		52232, // 01/Jan/2043, New Year's Day (Many regions)
		52263, // 01/Feb/2043, Federal Territory Day (KUL, LBN, PJY)
		52264, // 02/Feb/2043, 'Federal Territory Day' observed (KUL, LBN, PJY)
		52272, // 10/Feb/2043, Lunar New Year's Day
		52273, // 11/Feb/2043, Second Day of Lunar New Year (Most regions)
		52273, // 11/Feb/2043, Lunar New Year Holiday (Kelantan, Terengganu)
		52284, // 22/Feb/2043, The Prophet Muhammad's Birthday
		52352, // 01/May/2043, Labour Day
		52383, // 01/Jun/2043, The Yang di-Pertuan Agong's Birthday
		52466, // 23/Aug/2043, Nuzul Al-Quran (Most regions)
		52474, // 31/Aug/2043, Malaysia's National Day
		52480, // 06/Sep/2043, Hari Raya Puasa
		52481, // 07/Sep/2043, Hari Raya Puasa Day 2
		52490, // 16/Sep/2043, Malaysia Day
		52548, // 13/Nov/2043, Hari Raya Haji
		52548, // 13/Nov/2043, Hari Raya Haji holiday
		52568, // 03/Dec/2043, Muharram/New Year
		52590, // 25/Dec/2043, Christmas Day
		52597, // 01/Jan/2044, New Year's Day (Many regions)
		52626, // 30/Jan/2044, Lunar New Year's Day
		52627, // 31/Jan/2044, Second Day of Lunar New Year (Most regions)
		52627, // 31/Jan/2044, Lunar New Year Holiday (Kelantan, Terengganu)
		52628, // 01/Feb/2044, Federal Territory Day (KUL, LBN, PJY)
		52638, // 11/Feb/2044, The Prophet Muhammad's Birthday
		52718, // 01/May/2044, Labour Day
		52719, // 02/May/2044, 'Labour Day' observed
		52754, // 06/Jun/2044, The Yang di-Pertuan Agong's Birthday
		52820, // 11/Aug/2044, Nuzul Al-Quran (Most regions)
		52834, // 25/Aug/2044, Hari Raya Puasa
		52835, // 26/Aug/2044, Hari Raya Puasa Day 2
		52840, // 31/Aug/2044, Malaysia's National Day
		52856, // 16/Sep/2044, Malaysia Day
		52902, // 01/Nov/2044, Hari Raya Haji
		52902, // 01/Nov/2044, Hari Raya Haji holiday
		52923, // 22/Nov/2044, Muharram/New Year
		52956, // 25/Dec/2044, Christmas Day
		52957, // 26/Dec/2044, 'Christmas Day' observed
		52963, // 01/Jan/2045, New Year's Day (Many regions)
		52964, // 02/Jan/2045, 'New Year's Day' observed (Many regions)
		52993, // 31/Jan/2045, The Prophet Muhammad's Birthday
		52994, // 01/Feb/2045, Federal Territory Day (KUL, LBN, PJY)
		53010, // 17/Feb/2045, Lunar New Year's Day
		53011, // 18/Feb/2045, Second Day of Lunar New Year (Most regions)
		53011, // 18/Feb/2045, Lunar New Year Holiday (Kelantan, Terengganu)
		53083, // 01/May/2045, Labour Day
		53118, // 05/Jun/2045, The Yang di-Pertuan Agong's Birthday
		53175, // 01/Aug/2045, Nuzul Al-Quran (Most regions)
		53189, // 15/Aug/2045, Hari Raya Puasa
		53190, // 16/Aug/2045, Hari Raya Puasa Day 2
		53205, // 31/Aug/2045, Malaysia's National Day
		53221, // 16/Sep/2045, Malaysia Day
		53257, // 22/Oct/2045, Hari Raya Haji
		53257, // 22/Oct/2045, Hari Raya Haji holiday
		53277, // 11/Nov/2045, Muharram/New Year
		53321, // 25/Dec/2045, Christmas Day
		53328, // 01/Jan/2046, New Year's Day (Many regions)
		53347, // 20/Jan/2046, The Prophet Muhammad's Birthday
		53359, // 01/Feb/2046, Federal Territory Day (KUL, LBN, PJY)
		53364, // 06/Feb/2046, Lunar New Year's Day
		53365, // 07/Feb/2046, Second Day of Lunar New Year (Most regions)
		53365, // 07/Feb/2046, Lunar New Year Holiday (Kelantan, Terengganu)
		53448, // 01/May/2046, Labour Day
		53482, // 04/Jun/2046, The Yang di-Pertuan Agong's Birthday
		53529, // 21/Jul/2046, Nuzul Al-Quran (Most regions)
		53543, // 04/Aug/2046, Hari Raya Puasa
		53544, // 05/Aug/2046, Hari Raya Puasa Day 2
		53570, // 31/Aug/2046, Malaysia's National Day
		53586, // 16/Sep/2046, Malaysia Day
		53611, // 11/Oct/2046, Hari Raya Haji
		53611, // 11/Oct/2046, Hari Raya Haji holiday
		53631, // 31/Oct/2046, Muharram/New Year
		53686, // 25/Dec/2046, Christmas Day
		53693, // 01/Jan/2047, New Year's Day (Many regions)
		53701, // 09/Jan/2047, The Prophet Muhammad's Birthday
		53718, // 26/Jan/2047, Lunar New Year's Day
		53719, // 27/Jan/2047, Second Day of Lunar New Year (Most regions)
		53719, // 27/Jan/2047, Lunar New Year Holiday (Kelantan, Terengganu)
		53724, // 01/Feb/2047, Federal Territory Day (KUL, LBN, PJY)
		53813, // 01/May/2047, Labour Day
		53846, // 03/Jun/2047, The Yang di-Pertuan Agong's Birthday
		53883, // 10/Jul/2047, Nuzul Al-Quran (Most regions)
		53897, // 24/Jul/2047, Hari Raya Puasa
		53898, // 25/Jul/2047, Hari Raya Puasa Day 2
		53935, // 31/Aug/2047, Malaysia's National Day
		53951, // 16/Sep/2047, Malaysia Day
		53965, // 30/Sep/2047, Hari Raya Haji
		53965, // 30/Sep/2047, Hari Raya Haji holiday
		53986, // 21/Oct/2047, Muharram/New Year
		54051, // 25/Dec/2047, Christmas Day
		54056, // 30/Dec/2047, The Prophet Muhammad's Birthday
		54058, // 01/Jan/2048, New Year's Day (Many regions)
		54089, // 01/Feb/2048, Federal Territory Day (KUL, LBN, PJY)
		54102, // 14/Feb/2048, Lunar New Year's Day
		54103, // 15/Feb/2048, Second Day of Lunar New Year (Most regions)
		54103, // 15/Feb/2048, Lunar New Year Holiday (Kelantan, Terengganu)
		54179, // 01/May/2048, Labour Day
		54210, // 01/Jun/2048, The Yang di-Pertuan Agong's Birthday
		54238, // 29/Jun/2048, Nuzul Al-Quran (Most regions)
		54252, // 13/Jul/2048, Hari Raya Puasa
		54253, // 14/Jul/2048, Hari Raya Puasa Day 2
		54301, // 31/Aug/2048, Malaysia's National Day
		54317, // 16/Sep/2048, Malaysia Day
		54320, // 19/Sep/2048, Hari Raya Haji
		54320, // 19/Sep/2048, Hari Raya Haji holiday
		54340, // 09/Oct/2048, Muharram/New Year
		54410, // 18/Dec/2048, The Prophet Muhammad's Birthday
		54417, // 25/Dec/2048, Christmas Day
		54424, // 01/Jan/2049, New Year's Day (Many regions)
		54455, // 01/Feb/2049, Federal Territory Day (KUL, LBN, PJY)
		54456, // 02/Feb/2049, Lunar New Year's Day
		54457, // 03/Feb/2049, Second Day of Lunar New Year (Most regions)
		54457, // 03/Feb/2049, Lunar New Year Holiday (Kelantan, Terengganu)
		54544, // 01/May/2049, Labour Day
		54581, // 07/Jun/2049, The Yang di-Pertuan Agong's Birthday
		54592, // 18/Jun/2049, Nuzul Al-Quran (Most regions)
		54606, // 02/Jul/2049, Hari Raya Puasa
		54607, // 03/Jul/2049, Hari Raya Puasa Day 2
		54666, // 31/Aug/2049, Malaysia's National Day
		54674, // 08/Sep/2049, Hari Raya Haji
		54674, // 08/Sep/2049, Hari Raya Haji holiday
		54682, // 16/Sep/2049, Malaysia Day
		54694, // 28/Sep/2049, Muharram/New Year
		54764, // 07/Dec/2049, The Prophet Muhammad's Birthday
		54782, // 25/Dec/2049, Christmas Day
		54789, // 01/Jan/2050, New Year's Day (Many regions)
		54811, // 23/Jan/2050, Lunar New Year's Day
		54812, // 24/Jan/2050, Second Day of Lunar New Year (Most regions)
		54812, // 24/Jan/2050, Lunar New Year Holiday (Kelantan, Terengganu)
		54820, // 01/Feb/2050, Federal Territory Day (KUL, LBN, PJY)
		54909, // 01/May/2050, Labour Day
		54910, // 02/May/2050, 'Labour Day' observed
		54945, // 06/Jun/2050, The Yang di-Pertuan Agong's Birthday
		54946, // 07/Jun/2050, Nuzul Al-Quran (Most regions)
		54960, // 21/Jun/2050, Hari Raya Puasa
		54961, // 22/Jun/2050, Hari Raya Puasa Day 2
		55028, // 28/Aug/2050, Hari Raya Haji
		55028, // 28/Aug/2050, Hari Raya Haji holiday
		55031, // 31/Aug/2050, Malaysia's National Day
		55047, // 16/Sep/2050, Malaysia Day
		55049, // 18/Sep/2050, Muharram/New Year
		55119, // 27/Nov/2050, The Prophet Muhammad's Birthday
		55147, // 25/Dec/2050, Christmas Day
		55148, // 26/Dec/2050, 'Christmas Day' observed
		55154, // 01/Jan/2051, New Year's Day (Many regions)
		55155, // 02/Jan/2051, 'New Year's Day' observed (Many regions)
		55185, // 01/Feb/2051, Federal Territory Day (KUL, LBN, PJY)
		55195, // 11/Feb/2051, Lunar New Year's Day
		55196, // 12/Feb/2051, Second Day of Lunar New Year (Most regions)
		55196, // 12/Feb/2051, Lunar New Year Holiday (Kelantan, Terengganu)
		55274, // 01/May/2051, Labour Day
		55301, // 28/May/2051, Nuzul Al-Quran (Most regions)
		55309, // 05/Jun/2051, The Yang di-Pertuan Agong's Birthday
		55315, // 11/Jun/2051, Hari Raya Puasa
		55316, // 12/Jun/2051, Hari Raya Puasa Day 2
		55383, // 18/Aug/2051, Hari Raya Haji
		55383, // 18/Aug/2051, Hari Raya Haji holiday
		55396, // 31/Aug/2051, Malaysia's National Day
		55403, // 07/Sep/2051, Muharram/New Year
		55412, // 16/Sep/2051, Malaysia Day
		55473, // 16/Nov/2051, The Prophet Muhammad's Birthday
		55512, // 25/Dec/2051, Christmas Day
		55519, // 01/Jan/2052, New Year's Day (Many regions)
		55550, // 01/Feb/2052, Lunar New Year's Day
		55550, // 01/Feb/2052, Federal Territory Day (KUL, LBN, PJY)
		55551, // 02/Feb/2052, Second Day of Lunar New Year (Most regions)
		55551, // 02/Feb/2052, Lunar New Year Holiday (Kelantan, Terengganu)
		55640, // 01/May/2052, Labour Day
		55655, // 16/May/2052, Nuzul Al-Quran (Most regions)
		55669, // 30/May/2052, Hari Raya Puasa
		55670, // 31/May/2052, Hari Raya Puasa Day 2
		55673, // 03/Jun/2052, The Yang di-Pertuan Agong's Birthday
		55737, // 06/Aug/2052, Hari Raya Haji
		55737, // 06/Aug/2052, Hari Raya Haji holiday
		55757, // 26/Aug/2052, Muharram/New Year
		55762, // 31/Aug/2052, Malaysia's National Day
		55778, // 16/Sep/2052, Malaysia Day
		55827, // 04/Nov/2052, The Prophet Muhammad's Birthday
		55878, // 25/Dec/2052, Christmas Day
		55885, // 01/Jan/2053, New Year's Day (Many regions)
		55916, // 01/Feb/2053, Federal Territory Day (KUL, LBN, PJY)
		55934, // 19/Feb/2053, Lunar New Year's Day
		55935, // 20/Feb/2053, Second Day of Lunar New Year (Most regions)
		55935, // 20/Feb/2053, Lunar New Year Holiday (Kelantan, Terengganu)
		56005, // 01/May/2053, Labour Day
		56009, // 05/May/2053, Nuzul Al-Quran (Most regions)
		56023, // 19/May/2053, Hari Raya Puasa
		56024, // 20/May/2053, Hari Raya Puasa Day 2
		56037, // 02/Jun/2053, The Yang di-Pertuan Agong's Birthday
		56091, // 26/Jul/2053, Hari Raya Haji
		56091, // 26/Jul/2053, Hari Raya Haji holiday
		56112, // 16/Aug/2053, Muharram/New Year
		56127, // 31/Aug/2053, Malaysia's National Day
		56128, // 01/Sep/2053, 'Malaysia's National Day' observed
		56143, // 16/Sep/2053, Malaysia Day
		56182, // 25/Oct/2053, The Prophet Muhammad's Birthday
		56243, // 25/Dec/2053, Christmas Day
		56250, // 01/Jan/2054, New Year's Day (Many regions)
		56281, // 01/Feb/2054, Federal Territory Day (KUL, LBN, PJY)
		56282, // 02/Feb/2054, 'Federal Territory Day' observed (KUL, LBN, PJY)
		56288, // 08/Feb/2054, Lunar New Year's Day
		56289, // 09/Feb/2054, Second Day of Lunar New Year (Most regions)
		56289, // 09/Feb/2054, Lunar New Year Holiday (Kelantan, Terengganu)
		56364, // 25/Apr/2054, Nuzul Al-Quran (Most regions)
		56370, // 01/May/2054, Labour Day
		56378, // 09/May/2054, Hari Raya Puasa
		56379, // 10/May/2054, Hari Raya Puasa Day 2
		56401, // 01/Jun/2054, The Yang di-Pertuan Agong's Birthday
		56446, // 16/Jul/2054, Hari Raya Haji
		56446, // 16/Jul/2054, Hari Raya Haji holiday
		56466, // 05/Aug/2054, Muharram/New Year
		56492, // 31/Aug/2054, Malaysia's National Day
		56508, // 16/Sep/2054, Malaysia Day
		56536, // 14/Oct/2054, The Prophet Muhammad's Birthday
		56608, // 25/Dec/2054, Christmas Day
		56615, // 01/Jan/2055, New Year's Day (Many regions)
		56642, // 28/Jan/2055, Lunar New Year's Day
		56643, // 29/Jan/2055, Second Day of Lunar New Year (Most regions)
		56643, // 29/Jan/2055, Lunar New Year Holiday (Kelantan, Terengganu)
		56646, // 01/Feb/2055, Federal Territory Day (KUL, LBN, PJY)
		56718, // 14/Apr/2055, Nuzul Al-Quran (Most regions)
		56732, // 28/Apr/2055, Hari Raya Puasa
		56733, // 29/Apr/2055, Hari Raya Puasa Day 2
		56735, // 01/May/2055, Labour Day
		56772, // 07/Jun/2055, The Yang di-Pertuan Agong's Birthday
		56800, // 05/Jul/2055, Hari Raya Haji
		56800, // 05/Jul/2055, Hari Raya Haji holiday
		56821, // 26/Jul/2055, Muharram/New Year
		56857, // 31/Aug/2055, Malaysia's National Day
		56873, // 16/Sep/2055, Malaysia Day
		56891, // 04/Oct/2055, The Prophet Muhammad's Birthday
		56973, // 25/Dec/2055, Christmas Day
		56980, // 01/Jan/2056, New Year's Day (Many regions)
		57011, // 01/Feb/2056, Federal Territory Day (KUL, LBN, PJY)
		57025, // 15/Feb/2056, Lunar New Year's Day
		57026, // 16/Feb/2056, Second Day of Lunar New Year (Most regions)
		57026, // 16/Feb/2056, Lunar New Year Holiday (Kelantan, Terengganu)
		57073, // 03/Apr/2056, Nuzul Al-Quran (Most regions)
		57087, // 17/Apr/2056, Hari Raya Puasa
		57088, // 18/Apr/2056, Hari Raya Puasa Day 2
		57101, // 01/May/2056, Labour Day
		57136, // 05/Jun/2056, The Yang di-Pertuan Agong's Birthday
		57155, // 24/Jun/2056, Hari Raya Haji
		57155, // 24/Jun/2056, Hari Raya Haji holiday
		57175, // 14/Jul/2056, Muharram/New Year
		57223, // 31/Aug/2056, Malaysia's National Day
		57239, // 16/Sep/2056, Malaysia Day
		57245, // 22/Sep/2056, The Prophet Muhammad's Birthday
		57339, // 25/Dec/2056, Christmas Day
		57346, // 01/Jan/2057, New Year's Day (Many regions)
		57377, // 01/Feb/2057, Federal Territory Day (KUL, LBN, PJY)
		57380, // 04/Feb/2057, Lunar New Year's Day
		57381, // 05/Feb/2057, Second Day of Lunar New Year (Most regions)
		57381, // 05/Feb/2057, Lunar New Year Holiday (Kelantan, Terengganu)
		57427, // 23/Mar/2057, Nuzul Al-Quran (Most regions)
		57441, // 06/Apr/2057, Hari Raya Puasa
		57442, // 07/Apr/2057, Hari Raya Puasa Day 2
		57466, // 01/May/2057, Labour Day
		57500, // 04/Jun/2057, The Yang di-Pertuan Agong's Birthday
		57509, // 13/Jun/2057, Hari Raya Haji
		57509, // 13/Jun/2057, Hari Raya Haji holiday
		57529, // 03/Jul/2057, Muharram/New Year
		57588, // 31/Aug/2057, Malaysia's National Day
		57599, // 11/Sep/2057, The Prophet Muhammad's Birthday
		57604, // 16/Sep/2057, Malaysia Day
		57704, // 25/Dec/2057, Christmas Day
		57711, // 01/Jan/2058, New Year's Day (Many regions)
		57734, // 24/Jan/2058, Lunar New Year's Day
		57735, // 25/Jan/2058, Second Day of Lunar New Year (Most regions)
		57735, // 25/Jan/2058, Lunar New Year Holiday (Kelantan, Terengganu)
		57742, // 01/Feb/2058, Federal Territory Day (KUL, LBN, PJY)
		57781, // 12/Mar/2058, Nuzul Al-Quran (Most regions)
		57795, // 26/Mar/2058, Hari Raya Puasa
		57796, // 27/Mar/2058, Hari Raya Puasa Day 2
		57831, // 01/May/2058, Labour Day
		57863, // 02/Jun/2058, Hari Raya Haji
		57863, // 02/Jun/2058, Hari Raya Haji holiday
		57864, // 03/Jun/2058, The Yang di-Pertuan Agong's Birthday
		57884, // 23/Jun/2058, Muharram/New Year
		57953, // 31/Aug/2058, Malaysia's National Day
		57954, // 01/Sep/2058, The Prophet Muhammad's Birthday
		57969, // 16/Sep/2058, Malaysia Day
		58069, // 25/Dec/2058, Christmas Day
		58076, // 01/Jan/2059, New Year's Day (Many regions)
		58107, // 01/Feb/2059, Federal Territory Day (KUL, LBN, PJY)
		58118, // 12/Feb/2059, Lunar New Year's Day
		58119, // 13/Feb/2059, Second Day of Lunar New Year (Most regions)
		58119, // 13/Feb/2059, Lunar New Year Holiday (Kelantan, Terengganu)
		58136, // 02/Mar/2059, Nuzul Al-Quran (Most regions)
		58150, // 16/Mar/2059, Hari Raya Puasa
		58151, // 17/Mar/2059, Hari Raya Puasa Day 2
		58196, // 01/May/2059, Labour Day
		58218, // 23/May/2059, Hari Raya Haji
		58218, // 23/May/2059, Hari Raya Haji holiday
		58228, // 02/Jun/2059, The Yang di-Pertuan Agong's Birthday
		58238, // 12/Jun/2059, Muharram/New Year
		58308, // 21/Aug/2059, The Prophet Muhammad's Birthday
		58318, // 31/Aug/2059, Malaysia's National Day
		58319, // 01/Sep/2059, 'Malaysia's National Day' observed
		58334, // 16/Sep/2059, Malaysia Day
		58434, // 25/Dec/2059, Christmas Day
		58441, // 01/Jan/2060, New Year's Day (Many regions)
		58472, // 01/Feb/2060, Federal Territory Day (KUL, LBN, PJY)
		58473, // 02/Feb/2060, Lunar New Year's Day
		58473, // 02/Feb/2060, 'Federal Territory Day' observed (KUL, LBN, PJY)
		58474, // 03/Feb/2060, Second Day of Lunar New Year (Most regions)
		58474, // 03/Feb/2060, Lunar New Year Holiday (Kelantan, Terengganu)
		58490, // 19/Feb/2060, Nuzul Al-Quran (Most regions)
		58504, // 04/Mar/2060, Hari Raya Puasa
		58505, // 05/Mar/2060, Hari Raya Puasa Day 2
		58562, // 01/May/2060, Labour Day
		58572, // 11/May/2060, Hari Raya Haji
		58572, // 11/May/2060, Hari Raya Haji holiday
		58592, // 31/May/2060, Muharram/New Year
		58599, // 07/Jun/2060, The Yang di-Pertuan Agong's Birthday
		58662, // 09/Aug/2060, The Prophet Muhammad's Birthday
		58684, // 31/Aug/2060, Malaysia's National Day
		58700, // 16/Sep/2060, Malaysia Day
		58800, // 25/Dec/2060, Christmas Day
		58807, // 01/Jan/2061, New Year's Day (Many regions)
		58827, // 21/Jan/2061, Lunar New Year's Day
		58828, // 22/Jan/2061, Second Day of Lunar New Year (Most regions)
		58828, // 22/Jan/2061, Lunar New Year Holiday (Kelantan, Terengganu)
		58838, // 01/Feb/2061, Federal Territory Day (KUL, LBN, PJY)
		58844, // 07/Feb/2061, Nuzul Al-Quran (Most regions)
		58858, // 21/Feb/2061, Hari Raya Puasa
		58859, // 22/Feb/2061, Hari Raya Puasa Day 2
		58926, // 30/Apr/2061, Hari Raya Haji
		58926, // 30/Apr/2061, Hari Raya Haji holiday
		58927, // 01/May/2061, Labour Day
		58928, // 02/May/2061, 'Labour Day' observed
		58947, // 21/May/2061, Muharram/New Year
		58963, // 06/Jun/2061, The Yang di-Pertuan Agong's Birthday
		59017, // 30/Jul/2061, The Prophet Muhammad's Birthday
		59049, // 31/Aug/2061, Malaysia's National Day
		59065, // 16/Sep/2061, Malaysia Day
		59165, // 25/Dec/2061, Christmas Day
		59166, // 26/Dec/2061, 'Christmas Day' observed
		59172, // 01/Jan/2062, New Year's Day (Many regions)
		59173, // 02/Jan/2062, 'New Year's Day' observed (Many regions)
		59199, // 28/Jan/2062, Nuzul Al-Quran (Most regions)
		59203, // 01/Feb/2062, Federal Territory Day (KUL, LBN, PJY)
		59211, // 09/Feb/2062, Lunar New Year's Day
		59212, // 10/Feb/2062, Second Day of Lunar New Year (Most regions)
		59212, // 10/Feb/2062, Lunar New Year Holiday (Kelantan, Terengganu)
		59213, // 11/Feb/2062, Hari Raya Puasa
		59214, // 12/Feb/2062, Hari Raya Puasa Day 2
		59281, // 20/Apr/2062, Hari Raya Haji
		59281, // 20/Apr/2062, Hari Raya Haji holiday
		59292, // 01/May/2062, Labour Day
		59301, // 10/May/2062, Muharram/New Year
		59327, // 05/Jun/2062, The Yang di-Pertuan Agong's Birthday
		59371, // 19/Jul/2062, The Prophet Muhammad's Birthday
		59414, // 31/Aug/2062, Malaysia's National Day
		59430, // 16/Sep/2062, Malaysia Day
		59530, // 25/Dec/2062, Christmas Day
		59537, // 01/Jan/2063, New Year's Day (Many regions)
		59553, // 17/Jan/2063, Nuzul Al-Quran (Most regions)
		59565, // 29/Jan/2063, Lunar New Year's Day
		59566, // 30/Jan/2063, Second Day of Lunar New Year (Most regions)
		59566, // 30/Jan/2063, Lunar New Year Holiday (Kelantan, Terengganu)
		59567, // 31/Jan/2063, Hari Raya Puasa
		59568, // 01/Feb/2063, Federal Territory Day (KUL, LBN, PJY)
		59568, // 01/Feb/2063, Hari Raya Puasa Day 2
		59635, // 09/Apr/2063, Hari Raya Haji
		59635, // 09/Apr/2063, Hari Raya Haji holiday
		59655, // 29/Apr/2063, Muharram/New Year
		59657, // 01/May/2063, Labour Day
		59691, // 04/Jun/2063, The Yang di-Pertuan Agong's Birthday
		59725, // 08/Jul/2063, The Prophet Muhammad's Birthday
		59779, // 31/Aug/2063, Malaysia's National Day
		59795, // 16/Sep/2063, Malaysia Day
		59895, // 25/Dec/2063, Christmas Day
		59902, // 01/Jan/2064, New Year's Day (Many regions)
		59907, // 06/Jan/2064, Nuzul Al-Quran (Most regions)
		59921, // 20/Jan/2064, Hari Raya Puasa
		59922, // 21/Jan/2064, Hari Raya Puasa Day 2
		59933, // 01/Feb/2064, Federal Territory Day (KUL, LBN, PJY)
		59949, // 17/Feb/2064, Lunar New Year's Day
		59950, // 18/Feb/2064, Second Day of Lunar New Year (Most regions)
		59950, // 18/Feb/2064, Lunar New Year Holiday (Kelantan, Terengganu)
		59989, // 28/Mar/2064, Hari Raya Haji
		59989, // 28/Mar/2064, Hari Raya Haji holiday
		60010, // 18/Apr/2064, Muharram/New Year
		60023, // 01/May/2064, Labour Day
		60055, // 02/Jun/2064, The Yang di-Pertuan Agong's Birthday
		60080, // 27/Jun/2064, The Prophet Muhammad's Birthday
		60145, // 31/Aug/2064, Malaysia's National Day
		60146, // 01/Sep/2064, 'Malaysia's National Day' observed
		60161, // 16/Sep/2064, Malaysia Day
		60261, // 25/Dec/2064, Christmas Day
		60262, // 26/Dec/2064, Nuzul Al-Quran (Most regions)
		60268, // 01/Jan/2065, New Year's Day (Many regions)
		60276, // 09/Jan/2065, Hari Raya Puasa
		60277, // 10/Jan/2065, Hari Raya Puasa Day 2
		60299, // 01/Feb/2065, Federal Territory Day (KUL, LBN, PJY)
		60300, // 02/Feb/2065, 'Federal Territory Day' observed (KUL, LBN, PJY)
		60303, // 05/Feb/2065, Lunar New Year's Day
		60304, // 06/Feb/2065, Second Day of Lunar New Year (Most regions)
		60304, // 06/Feb/2065, Lunar New Year Holiday (Kelantan, Terengganu)
		60344, // 18/Mar/2065, Hari Raya Haji
		60344, // 18/Mar/2065, Hari Raya Haji holiday
		60364, // 07/Apr/2065, Muharram/New Year
		60388, // 01/May/2065, Labour Day
		60419, // 01/Jun/2065, The Yang di-Pertuan Agong's Birthday
		60434, // 16/Jun/2065, The Prophet Muhammad's Birthday
		60510, // 31/Aug/2065, Malaysia's National Day
		60526, // 16/Sep/2065, Malaysia Day
		60616, // 15/Dec/2065, Nuzul Al-Quran (Most regions)
		60626, // 25/Dec/2065, Christmas Day
		60630, // 29/Dec/2065, Hari Raya Puasa
		60631, // 30/Dec/2065, Hari Raya Puasa Day 2
		60633, // 01/Jan/2066, New Year's Day (Many regions)
		60658, // 26/Jan/2066, Lunar New Year's Day
		60659, // 27/Jan/2066, Second Day of Lunar New Year (Most regions)
		60659, // 27/Jan/2066, Lunar New Year Holiday (Kelantan, Terengganu)
		60664, // 01/Feb/2066, Federal Territory Day (KUL, LBN, PJY)
		60698, // 07/Mar/2066, Hari Raya Haji
		60698, // 07/Mar/2066, Hari Raya Haji holiday
		60719, // 28/Mar/2066, Muharram/New Year
		60753, // 01/May/2066, Labour Day
		60789, // 06/Jun/2066, The Prophet Muhammad's Birthday
		60790, // 07/Jun/2066, The Yang di-Pertuan Agong's Birthday
		60875, // 31/Aug/2066, Malaysia's National Day
		60891, // 16/Sep/2066, Malaysia Day
		60971, // 05/Dec/2066, Nuzul Al-Quran (Most regions)
		60985, // 19/Dec/2066, Hari Raya Puasa
		60986, // 20/Dec/2066, Hari Raya Puasa Day 2
		60991, // 25/Dec/2066, Christmas Day
		60998, // 01/Jan/2067, New Year's Day (Many regions)
		61029, // 01/Feb/2067, Federal Territory Day (KUL, LBN, PJY)
		61042, // 14/Feb/2067, Lunar New Year's Day
		61043, // 15/Feb/2067, Second Day of Lunar New Year (Most regions)
		61043, // 15/Feb/2067, Lunar New Year Holiday (Kelantan, Terengganu)
		61053, // 25/Feb/2067, Hari Raya Haji
		61053, // 25/Feb/2067, Hari Raya Haji holiday
		61073, // 17/Mar/2067, Muharram/New Year
		61118, // 01/May/2067, Labour Day
		61119, // 02/May/2067, 'Labour Day' observed
		61143, // 26/May/2067, The Prophet Muhammad's Birthday
		61154, // 06/Jun/2067, The Yang di-Pertuan Agong's Birthday
		61240, // 31/Aug/2067, Malaysia's National Day
		61256, // 16/Sep/2067, Malaysia Day
		61325, // 24/Nov/2067, Nuzul Al-Quran (Most regions)
		61339, // 08/Dec/2067, Hari Raya Puasa
		61340, // 09/Dec/2067, Hari Raya Puasa Day 2
		61356, // 25/Dec/2067, Christmas Day
		61357, // 26/Dec/2067, 'Christmas Day' observed
		61363, // 01/Jan/2068, New Year's Day (Many regions)
		61364, // 02/Jan/2068, 'New Year's Day' observed (Many regions)
		61394, // 01/Feb/2068, Federal Territory Day (KUL, LBN, PJY)
		61396, // 03/Feb/2068, Lunar New Year's Day
		61397, // 04/Feb/2068, Second Day of Lunar New Year (Most regions)
		61397, // 04/Feb/2068, Lunar New Year Holiday (Kelantan, Terengganu)
		61407, // 14/Feb/2068, Hari Raya Haji
		61407, // 14/Feb/2068, Hari Raya Haji holiday
		61427, // 05/Mar/2068, Muharram/New Year
		61484, // 01/May/2068, Labour Day
		61497, // 14/May/2068, The Prophet Muhammad's Birthday
		61518, // 04/Jun/2068, The Yang di-Pertuan Agong's Birthday
		61606, // 31/Aug/2068, Malaysia's National Day
		61622, // 16/Sep/2068, Malaysia Day
		61679, // 12/Nov/2068, Nuzul Al-Quran (Most regions)
		61693, // 26/Nov/2068, Hari Raya Puasa
		61694, // 27/Nov/2068, Hari Raya Puasa Day 2
		61722, // 25/Dec/2068, Christmas Day
		61729, // 01/Jan/2069, New Year's Day (Many regions)
		61751, // 23/Jan/2069, Lunar New Year's Day
		61752, // 24/Jan/2069, Second Day of Lunar New Year (Most regions)
		61752, // 24/Jan/2069, Lunar New Year Holiday (Kelantan, Terengganu)
		61760, // 01/Feb/2069, Federal Territory Day (KUL, LBN, PJY)
		61761, // 02/Feb/2069, Hari Raya Haji
		61761, // 02/Feb/2069, Hari Raya Haji holiday
		61782, // 23/Feb/2069, Muharram/New Year
		61849, // 01/May/2069, Labour Day
		61852, // 04/May/2069, The Prophet Muhammad's Birthday
		61882, // 03/Jun/2069, The Yang di-Pertuan Agong's Birthday
		61971, // 31/Aug/2069, Malaysia's National Day
		61987, // 16/Sep/2069, Malaysia Day
		62034, // 02/Nov/2069, Nuzul Al-Quran (Most regions)
		62048, // 16/Nov/2069, Hari Raya Puasa
		62049, // 17/Nov/2069, Hari Raya Puasa Day 2
		62087, // 25/Dec/2069, Christmas Day
		62094, // 01/Jan/2070, New Year's Day (Many regions)
		62116, // 23/Jan/2070, Hari Raya Haji
		62116, // 23/Jan/2070, Hari Raya Haji holiday
		62125, // 01/Feb/2070, Federal Territory Day (KUL, LBN, PJY)
		62135, // 11/Feb/2070, Lunar New Year's Day
		62136, // 12/Feb/2070, Second Day of Lunar New Year (Most regions)
		62136, // 12/Feb/2070, Lunar New Year Holiday (Kelantan, Terengganu)
		62136, // 12/Feb/2070, Muharram/New Year
		62206, // 23/Apr/2070, The Prophet Muhammad's Birthday
		62214, // 01/May/2070, Labour Day
		62246, // 02/Jun/2070, The Yang di-Pertuan Agong's Birthday
		62336, // 31/Aug/2070, Malaysia's National Day
		62337, // 01/Sep/2070, 'Malaysia's National Day' observed
		62352, // 16/Sep/2070, Malaysia Day
		62388, // 22/Oct/2070, Nuzul Al-Quran (Most regions)
		62402, // 05/Nov/2070, Hari Raya Puasa
		62403, // 06/Nov/2070, Hari Raya Puasa Day 2
		62452 // 25/Dec/2070, Christmas Day
	};
}
