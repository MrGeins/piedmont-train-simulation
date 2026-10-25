from backend.model.models import RailwayStation

stations_registry = {
    # PASSANTE
    "STURA": RailwayStation(
        "STURA", "Torino Stura", True, 1.0, True,
        num_tracks=9, available_tracks=[6, 7, 8, 9],
        stub_tracks={6: "SOUTH", 9: "SOUTH"}  # Non sono tronchi, ma per coerenza li gestiremo come tali
    ),
    "REBAUDENGO": RailwayStation("REBAUDENGO", "Torino Rebaudengo Fossata", True, 1.0, num_tracks=5, available_tracks=[1, 2, 3, 4, 5]),
    "DORA": RailwayStation("DORA", "Torino Dora", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "PORTA_SUSA": RailwayStation("PORTA_SUSA", "Torino Porta Susa", True, 1.0, num_tracks=6, available_tracks=[5, 6]),
    "ZAPPATA": RailwayStation("ZAPPATA", "Torino Zappata", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "LINGOTTO": RailwayStation("LINGOTTO", "Torino Lingotto", True, 1.0, num_tracks=9, available_tracks=[1, 2, 3, 4]),
    "PORTA_NUOVA": RailwayStation(
        "PORTA_NUOVA", "Torino Porta Nuova", True, 0.0, True,
        num_tracks=20, available_tracks=[1, 20],
        stub_tracks={i: "SOUTH" for i in range(1, 21)}
    ),

    # NORTH-WEST BRANCH
    "GROSSETO": RailwayStation("GROSSETO", "Torino Corso Grosseto", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "VENARIA_RIGOLA": RailwayStation("VENARIA_RIGOLA", "Venaria Reale-Rigola Stadio", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "VENARIA_REGGIA": RailwayStation("VENARIA_REGGIA", "Venaria Reale-Reggia", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "BORGARO": RailwayStation("BORGARO", "Borgaro", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "CASELLE": RailwayStation("CASELLE", "Caselle Torinese", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "AEROPORTO": RailwayStation(
        "AEROPORTO", "Torino Aeroporto di Caselle", True, 1.0, True,
        num_tracks=4, available_tracks=[1, 2, 3, 4],
        stub_tracks={3: "SOUTH", 4: "SOUTH"}
    ),
    "S_MAURIZIO": RailwayStation("S_MAURIZIO", "S. Maurizio Canavese", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "CIRIE": RailwayStation("CIRIE", "Ciriè", True, 2.0, num_tracks=3, available_tracks=[1, 2, 3]),
    "NOLE": RailwayStation("NOLE", "Nole", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "VILLANOVA_GROSSO": RailwayStation("VILLANOVA_GROSSO", "Villanova C.-Grosso", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "MATHI": RailwayStation("MATHI", "Mathi", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "BALANGERO": RailwayStation("BALANGERO", "Balangero", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "LANZO": RailwayStation("LANZO", "Lanzo Torinese", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "GERMAGNANO": RailwayStation(
        "GERMAGNANO", "Germagnano", True, 2.0, True,
        num_tracks=4, available_tracks=[1, 2, 3, 4],
        stub_tracks={1: "SOUTH"}  # Non è tronco, ma per coerenza lo gestiremo come tale
    ),
    "FUNGHERA": RailwayStation("FUNGHERA", "Funghera", True, 1.0, num_tracks=1, available_tracks=[1]),
    "TRAVES": RailwayStation("TRAVES", "Traves", True, 1.0, num_tracks=1, available_tracks=[1]),
    "LOSA": RailwayStation("LOSA", "Losa", True, 1.0, num_tracks=1, available_tracks=[1]),
    "PESSINETTO": RailwayStation("PESSINETTO", "Pessinetto", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "MEZZENILE": RailwayStation("MEZZENILE", "Mezzenile", False, 1.0, num_tracks=1, available_tracks=[1]),
    "CERES": RailwayStation(
        "CERES", "Ceres", True, 0.0, True,
        num_tracks=3, available_tracks=[1, 2, 3],
        stub_tracks={i: "EAST" for i in range(1, 4)}
    ),

    # WEST BRANCH
    "SAN_PAOLO": RailwayStation("SAN_PAOLO", "Torino San Paolo", True, 1.0, num_tracks=4, available_tracks=[1, 2, 3, 4]),
    "QUAGLIA": RailwayStation("QUAGLIA", "Quaglia - Le Gru", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "ORBASSANO": RailwayStation(
        "ORBASSANO", "Orbassano San Luigi", True, 0.0, True,
        num_tracks=2, available_tracks=[1, 2],
        stub_tracks={1: "NORTH", 2: "NORTH"}
    ),
    "GRUGLIASCO": RailwayStation("GRUGLIASCO", "Grugliasco", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "COLLEGNO": RailwayStation("COLLEGNO", "Collegno", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "ALPIGNANO": RailwayStation("ALPIGNANO", "Alpignano", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "ROSTA": RailwayStation("ROSTA", "Rosta", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "AVIGLIANA": RailwayStation("AVIGLIANA", "Avigliana", True, 1.0, num_tracks=3, available_tracks=[1, 2]),
    "S_AMBROGIO": RailwayStation("S_AMBROGIO", "S. Ambrogio", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "CONDOVE": RailwayStation("CONDOVE", "Condove-Chiusa S.M.", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "S_ANTONINO": RailwayStation("S_ANTONINO", "S. Antonino-Vaie", True, 1.0, num_tracks=3, available_tracks=[1, 2]),
    "BORGONE": RailwayStation("BORGONE", "Borgone", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "BRUZOLO": RailwayStation("BRUZOLO", "Bruzolo di Susa", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "BUSSOLENO": RailwayStation("BUSSOLENO", "Bussoleno", True, 2.0, num_tracks=4, available_tracks=[1, 2, 3]),
    "SUSA": RailwayStation(
        "SUSA", "Susa", True, 0.0, True,
        num_tracks=1,
        available_tracks=[1], stub_tracks={1: "EAST"}
    ),
    "MEANA": RailwayStation("MEANA", "Meana", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "CHIOMONTE": RailwayStation("CHIOMONTE", "Chiomonte", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "SALBERTRAND": RailwayStation("SALBERTRAND", "Salbertrand", True, 1.0, num_tracks=3, available_tracks=[1, 2]),
    "OULX": RailwayStation("OULX", "Oulx-Cesana-Claviere-Sestriere", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "BEAULARD": RailwayStation("BEAULARD", "Beaulard", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "BARDONECCHIA": RailwayStation(
        "BARDONECCHIA", "Bardonecchia", True, 0.0, True, num_tracks=4, available_tracks=[1, 2],
        stub_tracks={1: "EAST", 2: "EAST"}
    ),

    # NORTH BRANCH
    "SETTIMO": RailwayStation("SETTIMO", "Settimo Torinese", True, 1.0, num_tracks=4, available_tracks=[1, 2, 3, 4]),
    "VOLPIANO": RailwayStation("VOLPIANO", "Volpiano", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "S_BENIGNO": RailwayStation("S_BENIGNO", "S. Benigno Canavese", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "BOSCONERO": RailwayStation("BOSCONERO", "Bosconero", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "FELETTO": RailwayStation("FELETTO", "Feletto", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "RIVAROLO": RailwayStation(
        "RIVAROLO", "Rivarolo Canavese", True, 0.0, True,
        num_tracks=3, available_tracks=[1, 2, 3],
        stub_tracks={1: "SOUTH", 2: "SOUTH", 3: "SOUTH"}
    ),
    "BRANDIZZO": RailwayStation("BRANDIZZO", "Brandizzo", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "CHIVASSO": RailwayStation(
        "CHIVASSO", "Chivasso", True, 4.0, True,
        num_tracks=6, available_tracks=[1, 5, 6],
        stub_tracks={1: "WEST"}  # Non è tronco, ma per coerenza lo gestiamo come tale
    ),
    "MONTANARO": RailwayStation("MONTANARO", "Montanaro", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "RODALLO": RailwayStation("RODALLO", "Rodallo", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "CALUSO": RailwayStation("CALUSO", "Caluso", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "CANDIA": RailwayStation("CANDIA", "Candia Canavese", True, 4.0, num_tracks=2, available_tracks=[1, 2]),
    "MERCENASCO": RailwayStation("MERCENASCO", "Mercenasco", False, 1.0, num_tracks=1, available_tracks=[1]),
    "STRAMBINO": RailwayStation("STRAMBINO", "Strambino", True, 5.0, num_tracks=2, available_tracks=[1, 2]),
    "IVREA": RailwayStation("IVREA", "Ivrea", True, 0.0, True, num_tracks=4, available_tracks=[1, 3]),

    # SOUTH-WEST BRANCH
    "SANGONE": RailwayStation("SANGONE", "Moncalieri Sangone", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "NICHELINO": RailwayStation("NICHELINO", "Nichelino", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "CANDIOLO": RailwayStation("CANDIOLO", "Candiolo", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "NONE": RailwayStation("NONE", "None", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "AIRASCA": RailwayStation("AIRASCA", "Airasca", True, 1.0, num_tracks=3, available_tracks=[1, 2, 3]),
    "PISCINA": RailwayStation("PISCINA", "Piscina di Pinerolo", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "PIN_OLIMPICA": RailwayStation("PIN_OLIMPICA", "Pinerolo Olimpica", False, 1.0, num_tracks=1, available_tracks=[1]),
    "PINEROLO": RailwayStation(
        "PINEROLO", "Pinerolo", True, 0.0, True,
        num_tracks=3, available_tracks=[1, 2, 3],
        stub_tracks={i: "EAST" for i in range(1, 4)}
    ),

    # EAST BRANCH
    "MONCALIERI": RailwayStation("MONCALIERI", "Moncalieri", True, 1.0, num_tracks=5, available_tracks=[1, 2, 4, 5]),
    "TROFARELLO": RailwayStation("TROFARELLO", "Trofarello", True, 1.0, num_tracks=6, available_tracks=[1, 2, 3, 4, 5, 6]),
    "CHIERI": RailwayStation(
        "CHIERI", "Chieri", True, 0.0, True,
        num_tracks=2, available_tracks=[1, 2],
        stub_tracks={1: "WEST", 2: "WEST"}
    ),
    "CAMBIANO": RailwayStation("CAMBIANO", "Cambiano-Santena", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "PESSIONE": RailwayStation("PESSIONE", "Pessione", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "VILLANOVA_ASTI": RailwayStation("VILLANOVA_ASTI", "Villanova d'Asti", True, 1.0, num_tracks=3, available_tracks=[1, 2, 3]),
    "S_PAOLO_SOLBRITO": RailwayStation("S_PAOLO_SOLBRITO", "S. Paolo Solbrito", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "VILLAFRANCA": RailwayStation("VILLAFRANCA", "Villafranca-Cantarana", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "BALDICHIERI": RailwayStation("BALDICHIERI", "Baldichieri-Tigliole", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "S_DAMIANO": RailwayStation("S_DAMIANO", "S. Damiano d'Asti", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "ASTI": RailwayStation("ASTI", "Asti", True, 0.0, True, num_tracks=8, available_tracks=[1, 5]),

    # SOUTH BRANCH
    "VILLASTELLONE": RailwayStation("VILLASTELLONE", "Villastellone", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "CARMAGNOLA": RailwayStation("CARMAGNOLA", "Carmagnola", True, 1.0, num_tracks=3, available_tracks=[1, 2, 3]),
    "SOMMARIVA": RailwayStation("SOMMARIVA", "Sommariva Don Bosco", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "SANFRE": RailwayStation("SANFRE", "Sanfrè", False, 1.0, num_tracks=1, available_tracks=[1]),
    "BANDITO": RailwayStation("BANDITO", "Bandito", False, 1.0, num_tracks=1, available_tracks=[1]),
    "BRA": RailwayStation("BRA", "Bra", True, 2.0, num_tracks=6, available_tracks=[1, 2, 3]),
    "POCAPAGLIA": RailwayStation("POCAPAGLIA", "Pocapaglia", False, 1.0, num_tracks=1, available_tracks=[1]),
    "S_VITTORIA": RailwayStation("S_VITTORIA", "S. Vittoria", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "MONTICELLO": RailwayStation("MONTICELLO", "Monticello d'Alba", False, 1.0, num_tracks=1, available_tracks=[1]),
    "MUSSOTTO": RailwayStation("MUSSOTTO", "Mussotto", False, 1.0, num_tracks=1, available_tracks=[1]),
    "ALBA": RailwayStation(
        "ALBA", "Alba", True, 0.0, True,
        num_tracks=3, available_tracks=[1, 2, 3],
        stub_tracks={1: "WEST", 2: "WEST", 3: "WEST"}
    ),
    "RACCONIGI": RailwayStation("RACCONIGI", "Racconigi", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "CAVALLERMAGGIORE": RailwayStation("CAVALLERMAGGIORE", "Cavallermaggiore", True, 1.0, num_tracks=4, available_tracks=[1, 2]),
    "SAVIGLIANO": RailwayStation("SAVIGLIANO", "Savigliano", True, 1.0, num_tracks=4, available_tracks=[1, 2]),
    "FOSSANO": RailwayStation("FOSSANO", "Fossano", True, 2.0, num_tracks=7, available_tracks=[1, 2]),
    "CENTALLO": RailwayStation("CENTALLO", "Centallo", True, 1.0, num_tracks=2, available_tracks=[1, 2]),
    "CUNEO": RailwayStation(
        "CUNEO", "Cuneo", True, 0.0, True,
        num_tracks=5, available_tracks=[1, 2],
        stub_tracks={1: "EAST", 2: "EAST"}
    ),
}