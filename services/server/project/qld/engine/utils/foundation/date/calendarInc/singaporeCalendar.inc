namespace QLD {
	int SingaporeCalendar::holidays[] = {
		43831, // 01/Jan/2020, New Year's Day
		43855, // 25/Jan/2020, Lunar New Year's Day
		43856, // 26/Jan/2020, Second Day of Lunar New Year
		43857, // 27/Jan/2020, Lunar New Year Holiday
		43931, // 10/Apr/2020, Good Friday
		43952, // 01/May/2020, Labour Day
		43958, // 07/May/2020, Vesak Day
		43975, // 24/May/2020, Hari Raya Puasa
		43976, // 25/May/2020, 'Hari Raya Puasa' observed
		44022, // 10/Jul/2020, 2020 Polling Day
		44043, // 31/Jul/2020, Hari Raya Haji
		44052, // 09/Aug/2020, National Day
		44053, // 10/Aug/2020, 'National Day' observed
		44149, // 14/Nov/2020, Diwali/Deepavali
		44190, // 25/Dec/2020, Christmas Day
		44197, // 01/Jan/2021, New Year's Day
		44239, // 12/Feb/2021, Lunar New Year's Day
		44240, // 13/Feb/2021, Second Day of Lunar New Year
		44288, // 02/Apr/2021, Good Friday
		44317, // 01/May/2021, Labour Day
		44329, // 13/May/2021, Hari Raya Puasa
		44342, // 26/May/2021, Vesak Day
		44397, // 20/Jul/2021, Hari Raya Haji
		44417, // 09/Aug/2021, National Day
		44504, // 04/Nov/2021, Diwali/Deepavali
		44555, // 25/Dec/2021, Christmas Day
		44562, // 01/Jan/2022, New Year's Day
		44593, // 01/Feb/2022, Lunar New Year's Day
		44594, // 02/Feb/2022, Second Day of Lunar New Year
		44666, // 15/Apr/2022, Good Friday
		44682, // 01/May/2022, Labour Day
		44683, // 02/May/2022, 'Labour Day' day off
		44684, // 03/May/2022, Hari Raya Puasa
		44696, // 15/May/2022, Vesak Day
		44697, // 16/May/2022, 'Vesak Day' day off
		44752, // 10/Jul/2022, Hari Raya Haji
		44753, // 11/Jul/2022, 'Hari Raya Haji' day off
		44782, // 09/Aug/2022, National Day
		44858, // 24/Oct/2022, Diwali/Deepavali
		44920, // 25/Dec/2022, Christmas Day
		44921, // 26/Dec/2022, 'Christmas Day' day off
		44927, // 01/Jan/2023, New Year's Day
		44928, // 02/Jan/2023, 'New Year's Day' observed
		44948, // 22/Jan/2023, Lunar New Year's Day
		44949, // 23/Jan/2023, Second Day of Lunar New Year
		44950, // 24/Jan/2023, 'Lunar New Year's Day' day off
		45023, // 07/Apr/2023, Good Friday
		45038, // 22/Apr/2023, Hari Raya Puasa
		45047, // 01/May/2023, Labour Day
		45079, // 02/Jun/2023, Vesak Day
		45106, // 29/Jun/2023, Hari Raya Haji
		45147, // 09/Aug/2023, National Day
		45242, // 12/Nov/2023, Diwali/Deepavali
		45243, // 13/Nov/2023, 'Diwali/Deepavali' day off
		45285, // 25/Dec/2023, Christmas Day
		45292, // 01/Jan/2024, New Year's Day
		45332, // 10/Feb/2024, Lunar New Year's Day
		45333, // 11/Feb/2024, Second Day of Lunar New Year
		45334, // 12/Feb/2024, 'Lunar New Year's Day' day off
		45380, // 29/Mar/2024, Good Friday
		45392, // 10/Apr/2024, Hari Raya Puasa
		45413, // 01/May/2024, Labour Day
		45434, // 22/May/2024, Vesak Day
		45460, // 17/Jun/2024, Hari Raya Haji
		45513, // 09/Aug/2024, National Day
		45596, // 31/Oct/2024, Diwali/Deepavali
		45651, // 25/Dec/2024, Christmas Day
		45658, // 01/Jan/2025, New Year's Day
		45686, // 29/Jan/2025, Lunar New Year's Day
		45747, // 31/Mar/2025, Hari Raya Puasa
		45765, // 18/Apr/2025, Good Friday
		45778, // 01/May/2025, Labour Day
		45789, // 12/May/2025, Vesak Day
		45814, // 06/Jun/2025, Hari Raya Haji
		45878, // 09/Aug/2025, National Day
		45951, // 21/Oct/2025, Diwali/Deepavali
		46016, // 25/Dec/2025, Christmas Day
		46023, // 01/Jan/2026, New Year's Day
		46070, // 17/Feb/2026, Lunar New Year's Day
		46101, // 20/Mar/2026, Hari Raya Puasa
		46115, // 03/Apr/2026, Good Friday
		46143, // 01/May/2026, Labour Day
		46243, // 09/Aug/2026, National Day
		46244, // 10/Aug/2026, 'National Day' observed
		46334, // 08/Nov/2026, Diwali/Deepavali
		46335, // 09/Nov/2026, 'Diwali/Deepavali' day off
		46381, // 25/Dec/2026, Christmas Day
		46388, // 01/Jan/2027, New Year's Day
		46424, // 06/Feb/2027, Lunar New Year's Day
		46456, // 10/Mar/2027, Hari Raya Puasa
		46472, // 26/Mar/2027, Good Friday
		46508, // 01/May/2027, Labour Day
		46608, // 09/Aug/2027, National Day
		46689, // 29/Oct/2027, Diwali/Deepavali
		46746, // 25/Dec/2027, Christmas Day
		46753, // 01/Jan/2028, New Year's Day
		46778, // 26/Jan/2028, Lunar New Year's Day
		46810, // 27/Feb/2028, Hari Raya Puasa
		46857, // 14/Apr/2028, Good Friday
		46874, // 01/May/2028, Labour Day
		46974, // 09/Aug/2028, National Day
		47043, // 17/Oct/2028, Diwali/Deepavali
		47112, // 25/Dec/2028, Christmas Day
		47119, // 01/Jan/2029, New Year's Day
		47162, // 13/Feb/2029, Lunar New Year's Day
		47164, // 15/Feb/2029, Hari Raya Puasa
		47207, // 30/Mar/2029, Good Friday
		47239, // 01/May/2029, Labour Day
		47339, // 09/Aug/2029, National Day
		47427, // 05/Nov/2029, Diwali/Deepavali
		47477, // 25/Dec/2029, Christmas Day
		47484, // 01/Jan/2030, New Year's Day
		47518, // 04/Feb/2030, Lunar New Year's Day
		47519, // 05/Feb/2030, Hari Raya Puasa
		47592, // 19/Apr/2030, Good Friday
		47604, // 01/May/2030, Labour Day
		47704, // 09/Aug/2030, National Day
		47782, // 26/Oct/2030, Diwali/Deepavali
		47842, // 25/Dec/2030, Christmas Day
		47849, // 01/Jan/2031, New Year's Day
		47871, // 23/Jan/2031, Lunar New Year's Day
		47873, // 25/Jan/2031, Hari Raya Puasa
		47949, // 11/Apr/2031, Good Friday
		47969, // 01/May/2031, Labour Day
		48069, // 09/Aug/2031, National Day
		48207, // 25/Dec/2031, Christmas Day
		48214, // 01/Jan/2032, New Year's Day
		48227, // 14/Jan/2032, Hari Raya Puasa
		48255, // 11/Feb/2032, Lunar New Year's Day
		48299, // 26/Mar/2032, Good Friday
		48335, // 01/May/2032, Labour Day
		48435, // 09/Aug/2032, National Day
		48573, // 25/Dec/2032, Christmas Day
		48580, // 01/Jan/2033, New Year's Day
		48582, // 03/Jan/2033, Hari Raya Puasa
		48610, // 31/Jan/2033, Lunar New Year's Day
		48684, // 15/Apr/2033, Good Friday
		48700, // 01/May/2033, Labour Day
		48701, // 02/May/2033, 'Labour Day' day off
		48800, // 09/Aug/2033, National Day
		48936, // 23/Dec/2033, Hari Raya Puasa
		48938, // 25/Dec/2033, Christmas Day
		48939, // 26/Dec/2033, 'Christmas Day' day off
		48945, // 01/Jan/2034, New Year's Day
		48946, // 02/Jan/2034, 'New Year's Day' observed
		48995, // 20/Feb/2034, Lunar New Year's Day
		49041, // 07/Apr/2034, Good Friday
		49065, // 01/May/2034, Labour Day
		49165, // 09/Aug/2034, National Day
		49290, // 12/Dec/2034, Hari Raya Puasa
		49303, // 25/Dec/2034, Christmas Day
		49310, // 01/Jan/2035, New Year's Day
		49348, // 08/Feb/2035, Lunar New Year's Day
		49391, // 23/Mar/2035, Good Friday
		49430, // 01/May/2035, Labour Day
		49530, // 09/Aug/2035, National Day
		49645, // 02/Dec/2035, Hari Raya Puasa
		49668, // 25/Dec/2035, Christmas Day
		49675, // 01/Jan/2036, New Year's Day
		49702, // 28/Jan/2036, Lunar New Year's Day
		49776, // 11/Apr/2036, Good Friday
		49796, // 01/May/2036, Labour Day
		49896, // 09/Aug/2036, National Day
		49999, // 20/Nov/2036, Hari Raya Puasa
		50034, // 25/Dec/2036, Christmas Day
		50041, // 01/Jan/2037, New Year's Day
		50087, // 16/Feb/2037, Lunar New Year's Day
		50133, // 03/Apr/2037, Good Friday
		50161, // 01/May/2037, Labour Day
		50261, // 09/Aug/2037, National Day
		50262, // 10/Aug/2037, 'National Day' observed
		50354, // 10/Nov/2037, Hari Raya Puasa
		50399, // 25/Dec/2037, Christmas Day
		50406, // 01/Jan/2038, New Year's Day
		50440, // 04/Feb/2038, Lunar New Year's Day
		50518, // 23/Apr/2038, Good Friday
		50526, // 01/May/2038, Labour Day
		50626, // 09/Aug/2038, National Day
		50708, // 30/Oct/2038, Hari Raya Puasa
		50764, // 25/Dec/2038, Christmas Day
		50771, // 01/Jan/2039, New Year's Day
		50794, // 24/Jan/2039, Lunar New Year's Day
		50868, // 08/Apr/2039, Good Friday
		50891, // 01/May/2039, Labour Day
		50892, // 02/May/2039, 'Labour Day' day off
		50991, // 09/Aug/2039, National Day
		51062, // 19/Oct/2039, Hari Raya Puasa
		51129, // 25/Dec/2039, Christmas Day
		51130, // 26/Dec/2039, 'Christmas Day' day off
		51136, // 01/Jan/2040, New Year's Day
		51137, // 02/Jan/2040, 'New Year's Day' observed
		51179, // 13/Feb/2040, Lunar New Year's Day
		51225, // 30/Mar/2040, Good Friday
		51257, // 01/May/2040, Labour Day
		51357, // 09/Aug/2040, National Day
		51417, // 08/Oct/2040, Hari Raya Puasa
		51495, // 25/Dec/2040, Christmas Day
		51502, // 01/Jan/2041, New Year's Day
		51533, // 01/Feb/2041, Lunar New Year's Day
		51610, // 19/Apr/2041, Good Friday
		51622, // 01/May/2041, Labour Day
		51722, // 09/Aug/2041, National Day
		51771, // 27/Sep/2041, Hari Raya Puasa
		51860, // 25/Dec/2041, Christmas Day
		51867, // 01/Jan/2042, New Year's Day
		51888, // 22/Jan/2042, Lunar New Year's Day
		51960, // 04/Apr/2042, Good Friday
		51987, // 01/May/2042, Labour Day
		52087, // 09/Aug/2042, National Day
		52125, // 16/Sep/2042, Hari Raya Puasa
		52225, // 25/Dec/2042, Christmas Day
		52232, // 01/Jan/2043, New Year's Day
		52272, // 10/Feb/2043, Lunar New Year's Day
		52317, // 27/Mar/2043, Good Friday
		52352, // 01/May/2043, Labour Day
		52452, // 09/Aug/2043, National Day
		52453, // 10/Aug/2043, 'National Day' observed
		52480, // 06/Sep/2043, Hari Raya Puasa
		52590, // 25/Dec/2043, Christmas Day
		52597, // 01/Jan/2044, New Year's Day
		52626, // 30/Jan/2044, Lunar New Year's Day
		52702, // 15/Apr/2044, Good Friday
		52718, // 01/May/2044, Labour Day
		52719, // 02/May/2044, 'Labour Day' day off
		52818, // 09/Aug/2044, National Day
		52834, // 25/Aug/2044, Hari Raya Puasa
		52956, // 25/Dec/2044, Christmas Day
		52957, // 26/Dec/2044, 'Christmas Day' day off
		52963, // 01/Jan/2045, New Year's Day
		52964, // 02/Jan/2045, 'New Year's Day' observed
		53010, // 17/Feb/2045, Lunar New Year's Day
		53059, // 07/Apr/2045, Good Friday
		53083, // 01/May/2045, Labour Day
		53183, // 09/Aug/2045, National Day
		53189, // 15/Aug/2045, Hari Raya Puasa
		53321, // 25/Dec/2045, Christmas Day
		53328, // 01/Jan/2046, New Year's Day
		53364, // 06/Feb/2046, Lunar New Year's Day
		53409, // 23/Mar/2046, Good Friday
		53448, // 01/May/2046, Labour Day
		53543, // 04/Aug/2046, Hari Raya Puasa
		53548, // 09/Aug/2046, National Day
		53686, // 25/Dec/2046, Christmas Day
		53693, // 01/Jan/2047, New Year's Day
		53718, // 26/Jan/2047, Lunar New Year's Day
		53794, // 12/Apr/2047, Good Friday
		53813, // 01/May/2047, Labour Day
		53897, // 24/Jul/2047, Hari Raya Puasa
		53913, // 09/Aug/2047, National Day
		54051, // 25/Dec/2047, Christmas Day
		54058, // 01/Jan/2048, New Year's Day
		54102, // 14/Feb/2048, Lunar New Year's Day
		54151, // 03/Apr/2048, Good Friday
		54179, // 01/May/2048, Labour Day
		54252, // 13/Jul/2048, Hari Raya Puasa
		54279, // 09/Aug/2048, National Day
		54280, // 10/Aug/2048, 'National Day' observed
		54417, // 25/Dec/2048, Christmas Day
		54424, // 01/Jan/2049, New Year's Day
		54456, // 02/Feb/2049, Lunar New Year's Day
		54529, // 16/Apr/2049, Good Friday
		54544, // 01/May/2049, Labour Day
		54606, // 02/Jul/2049, Hari Raya Puasa
		54644, // 09/Aug/2049, National Day
		54782, // 25/Dec/2049, Christmas Day
		54789, // 01/Jan/2050, New Year's Day
		54812, // 24/Jan/2050, Lunar New Year's Day
		54886, // 08/Apr/2050, Good Friday
		54909, // 01/May/2050, Labour Day
		54910, // 02/May/2050, 'Labour Day' day off
		54960, // 21/Jun/2050, Hari Raya Puasa
		55009, // 09/Aug/2050, National Day
		55147, // 25/Dec/2050, Christmas Day
		55148, // 26/Dec/2050, 'Christmas Day' day off
		55154, // 01/Jan/2051, New Year's Day
		55155, // 02/Jan/2051, 'New Year's Day' observed
		55195, // 11/Feb/2051, Lunar New Year's Day
		55243, // 31/Mar/2051, Good Friday
		55274, // 01/May/2051, Labour Day
		55315, // 11/Jun/2051, Hari Raya Puasa
		55374, // 09/Aug/2051, National Day
		55512, // 25/Dec/2051, Christmas Day
		55519, // 01/Jan/2052, New Year's Day
		55550, // 01/Feb/2052, Lunar New Year's Day
		55628, // 19/Apr/2052, Good Friday
		55640, // 01/May/2052, Labour Day
		55669, // 30/May/2052, Hari Raya Puasa
		55740, // 09/Aug/2052, National Day
		55878, // 25/Dec/2052, Christmas Day
		55885, // 01/Jan/2053, New Year's Day
		55934, // 19/Feb/2053, Lunar New Year's Day
		55978, // 04/Apr/2053, Good Friday
		56005, // 01/May/2053, Labour Day
		56023, // 19/May/2053, Hari Raya Puasa
		56105, // 09/Aug/2053, National Day
		56243, // 25/Dec/2053, Christmas Day
		56250, // 01/Jan/2054, New Year's Day
		56289, // 09/Feb/2054, Lunar New Year's Day
		56335, // 27/Mar/2054, Good Friday
		56370, // 01/May/2054, Labour Day
		56378, // 09/May/2054, Hari Raya Puasa
		56470, // 09/Aug/2054, National Day
		56471, // 10/Aug/2054, 'National Day' observed
		56608, // 25/Dec/2054, Christmas Day
		56615, // 01/Jan/2055, New Year's Day
		56642, // 28/Jan/2055, Lunar New Year's Day
		56720, // 16/Apr/2055, Good Friday
		56732, // 28/Apr/2055, Hari Raya Puasa
		56735, // 01/May/2055, Labour Day
		56835, // 09/Aug/2055, National Day
		56973, // 25/Dec/2055, Christmas Day
		56980, // 01/Jan/2056, New Year's Day
		57025, // 15/Feb/2056, Lunar New Year's Day
		57070, // 31/Mar/2056, Good Friday
		57087, // 17/Apr/2056, Hari Raya Puasa
		57101, // 01/May/2056, Labour Day
		57201, // 09/Aug/2056, National Day
		57339, // 25/Dec/2056, Christmas Day
		57346, // 01/Jan/2057, New Year's Day
		57381, // 05/Feb/2057, Lunar New Year's Day
		57441, // 06/Apr/2057, Hari Raya Puasa
		57455, // 20/Apr/2057, Good Friday
		57466, // 01/May/2057, Labour Day
		57566, // 09/Aug/2057, National Day
		57704, // 25/Dec/2057, Christmas Day
		57711, // 01/Jan/2058, New Year's Day
		57734, // 24/Jan/2058, Lunar New Year's Day
		57795, // 26/Mar/2058, Hari Raya Puasa
		57812, // 12/Apr/2058, Good Friday
		57831, // 01/May/2058, Labour Day
		57931, // 09/Aug/2058, National Day
		58069, // 25/Dec/2058, Christmas Day
		58076, // 01/Jan/2059, New Year's Day
		58118, // 12/Feb/2059, Lunar New Year's Day
		58150, // 16/Mar/2059, Hari Raya Puasa
		58162, // 28/Mar/2059, Good Friday
		58196, // 01/May/2059, Labour Day
		58296, // 09/Aug/2059, National Day
		58434, // 25/Dec/2059, Christmas Day
		58441, // 01/Jan/2060, New Year's Day
		58473, // 02/Feb/2060, Lunar New Year's Day
		58504, // 04/Mar/2060, Hari Raya Puasa
		58547, // 16/Apr/2060, Good Friday
		58562, // 01/May/2060, Labour Day
		58662, // 09/Aug/2060, National Day
		58800, // 25/Dec/2060, Christmas Day
		58807, // 01/Jan/2061, New Year's Day
		58827, // 21/Jan/2061, Lunar New Year's Day
		58858, // 21/Feb/2061, Hari Raya Puasa
		58904, // 08/Apr/2061, Good Friday
		58927, // 01/May/2061, Labour Day
		58928, // 02/May/2061, 'Labour Day' day off
		59027, // 09/Aug/2061, National Day
		59165, // 25/Dec/2061, Christmas Day
		59166, // 26/Dec/2061, 'Christmas Day' day off
		59172, // 01/Jan/2062, New Year's Day
		59173, // 02/Jan/2062, 'New Year's Day' observed
		59211, // 09/Feb/2062, Lunar New Year's Day
		59213, // 11/Feb/2062, Hari Raya Puasa
		59254, // 24/Mar/2062, Good Friday
		59292, // 01/May/2062, Labour Day
		59392, // 09/Aug/2062, National Day
		59530, // 25/Dec/2062, Christmas Day
		59537, // 01/Jan/2063, New Year's Day
		59565, // 29/Jan/2063, Lunar New Year's Day
		59567, // 31/Jan/2063, Hari Raya Puasa
		59639, // 13/Apr/2063, Good Friday
		59657, // 01/May/2063, Labour Day
		59757, // 09/Aug/2063, National Day
		59895, // 25/Dec/2063, Christmas Day
		59902, // 01/Jan/2064, New Year's Day
		59921, // 20/Jan/2064, Hari Raya Puasa
		59950, // 18/Feb/2064, Lunar New Year's Day
		59996, // 04/Apr/2064, Good Friday
		60023, // 01/May/2064, Labour Day
		60123, // 09/Aug/2064, National Day
		60261, // 25/Dec/2064, Christmas Day
		60268, // 01/Jan/2065, New Year's Day
		60276, // 09/Jan/2065, Hari Raya Puasa
		60303, // 05/Feb/2065, Lunar New Year's Day
		60353, // 27/Mar/2065, Good Friday
		60388, // 01/May/2065, Labour Day
		60488, // 09/Aug/2065, National Day
		60489, // 10/Aug/2065, 'National Day' observed
		60626, // 25/Dec/2065, Christmas Day
		60630, // 29/Dec/2065, Hari Raya Puasa
		60633, // 01/Jan/2066, New Year's Day
		60658, // 26/Jan/2066, Lunar New Year's Day
		60731, // 09/Apr/2066, Good Friday
		60753, // 01/May/2066, Labour Day
		60853, // 09/Aug/2066, National Day
		60985, // 19/Dec/2066, Hari Raya Puasa
		60991, // 25/Dec/2066, Christmas Day
		60998, // 01/Jan/2067, New Year's Day
		61042, // 14/Feb/2067, Lunar New Year's Day
		61088, // 01/Apr/2067, Good Friday
		61118, // 01/May/2067, Labour Day
		61119, // 02/May/2067, 'Labour Day' day off
		61218, // 09/Aug/2067, National Day
		61339, // 08/Dec/2067, Hari Raya Puasa
		61356, // 25/Dec/2067, Christmas Day
		61357, // 26/Dec/2067, 'Christmas Day' day off
		61363, // 01/Jan/2068, New Year's Day
		61364, // 02/Jan/2068, 'New Year's Day' observed
		61396, // 03/Feb/2068, Lunar New Year's Day
		61473, // 20/Apr/2068, Good Friday
		61484, // 01/May/2068, Labour Day
		61584, // 09/Aug/2068, National Day
		61693, // 26/Nov/2068, Hari Raya Puasa
		61722, // 25/Dec/2068, Christmas Day
		61729, // 01/Jan/2069, New Year's Day
		61751, // 23/Jan/2069, Lunar New Year's Day
		61830, // 12/Apr/2069, Good Friday
		61849, // 01/May/2069, Labour Day
		61949, // 09/Aug/2069, National Day
		62048, // 16/Nov/2069, Hari Raya Puasa
		62087, // 25/Dec/2069, Christmas Day
		62094, // 01/Jan/2070, New Year's Day
		62135, // 11/Feb/2070, Lunar New Year's Day
		62180, // 28/Mar/2070, Good Friday
		62214, // 01/May/2070, Labour Day
		62314, // 09/Aug/2070, National Day
		62402, // 05/Nov/2070, Hari Raya Puasa
		62452 // 25/Dec/2070, Christmas Day
	};
}
