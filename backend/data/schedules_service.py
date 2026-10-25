# backend/data/schedules_service.py

ROUTES = {
    "S1": [
        "RIVAROLO", "FELETTO", "BOSCONERO", "S_BENIGNO", "VOLPIANO", "SETTIMO",
        "STURA", "REBAUDENGO", "DORA", "PORTA_SUSA", "ZAPPATA", "LINGOTTO",
        "MONCALIERI", "TROFARELLO", "CHIERI"
    ],
    "S2": [
        "STURA", "REBAUDENGO", "DORA", "PORTA_SUSA", "ZAPPATA", "LINGOTTO",
        "SANGONE", "NICHELINO", "CANDIOLO", "NONE", "AIRASCA", "PISCINA",
        "PIN_OLIMPICA", "PINEROLO"
    ],
    "S3a": [
        "BARDONECCHIA", "BEAULARD", "OULX", "SALBERTRAND", "CHIOMONTE", "MEANA",
        "BUSSOLENO", "S_ANTONINO", "AVIGLIANA", "ROSTA", "ALPIGNANO", "COLLEGNO",
        "GRUGLIASCO", "SAN_PAOLO", "PORTA_SUSA", "DORA", "REBAUDENGO", "STURA"
    ],
    "S3b": [
        "STURA", "REBAUDENGO", "DORA", "PORTA_SUSA", "SAN_PAOLO",
        "GRUGLIASCO", "COLLEGNO", "ALPIGNANO", "ROSTA", "AVIGLIANA", "S_AMBROGIO",
        "CONDOVE", "S_ANTONINO", "BORGONE", "BRUZOLO", "BUSSOLENO", "SUSA"
    ],
    "S4": [
        "ALBA", "MUSSOTTO", "MONTICELLO", "S_VITTORIA", "BRA", "BANDITO", "SANFRE",
        "SOMMARIVA", "CARMAGNOLA", "VILLASTELLONE", "TROFARELLO", "MONCALIERI",
        "LINGOTTO", "ZAPPATA", "PORTA_SUSA", "DORA", "REBAUDENGO", "STURA"
    ],
    "S4b": [
        "ALBA", "MUSSOTTO", "S_VITTORIA", "POCAPAGLIA", "BRA", "BANDITO", "SANFRE",
        "SOMMARIVA", "CARMAGNOLA", "VILLASTELLONE", "TROFARELLO", "MONCALIERI",
        "LINGOTTO", "ZAPPATA", "PORTA_SUSA", "DORA", "REBAUDENGO", "STURA"
    ],
    "S5": [
        "ORBASSANO", "QUAGLIA", "SAN_PAOLO", "PORTA_SUSA", "DORA", "REBAUDENGO",
        "STURA", "SETTIMO", "BRANDIZZO", "CHIVASSO"
    ],
    "S5e": [
        "ORBASSANO", "QUAGLIA", "SAN_PAOLO", "PORTA_SUSA", "DORA", "REBAUDENGO",
        "STURA", "SETTIMO", "BRANDIZZO", "CHIVASSO", "MONTANARO", "RODALLO",
        "CALUSO", "CANDIA", "MERCENASCO", "STRAMBINO", "IVREA"
    ],
    "S6": [
        "ASTI", "S_DAMIANO", "BALDICHIERI", "VILLAFRANCA", "S_PAOLO_SOLBRITO",
        "VILLANOVA_ASTI", "PESSIONE", "CAMBIANO", "TROFARELLO", "MONCALIERI",
        "LINGOTTO", "ZAPPATA", "PORTA_SUSA", "DORA", "REBAUDENGO", "GROSSETO",
        "VENARIA_RIGOLA", "VENARIA_REGGIA", "BORGARO", "CASELLE", "AEROPORTO"
    ],
    "S7": [
        "CUNEO", "CENTALLO", "FOSSANO", "SAVIGLIANO", "CAVALLERMAGGIORE",
        "RACCONIGI", "CARMAGNOLA", "VILLASTELLONE", "TROFARELLO", "MONCALIERI",
        "LINGOTTO", "PORTA_NUOVA"
    ],
    "S8": [
        "PORTA_NUOVA", "ZAPPATA", "PORTA_SUSA", "DORA", "REBAUDENGO", "GROSSETO",
        "VENARIA_RIGOLA", "VENARIA_REGGIA", "BORGARO", "CASELLE", "AEROPORTO",
        "S_MAURIZIO", "CIRIE", "NOLE", "VILLANOVA_GROSSO", "MATHI", "BALANGERO",
        "LANZO", "GERMAGNANO"
    ],
    "S8e": [
        "PORTA_NUOVA", "ZAPPATA", "PORTA_SUSA", "DORA", "REBAUDENGO", "GROSSETO",
        "VENARIA_RIGOLA", "VENARIA_REGGIA", "BORGARO", "CASELLE", "AEROPORTO",
        "S_MAURIZIO", "CIRIE", "NOLE", "VILLANOVA_GROSSO", "MATHI", "BALANGERO",
        "LANZO", "GERMAGNANO", "FUNGHERA", "TRAVES", "LOSA", "PESSINETTO", "MEZZENILE", "CERES"
    ]
}

