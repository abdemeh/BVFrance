import duckdb

path = "parquet/*.parquet"
con = duckdb.connect()

def run(title, sql):
    print(f"\n--- {title} ---")
    df = con.execute(sql).df()
    print(df)


# Résultats par commune : % Exprimés, % Inscrits (1er et 2nd tour)
run("Résultats par commune (1er et 2nd tour)", f'''
    SELECT 
        "Libellé commune" AS Commune,
        ROUND(SUM("Exprimés") * 100.0 / NULLIF(SUM("Votants"),0), 2) AS Pourc_Exprimés,
        ROUND(SUM("Exprimés") * 100.0 / NULLIF(SUM("Inscrits"),0), 2) AS Pourc_Inscrits
    FROM read_parquet('{path}')
    GROUP BY Commune
    ORDER BY Commune
    LIMIT 20
''')

# Résultats par étiquette (Département, France)
for i in range(1, 6):
    run(f"Résultats par étiquette - Département (Liste {i})", f'''
        SELECT 
            "Libellé département" AS Niveau,
            "Nuance liste {i}" AS Etiquette,
            SUM("Voix {i}") AS Voix,
            ROUND(SUM("Voix {i}") * 100.0 / NULLIF(SUM("Exprimés"),0), 2) AS Pourc_Exprimés,
            ROUND(SUM("Voix {i}") * 100.0 / NULLIF(SUM("Inscrits"),0), 2) AS Pourc_Inscrits
        FROM read_parquet('{path}')
        GROUP BY Niveau, Etiquette
        ORDER BY Niveau, Voix DESC
        LIMIT 20
    ''')

# If region mapping is needed, add a mapping from department to region and join here.

for i in range(1, 6):
    run(f"Résultats par étiquette - France (Liste {i})", f'''
        SELECT 
            'France' AS Niveau,
            "Nuance liste {i}" AS Etiquette,
            SUM("Voix {i}") AS Voix,
            ROUND(SUM("Voix {i}") * 100.0 / NULLIF(SUM("Exprimés"),0), 2) AS Pourc_Exprimés,
            ROUND(SUM("Voix {i}") * 100.0 / NULLIF(SUM("Inscrits"),0), 2) AS Pourc_Inscrits
        FROM read_parquet('{path}')
        GROUP BY Etiquette
        ORDER BY Voix DESC
        LIMIT 20
    ''')

# Abstention et participation (Département, France)
run("Abstention et participation - Département", f'''
    SELECT 
        "Libellé département" AS Niveau,
        ROUND(100.0 - AVG("% Votants"), 2) AS Pourc_Abstention,
        ROUND(AVG("% Votants"), 2) AS Pourc_Participation
    FROM read_parquet('{path}')
    GROUP BY Niveau
    ORDER BY Niveau
    LIMIT 20
''')

# If region mapping is needed, add a mapping from department to region and join here.

run("Abstention et participation - France", f'''
    SELECT 
        'France' AS Niveau,
        ROUND(100.0 - AVG("% Votants"), 2) AS Pourc_Abstention,
        ROUND(AVG("% Votants"), 2) AS Pourc_Participation
    FROM read_parquet('{path}')
''')

# 1. Top 10 villes par inscrits
run("TOP 10 VILLES (INSCRITS)", f"""
    SELECT "Libellé commune" as Commune, SUM(Inscrits) as Total 
    FROM read_parquet('{path}')
    GROUP BY Commune ORDER BY Total DESC LIMIT 10
""")

# 2. Classement des départements par nombre de bureaux de vote
run("NB BUREAUX DE VOTE PAR DEP", f"""
    SELECT "Libellé département" as Dep, COUNT(*) as NB_BV 
    FROM read_parquet('{path}')
    GROUP BY Dep ORDER BY NB_BV DESC LIMIT 10
""")

# 3. Participation par commune
run("PARTICIPATION MOYENNE (Villes > 1000 inscrits)", f"""
    SELECT "Libellé commune" as Commune, AVG("% Votants") as Participation
    FROM read_parquet('{path}')
    GROUP BY Commune HAVING SUM(Inscrits) > 1000
    ORDER BY Participation DESC LIMIT 10
""")

# 4. Total des votes blancs
run("TOTAL VOTES BLANCS", f"""
    SELECT SUM(Blancs) as Total_France FROM read_parquet('{path}')
""")