PLATFORM_PLANS = {
    "S1": {
        "RIVAROLO": 1, "FELETTO": 1, "BOSCONERO": 1, "S_BENIGNO": 1, "VOLPIANO": 1, "SETTIMO": 4,
        "STURA": 7, "REBAUDENGO": 5, "DORA": 1, "PORTA_SUSA": 5, "ZAPPATA": 1, "LINGOTTO": 4,
        "MONCALIERI": 1, "TROFARELLO": 1, "CHIERI": 1
    },
    "S2": {
        "STURA": 9, "REBAUDENGO": 4, "DORA": 1, "PORTA_SUSA": 5, "ZAPPATA": 1,
        "LINGOTTO": 4, "SANGONE": 1, "NICHELINO": 1, "CANDIOLO": 2,
        "NONE": 1, "AIRASCA": 2, "PISCINA": 1, "PIN_OLIMPICA": 1, "PINEROLO": 1
    },
    "S3a": {
        "BARDONECCHIA": 1, "BEAULARD": 1, "OULX": 2, "SALBERTRAND": 1, "CHIOMONTE": 2, "MEANA": 1,
        "BUSSOLENO": 2, "S_ANTONINO": 2, "AVIGLIANA": 2, "ROSTA": 2, "ALPIGNANO": 1, "COLLEGNO": 1,
        "GRUGLIASCO": 1, "SAN_PAOLO": 3, "PORTA_SUSA": 6, "DORA": 2, "REBAUDENGO": 4, "STURA": 6
    },
    "S3b": {
        "STURA": 6, "REBAUDENGO": 5, "DORA": 1, "PORTA_SUSA": 5, "SAN_PAOLO": 4,
        "GRUGLIASCO": 2, "COLLEGNO": 2, "ALPIGNANO": 2, "ROSTA": 1, "AVIGLIANA": 1, "S_AMBROGIO": 1,
        "CONDOVE": 2, "S_ANTONINO": 1, "BORGONE": 2, "BRUZOLO": 2, "BUSSOLENO": 3, "SUSA": 1
    },
    "S4": {
        "ALBA": 2, "MUSSOTTO": 1, "MONTICELLO": 1, "S_VITTORIA": 1, "POCAPAGLIA": 1,
        "BRA": 2, "BANDITO": 1, "SANFRE": 1, "SOMMARIVA": 2, "CARMAGNOLA": 3,
        "VILLASTELLONE": 1, "TROFARELLO": 6, "MONCALIERI": 5, "LINGOTTO": 3,
        "ZAPPATA": 2, "PORTA_SUSA": 6, "DORA": 2, "REBAUDENGO": 4, "STURA": 9
    },
    "S4b": {
        "ALBA": 2, "MUSSOTTO": 1, "MONTICELLO": 1, "S_VITTORIA": 1, "POCAPAGLIA": 1,
        "BRA": 2, "BANDITO": 1, "SANFRE": 1, "SOMMARIVA": 2, "CARMAGNOLA": 3,
        "VILLASTELLONE": 1, "TROFARELLO": 6, "MONCALIERI": 5, "LINGOTTO": 3,
        "ZAPPATA": 2, "PORTA_SUSA": 6, "DORA": 2, "REBAUDENGO": 4, "STURA": 9
    },
    "S5": {
        "ORBASSANO": 1, "QUAGLIA": 2, "SAN_PAOLO": 1, "PORTA_SUSA": 6, "DORA": 2,
        "REBAUDENGO": 4, "STURA": 8, "SETTIMO": 2, "BRANDIZZO": 2, "CHIVASSO": 1
    },
    "S5e": {
        "ORBASSANO": 1, "QUAGLIA": 2, "SAN_PAOLO": 1, "PORTA_SUSA": 6, "DORA": 2, "REBAUDENGO": 4,
        "STURA": 8, "SETTIMO": 2, "BRANDIZZO": 2, "CHIVASSO": 5, "MONTANARO": 1, "RODALLO": 1,
        "CALUSO": 1, "CANDIA": 1, "MERCENASCO": 1, "STRAMBINO": 1, "IVREA": 3
    },
    "S6": {
        "ASTI": 1, "S_DAMIANO": 1, "BALDICHIERI": 2, "VILLAFRANCA": 2, "S_PAOLO_SOLBRITO": 1,
        "VILLANOVA_ASTI": 1, "PESSIONE": 2, "CAMBIANO": 1, "TROFARELLO": 4, "MONCALIERI": 5,
        "LINGOTTO": 3, "ZAPPATA": 2, "PORTA_SUSA": 6, "DORA": 2, "REBAUDENGO": 2, "GROSSETO": 2,
        "VENARIA_RIGOLA": 2, "VENARIA_REGGIA": 2, "BORGARO": 2, "CASELLE": 2, "AEROPORTO": 3
    },
    "S7": {
        "CUNEO": 1, "CENTALLO": 1, "FOSSANO": 2, "SAVIGLIANO": 2, "CAVALLERMAGGIORE": 2,
        "RACCONIGI": 1, "CARMAGNOLA": 1, "VILLASTELLONE": 1, "TROFARELLO": 6,
        "MONCALIERI": 5, "LINGOTTO": 3, "PORTA_NUOVA": 1
    },
    "S8": {
        "PORTA_NUOVA": 20, "ZAPPATA": 2, "PORTA_SUSA": 6, "DORA": 2,
        "REBAUDENGO": 2, "GROSSETO": 2, "VENARIA_RIGOLA": 2, "VENARIA_REGGIA": 2,
        "BORGARO": 2, "CASELLE": 2, "AEROPORTO": 2, "S_MAURIZIO": 2, "CIRIE": 3, "NOLE": 1,
        "VILLANOVA_GROSSO": 1, "MATHI": 1, "BALANGERO": 1, "LANZO": 1, "GERMAGNANO": 1
    },
    "S8e": {
        "PORTA_NUOVA": 20, "ZAPPATA": 2, "PORTA_SUSA": 6, "DORA": 2,
        "REBAUDENGO": 2, "GROSSETO": 2, "VENARIA_RIGOLA": 2, "VENARIA_REGGIA": 2,
        "BORGARO": 2, "CASELLE": 2, "AEROPORTO": 2, "S_MAURIZIO": 2, "CIRIE": 1, "NOLE": 1,
        "VILLANOVA_GROSSO": 1, "MATHI": 1, "BALANGERO": 1, "LANZO": 1, "GERMAGNANO": 2,
        "FUNGHERA": 1, "TRAVES": 1, "LOSA": 1, "PESSINETTO": 1, "MEZZENILE": 1, "CERES": 1
    },
}

TAKT_TEMPLATES = {
    "S1": {
        "service_id": "S1",
        "route_key": "S1",
        "base_num": 1000,
        "fleet_size": 4,
        "start_time_south": "05:25:00",
        "start_time_north": "05:19:00",
        "end_time": "22:50:00",
        "frequency_min": 60,
        "SOUTH": {  # Rivarolo -> Chieri
            "RIVAROLO": "p:25", "FELETTO": "29-30", "BOSCONERO": "36-37", "S_BENIGNO": "43-44",
            "VOLPIANO": "47-48", "SETTIMO": "58-59", "STURA": "02-03", "REBAUDENGO": "06-07",
            "DORA": "09-10", "PORTA_SUSA": "12-13", "ZAPPATA": "15-16", "LINGOTTO": "20-21",
            "MONCALIERI": "25-26", "TROFARELLO": "30-31", "CHIERI": "a:41"
        },
        "NORTH": {  # Chieri -> Rivarolo
            "CHIERI": "p:19", "TROFARELLO": "29-30", "MONCALIERI": "34-35", "LINGOTTO": "39-40",
            "ZAPPATA": "44-45", "PORTA_SUSA": "47-48", "DORA": "50-51", "REBAUDENGO": "53-54",
            "STURA": "57-58", "SETTIMO": "04-05", "VOLPIANO": "15-16", "S_BENIGNO": "19-20",
            "BOSCONERO": "27-36", "FELETTO": "42-43", "RIVAROLO": "a:47"
        }
    },
    "S2": {
        "service_id": "S2",
        "route_key": "S2",
        "base_num": 2000,
        "fleet_size": 2,
        "start_time_south": "05:33:00",
        "start_time_north": "05:24:00",
        "end_time": "22:50:00",
        "frequency_min": 60,
        "SOUTH": {  # Stura -> Pinerolo
            "STURA": "p:33", "REBAUDENGO": "36-37", "DORA": "39-40", "PORTA_SUSA": "42-43",
            "ZAPPATA": "45-46", "LINGOTTO": "50-51", "SANGONE": "55-56", "NICHELINO": "59-00",
            "CANDIOLO": "04-05", "NONE": "09-10", "AIRASCA": "13-14", "PISCINA": "18-19",
            "PIN_OLIMPICA": "28-29", "PINEROLO": "a:36"
        },
        "NORTH": {  # Pinerolo -> Stura
            "PINEROLO": "p:24", "PIN_OLIMPICA": "31-32", "PISCINA": "41-42", "AIRASCA": "46-47",
            "NONE": "50-51", "CANDIOLO": "55-56", "NICHELINO": "00-01", "SANGONE": "04-05",
            "LINGOTTO": "09-10", "ZAPPATA": "14-15", "PORTA_SUSA": "17-18", "DORA": "20-21",
            "REBAUDENGO": "23-24", "STURA": "a:27"
        }
    },
    "S3a": {
        "service_id": "S3a",
        "route_key": "S3a",
        "base_num": 3000,
        "fleet_size": 3,
        "start_time_south": "06:27:00",
        "start_time_north": "05:09:00",
        "end_time": "22:50:00",
        "frequency_min": 120,
        "SOUTH": {  # Stura -> Bardonecchia
            "STURA": "p:27", "REBAUDENGO": "30-31", "DORA": "33-34", "PORTA_SUSA": "36-37",
            "SAN_PAOLO": "41-42", "GRUGLIASCO": "46-47", "COLLEGNO": "50-51", "ALPIGNANO": "55-56",
            "ROSTA": "00-01", "AVIGLIANA": "05-06", "S_ANTONINO": "13-14", "BUSSOLENO": "23-24",
            "MEANA": "30-31", "CHIOMONTE": "37-38", "SALBERTRAND": "46-47", "OULX": "52-53",
            "BEAULARD": "58-59", "BARDONECCHIA": "a:05"
        },
        "NORTH": {  # Bardonecchia -> Stura
            "BARDONECCHIA": "p:09", "BEAULARD": "17-18", "OULX": "23-24", "SALBERTRAND": "29-30",
            "CHIOMONTE": "38-39", "MEANA": "45-46", "BUSSOLENO": "53-54", "S_ANTONINO": "03-04",
            "AVIGLIANA": "11-12", "ROSTA": "16-17", "ALPIGNANO": "21-22", "COLLEGNO": "26-27",
            "GRUGLIASCO": "30-31", "SAN_PAOLO": "35-36", "PORTA_SUSA": "40-41", "DORA": "43-44",
            "REBAUDENGO": "46-47", "STURA": "a:50"
        }
    },
    "S3b": {
        "service_id": "S3b",
        "route_key": "S3b",
        "base_num": 3500,
        "fleet_size": 3,
        "start_time_south": "05:27:00",
        "start_time_north": "04:32:00",
        "end_time": "22:50:00",
        "frequency_min": 120,
        "SOUTH": {  # Stura -> Susa
            "STURA": "p:27", "REBAUDENGO": "30-31", "DORA": "33-34", "PORTA_SUSA": "36-37",
            "SAN_PAOLO": "41-42", "GRUGLIASCO": "46-47", "COLLEGNO": "50-51", "ALPIGNANO": "55-56",
            "ROSTA": "00-01", "AVIGLIANA": "05-06", "S_AMBROGIO": "10-11", "CONDOVE": "15-16",
            "S_ANTONINO": "19-20", "BORGONE": "24-25", "BRUZOLO": "28-29", "BUSSOLENO": "33-34",
            "SUSA": "a:44"
        },
        "NORTH": {  # Susa -> Stura
            "SUSA": "p:32", "BUSSOLENO": "42-43", "BRUZOLO": "48-49", "BORGONE": "52-53",
            "S_ANTONINO": "57-58", "CONDOVE": "01-02", "S_AMBROGIO": "06-07", "AVIGLIANA": "11-12",
            "ROSTA": "16-17", "ALPIGNANO": "21-22", "COLLEGNO": "26-27", "GRUGLIASCO": "30-31",
            "SAN_PAOLO": "35-36", "PORTA_SUSA": "40-41", "DORA": "43-44", "REBAUDENGO": "46-47",
            "STURA": "a:50"
        }
    },
    "S4": {
        "service_id": "S4",
        "route_key": "S4",
        "base_num": 4000,
        "fleet_size": 2,
        "start_time_south": "04:51:00",       # Stura -> Alba (ore pari)
        "start_time_north": "05:15:00", # Alba -> Stura (ore dispari)
        "end_time": "22:55:00",
        "frequency_min": 120,
        "SOUTH": {  # Stura -> Alba (via Monticello)
            "STURA": "p:51", "REBAUDENGO": "54-55", "DORA": "57-58", "PORTA_SUSA": "00-01",
            "ZAPPATA": "03-04", "LINGOTTO": "08-09", "MONCALIERI": "13-14", "TROFARELLO": "18-19",
            "VILLASTELLONE": "24-25", "CARMAGNOLA": "31-32", "SOMMARIVA": "39-51",
            "SANFRE": "54-55", "BANDITO": "58-59", "BRA": "11-13", "S_VITTORIA": "19-20",
            "MONTICELLO": "24-25", "MUSSOTTO": "29-30", "ALBA": "a:34"
        },
        "NORTH": {  # Alba -> Stura (via Monticello)
            "ALBA": "p:15", "MUSSOTTO": "19-20", "MONTICELLO": "24-25", "S_VITTORIA": "29-30",
            "BRA": "36-38", "BANDITO": "42-43", "SANFRE": "46-47", "SOMMARIVA": "49-50",
            "CARMAGNOLA": "56-57", "VILLASTELLONE": "03-04", "TROFARELLO": "09-10",
            "MONCALIERI": "13-14", "LINGOTTO": "18-19", "ZAPPATA": "23-24", "PORTA_SUSA": "26-27",
            "DORA": "29-30", "REBAUDENGO": "32-33", "STURA": "a:36"
        }
    },
    "S4b": {
        "service_id": "S4",
        "route_key": "S4b",
        "base_num": 4500,
        "fleet_size": 2,
        "start_time_south": "05:51:00",       # Stura -> Alba (ore dispari)
        "start_time_north": "06:15:00", # Alba -> Stura (ore pari)
        "end_time": "22:55:00",
        "frequency_min": 120,
        "SOUTH": {  # Stura -> Alba (via Pocapaglia)
            "STURA": "p:51", "REBAUDENGO": "54-55", "DORA": "57-58", "PORTA_SUSA": "00-01",
            "ZAPPATA": "03-04", "LINGOTTO": "08-09", "MONCALIERI": "13-14", "TROFARELLO": "18-19",
            "VILLASTELLONE": "24-25", "CARMAGNOLA": "31-32", "SOMMARIVA": "39-51",
            "SANFRE": "54-55", "BANDITO": "58-59", "BRA": "11-13", "POCAPAGLIA": "17-18",
            "S_VITTORIA": "21-22", "MUSSOTTO": "29-30", "ALBA": "a:34"
        },
        "NORTH": {  # Alba -> Stura (via Pocapaglia)
            "ALBA": "p:15", "MUSSOTTO": "19-20", "S_VITTORIA": "26-27", "POCAPAGLIA": "30-31",
            "BRA": "36-38", "BANDITO": "42-43", "SANFRE": "46-47", "SOMMARIVA": "49-50",
            "CARMAGNOLA": "56-57", "VILLASTELLONE": "03-04", "TROFARELLO": "09-10",
            "MONCALIERI": "13-14", "LINGOTTO": "18-19", "ZAPPATA": "23-24", "PORTA_SUSA": "26-27",
            "DORA": "29-30", "REBAUDENGO": "32-33", "STURA": "a:36"
        }
    },
    "S5": {
        "service_id": "S5",
        "route_key": "S5",
        "base_num": 5000,
        "fleet_size": 2,
        "start_time_south": "06:29:00",
        "start_time_north": "05:48:00",
        "end_time": "22:32:00",
        "frequency_min": 120,
        "SOUTH": {  # Chivasso -> Orbassano
            "CHIVASSO": "p:29", "BRANDIZZO": "33-34", "SETTIMO": "39-40", "STURA": "43-44",
            "REBAUDENGO": "47-48", "DORA": "50-51", "PORTA_SUSA": "53-54", "SAN_PAOLO": "58-59",
            "QUAGLIA": "03-04", "ORBASSANO": "a:10"
        },
        "NORTH": {  # Orbassano -> Chivasso
            "ORBASSANO": "p:48", "QUAGLIA": "54-55", "SAN_PAOLO": "59-00", "PORTA_SUSA": "04-05",
            "DORA": "07-08", "REBAUDENGO": "10-11", "STURA": "14-15", "SETTIMO": "21-22",
            "BRANDIZZO": "27-28", "CHIVASSO": "a:32"
        }
    },
    "S5e": {
        "service_id": "S5e",
        "route_key": "S5e",
        "base_num": 5500,
        "fleet_size": 2,
        "start_time_south": "04:45:00",
        "start_time_north": "06:48:00",
        "end_time": "23:16:00",
        "frequency_min": 120,
        "SOUTH": {  # Ivrea -> Orbassano
            "IVREA": "p:45", "STRAMBINO": "52-53", "MERCENASCO": "56-57", "CANDIA": "00-01",
            "CALUSO": "06-07", "RODALLO": "11-12", "MONTANARO": "19-20", "CHIVASSO": "25-29",
            "BRANDIZZO": "33-34", "SETTIMO": "39-40", "STURA": "43-44", "REBAUDENGO": "47-48",
            "DORA": "50-51", "PORTA_SUSA": "53-54", "SAN_PAOLO": "58-59", "QUAGLIA": "03-04",
            "ORBASSANO": "a:10"
        },
        "NORTH": {  # Orbassano -> Ivrea
            "ORBASSANO": "p:48", "QUAGLIA": "54-55", "SAN_PAOLO": "59-00", "PORTA_SUSA": "04-05",
            "DORA": "07-08", "REBAUDENGO": "10-11", "STURA": "14-15", "SETTIMO": "21-22",
            "BRANDIZZO": "27-28", "CHIVASSO": "32-36", "MONTANARO": "41-42", "RODALLO": "49-50",
            "CALUSO": "54-55", "CANDIA": "00-01", "MERCENASCO": "04-05", "STRAMBINO": "08-09",
            "IVREA": "a:16"
        }
    },
    "S6": {
        "service_id": "S6",
        "route_key": "S6",
        "base_num": 6000,
        "fleet_size": 4,
        "start_time_south": "05:12:00",
        "start_time_north": "05:10:00",
        "end_time": "22:50:00",
        "frequency_min": 60,
        "SOUTH": {  # Aeroporto -> Asti
            "AEROPORTO": "p:12", "CASELLE": "16-17", "BORGARO": "21-22",
            "VENARIA_REGGIA": "26-27", "VENARIA_RIGOLA": "31-32", "GROSSETO": "36-37",
            "REBAUDENGO": "40-41", "DORA": "43-44", "PORTA_SUSA": "46-47",
            "ZAPPATA": "49-50", "LINGOTTO": "54-55", "MONCALIERI": "59-00",
            "TROFARELLO": "05-07", "CAMBIANO": "10-11", "PESSIONE": "15-16",
            "VILLANOVA_ASTI": "22-23", "S_PAOLO_SOLBRITO": "26-27",
            "VILLAFRANCA": "32-33", "BALDICHIERI": "37-38", "S_DAMIANO": "41-42",
            "ASTI": "a:50"
        },
        "NORTH": {  # Asti -> Aeroporto
            "ASTI": "p:10", "S_DAMIANO": "16-17", "BALDICHIERI": "21-22",
            "VILLAFRANCA": "26-27", "S_PAOLO_SOLBRITO": "32-33",
            "VILLANOVA_ASTI": "36-37", "PESSIONE": "42-43", "CAMBIANO": "47-48",
            "TROFARELLO": "52-55", "MONCALIERI": "59-00", "LINGOTTO": "04-05",
            "ZAPPATA": "09-10", "PORTA_SUSA": "12-13", "DORA": "15-16",
            "REBAUDENGO": "18-19", "GROSSETO": "22-23", "VENARIA_RIGOLA": "27-28",
            "VENARIA_REGGIA": "32-33", "BORGARO": "37-38", "CASELLE": "42-43",
            "AEROPORTO": "a:47"
        }
    },
    "S7": {
        "service_id": "S7",
        "route_key": "S7",
        "base_num": 7000,
        "fleet_size": 4,
        "start_time_south": "05:55:00",
        "start_time_north": "05:40:00",
        "end_time": "22:55:00",
        "frequency_min": 60,
        "SOUTH": {  # Porta Nuova -> Cuneo
            "PORTA_NUOVA": "p:55", "LINGOTTO": "02-03", "MONCALIERI": "07-08",
            "TROFARELLO": "12-13", "VILLASTELLONE": "18-19", "CARMAGNOLA": "25-26",
            "RACCONIGI": "32-33", "CAVALLERMAGGIORE": "38-39", "SAVIGLIANO": "44-45",
            "FOSSANO": "56-57", "CENTALLO": "06-07", "CUNEO": "a:21"
        },
        "NORTH": {  # Cuneo -> Porta Nuova
            "CUNEO": "p:40", "CENTALLO": "54-55", "FOSSANO": "04-05",
            "SAVIGLIANO": "16-17", "CAVALLERMAGGIORE": "22-23", "RACCONIGI": "28-29",
            "CARMAGNOLA": "35-36", "VILLASTELLONE": "42-43", "TROFARELLO": "48-49",
            "MONCALIERI": "53-54", "LINGOTTO": "58-59", "PORTA_NUOVA": "a:05"
        }
    },
    "S8": {
        "service_id": "S8",
        "route_key": "S8",
        "base_num": 8000,
        "fleet_size": 4,
        "start_time_south": "05:47:00",
        "start_time_north": "05:26:00",
        "end_time": "22:35:00",
        "frequency_min": 60,
        "SOUTH": {  # Germagnano -> Porta Nuova
            "GERMAGNANO": "p:47", "LANZO": "53-54", "BALANGERO": "01-02", "MATHI": "07-08",
            "VILLANOVA_GROSSO": "10-11", "NOLE": "13-14", "CIRIE": "18-19", "S_MAURIZIO": "25-26",
            "AEROPORTO": "31-32", "CASELLE": "36-37", "BORGARO": "41-42", "VENARIA_REGGIA": "46-47",
            "VENARIA_RIGOLA": "50-51", "GROSSETO": "55-56", "REBAUDENGO": "00-01", "DORA": "03-04",
            "PORTA_SUSA": "06-07", "ZAPPATA": "09-10", "PORTA_NUOVA": "a:15"
        },
        "NORTH": {  # Porta Nuova -> Germagnano
            "PORTA_NUOVA": "p:26", "ZAPPATA": "30-31", "PORTA_SUSA": "33-34", "DORA": "36-37",
            "REBAUDENGO": "39-40", "GROSSETO": "44-45", "VENARIA_RIGOLA": "49-50", "VENARIA_REGGIA": "53-54",
            "BORGARO": "58-59", "CASELLE": "03-04", "AEROPORTO": "08-09", "S_MAURIZIO": "14-15",
            "CIRIE": "21-22", "NOLE": "26-27", "VILLANOVA_GROSSO": "29-30", "MATHI": "32-33",
            "BALANGERO": "38-39", "LANZO": "46-53", "GERMAGNANO": "a:59"
        }
    },
    "S8b": {
        "service_id": "S8",
        "route_key": "S8",
        "base_num": 8400,
        "fleet_size": 2,
        "start_time_south": "06:07:00",
        "start_time_north": "05:45:00",
        "end_time": "22:35:00",
        "frequency_min": 120,
        "SOUTH": {  # Germagnano -> Porta Nuova
            "GERMAGNANO": "p:07", "LANZO": "13-14", "BALANGERO": "21-22", "MATHI": "27-28",
            "VILLANOVA_GROSSO": "30-31", "NOLE": "33-34", "CIRIE": "38-39", "S_MAURIZIO": "45-46",
            "AEROPORTO": "51-52", "CASELLE": "56-57", "BORGARO": "01-02", "VENARIA_REGGIA": "06-07",
            "VENARIA_RIGOLA": "10-11", "GROSSETO": "15-16", "REBAUDENGO": "20-21", "DORA": "23-24",
            "PORTA_SUSA": "26-27", "ZAPPATA": "29-30", "PORTA_NUOVA": "a:35"
        },
        "NORTH": {  # Porta Nuova -> Germagnano
            "PORTA_NUOVA": "p:45", "ZAPPATA": "49-50", "PORTA_SUSA": "52-53", "DORA": "55-56",
            "REBAUDENGO": "58-00", "GROSSETO": "04-05", "VENARIA_RIGOLA": "09-10", "VENARIA_REGGIA": "13-14",
            "BORGARO": "18-19", "CASELLE": "23-24", "AEROPORTO": "28-29", "S_MAURIZIO": "34-35",
            "CIRIE": "41-42", "NOLE": "46-47", "VILLANOVA_GROSSO": "49-50", "MATHI": "52-53",
            "BALANGERO": "58-02", "LANZO": "09-14", "GERMAGNANO": "a:20"
        }
    },
    "S8e": {
        "service_id": "S8e",
        "route_key": "S8e",
        "base_num": 8800,
        "fleet_size": 3,
        "start_time_south": "04:39:00",
        "start_time_north": "06:45:00",
        "end_time": "23:35:00",
        "frequency_min": 120,
        "SOUTH": {  # Ceres -> Porta Nuova
            "CERES": "p:39", "MEZZENILE": "45-46", "PESSINETTO": "49-50", "LOSA": "52-53",
            "TRAVES": "57-58", "FUNGHERA": "00-01", "GERMAGNANO": "06-07", "LANZO": "13-14",
            "BALANGERO": "21-22", "MATHI": "27-28", "VILLANOVA_GROSSO": "30-31", "NOLE": "33-34",
            "CIRIE": "38-39", "S_MAURIZIO": "45-46", "AEROPORTO": "51-52", "CASELLE": "56-57",
            "BORGARO": "01-02", "VENARIA_REGGIA": "06-07", "VENARIA_RIGOLA": "10-11", "GROSSETO": "15-16",
            "REBAUDENGO": "20-21", "DORA": "23-24", "PORTA_SUSA": "26-27", "ZAPPATA": "29-30",
            "PORTA_NUOVA": "a:35"
        },
        "NORTH": {  # Porta Nuova -> Ceres
            "PORTA_NUOVA": "p:45", "ZAPPATA": "49-50", "PORTA_SUSA": "52-53", "DORA": "55-56",
            "REBAUDENGO": "58-00", "GROSSETO": "04-05", "VENARIA_RIGOLA": "09-10", "VENARIA_REGGIA": "13-14",
            "BORGARO": "18-19", "CASELLE": "23-24", "AEROPORTO": "28-29", "S_MAURIZIO": "34-35",
            "CIRIE": "41-42", "NOLE": "46-47", "VILLANOVA_GROSSO": "49-50", "MATHI": "52-53",
            "BALANGERO": "58-02", "LANZO": "09-14", "GERMAGNANO": "20-21", "FUNGHERA": "26-27",
            "TRAVES": "29-30", "LOSA": "34-35", "PESSINETTO": "37-38", "MEZZENILE": "41-42",
            "CERES": "a:49"
        }
    },
}