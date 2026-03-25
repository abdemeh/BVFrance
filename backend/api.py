from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import duckdb
import pandas as pd
import numpy as np
import os
import glob
import json

app = FastAPI(title="API Résultats Électoraux 🗳️", version="3.4.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

PARQUET_DIR = os.path.join(os.path.dirname(__file__), "parquet")
REGIONS_FILE = os.path.join(os.path.dirname(__file__), "regions.json")
con = duckdb.connect(database=':memory:')

regions_data = []
if os.path.exists(REGIONS_FILE):
    with open(REGIONS_FILE, 'r') as f:
        regions_data = json.load(f)

def load_data():
    tour_mapping = {
        "municipales-2026-resultats-bureau-de-vote-2026-03-23-16h15.parquet": 1,
        "municipales-2026-resultats-bv-par-communes-2026-03-20.parquet": 2
    }
    
    files = glob.glob(os.path.join(PARQUET_DIR, "*.parquet"))
    if not files: return False

    all_rows = []
    for f in files:
        fname = os.path.basename(f)
        tour_val = tour_mapping.get(fname, 1)
        try:
            df = pd.read_parquet(f)
            col_map = {c.lower().strip(): c for c in df.columns}
            def gc(candidates):
                for c in candidates:
                    if c.lower().strip() in col_map: return col_map[c.lower().strip()]
                return None

            c_com, l_com = gc(["code commune", "code de la commune"]), gc(["libellé commune", "libellé de la commune"])
            c_dep, l_dep = gc(["code département", "code du département"]), gc(["libellé département", "libellé du département"])
            n_ins, n_vot, n_exp = gc(["inscrits"]), gc(["votants"]), gc(["exprimés"])

            if not c_com or not n_ins: continue

            for _, row in df.iterrows():
                inscrits = int(pd.to_numeric(row.get(n_ins, 0), errors='coerce') or 0)
                votants = int(pd.to_numeric(row.get(n_vot, 0), errors='coerce') or 0)
                exprimes = int(pd.to_numeric(row.get(n_exp, 0), errors='coerce') or 0)
                
                cdep_val = str(row.get(c_dep, ''))
                reg_name = "Inconnu"
                for r in regions_data:
                    if cdep_val in r['depts']:
                        reg_name = r['nom']
                        break

                base_row = {
                    "code_commune": str(row.get(c_com, '')),
                    "libelle_commune": str(row.get(l_com, '')),
                    "code_dep": cdep_val,
                    "libelle_dep": str(row.get(l_dep, '')),
                    "libelle_reg": reg_name,
                    "inscrits": inscrits, "votants": votants, "exprimes": exprimes, "tour": tour_val
                }

                for i in range(1, 31):
                    v_col = gc([f"voix {i}"])
                    if not v_col or v_col not in df.columns: break
                    voix = pd.to_numeric(row.get(v_col), errors='coerce')
                    if pd.isna(voix) or voix <= 0: continue

                    n_col = gc([f"nuance liste {i}", f"nuance {i}"])
                    s_col = gc([f"sièges au cm {i}", f"sièges {i}"])
                    l_col = gc([f"libellé de liste {i}", f"libellé abrégé de liste {i}"])

                    nuance = str(row.get(n_col, "SANS ÉTIQUETTE")).strip()
                    if not nuance or nuance.lower() == 'nan': nuance = "SANS ÉTIQUETTE"

                    all_rows.append({
                        **base_row,
                        "nuance": nuance,
                        "voix": int(voix),
                        "sieges": int(pd.to_numeric(row.get(s_col, 0), errors='coerce') or 0),
                        "libelle": str(row.get(l_col, '')) if l_col and pd.notna(row.get(l_col)) else ""
                    })
        except Exception as e: print(f"Error {fname}: {e}")

    if all_rows:
        con.register("results", pd.DataFrame(all_rows))
        return True
    return False

load_data()

@app.get("/get/stats/global")
def get_global_stats(tour: int = Query(0)):
    where = f"WHERE tour = {tour}" if tour in [1, 2] else ""
    try:
        nuances = con.execute(f"SELECT nuance as Nuance, SUM(voix) as total_voix, SUM(sieges) as total_sieges, COUNT(DISTINCT code_commune) as nb_communes FROM results {where} GROUP BY nuance ORDER BY total_sieges DESC").df().fillna(0).to_dict(orient='records')
        m = con.execute(f"SELECT SUM(inscrits) as ti, SUM(votants) as tv, ROUND(AVG(100.0 * votants / NULLIF(inscrits, 0)), 2) as ap FROM (SELECT code_commune, tour, MAX(inscrits) as inscrits, MAX(votants) as votants FROM results {where} GROUP BY code_commune, tour)").df().fillna(0).iloc[0]
        return {"metrics": {"total_inscrits": int(m['ti']), "total_votants": int(m['tv']), "avg_part": float(m['ap'])}, "nuances": nuances}
    except Exception: return {"metrics": {"total_inscrits": 0, "total_votants": 0, "avg_part": 0.0}, "nuances": []}

@app.get("/get/stats/geo/{level}/{code}")
def get_geo_stats(level: str, code: str, tour: int = Query(0)):
    col = "code_dep" if level == "departement" else "libelle_reg"
    where = f"WHERE {col} = '{code}'"
    if tour in [1, 2]: where += f" AND tour = {tour}"
    try:
        nuances = con.execute(f"SELECT nuance as Nuance, SUM(voix) as total_voix, SUM(sieges) as total_sieges, COUNT(DISTINCT code_commune) as nb_communes FROM results {where} GROUP BY nuance ORDER BY total_sieges DESC").df().fillna(0).to_dict(orient='records')
        m = con.execute(f"SELECT SUM(inscrits) as ti, ROUND(AVG(100.0 * votants / NULLIF(inscrits, 0)), 2) as ap FROM (SELECT code_commune, tour, MAX(inscrits) as inscrits, MAX(votants) as votants FROM results {where} GROUP BY code_commune, tour)").df().fillna(0).iloc[0]
        return {"label": code, "inscrits": int(m['ti']), "participation": float(m['ap']), "nuances": nuances}
    except Exception: return {"label": code, "inscrits": 0, "participation": 0.0, "nuances": []}

@app.get("/get/resultats/commune/{code}")
def get_commune(code: str, tour: int = Query(1)):
    try:
        meta = con.execute(f"SELECT libelle_commune, code_dep, SUM(DISTINCT inscrits) as inscrits, SUM(DISTINCT votants) as votants, SUM(DISTINCT exprimes) as exprimes FROM results WHERE code_commune = '{code}' AND tour = {tour} GROUP BY libelle_commune, code_dep").df()
        if meta.empty: return {"error": "Not found"}
        r = meta.iloc[0]
        lists = con.execute(f"SELECT nuance as Nuance, libelle as Libelle, SUM(voix) as Voix, SUM(sieges) as Sieges, ROUND(100.0 * SUM(voix) / NULLIF({int(r['exprimes'])}, 0), 2) as pct_exprimes FROM results WHERE code_commune = '{code}' AND tour = {tour} GROUP BY nuance, libelle ORDER BY Voix DESC").df().fillna(0).to_dict(orient='records')
        return {"nom": r['libelle_commune'], "code": code, "dep": r['code_dep'], "inscrits": int(r['inscrits']), "votants": int(r['votants']), "participation": round(100 * r['votants'] / r['inscrits'], 2) if r['inscrits'] > 0 else 0, "lists": lists}
    except Exception as e: return {"error": str(e)}

@app.get("/search/{level}")
def search_geo(level: str, q: str):
    if level == "commune":
        return con.execute(f"SELECT DISTINCT code_commune as id, libelle_commune as nom, code_dep as dep FROM results WHERE lower(libelle_commune) LIKE '%{q.lower()}%' OR code_commune LIKE '{q}%' LIMIT 15").df().to_dict(orient='records')
    elif level == "departement":
        return con.execute(f"SELECT DISTINCT code_dep as id, libelle_dep as nom FROM results WHERE lower(libelle_dep) LIKE '%{q.lower()}%' OR code_dep LIKE '{q}%' LIMIT 15").df().to_dict(orient='records')
    elif level == "region":
        return con.execute(f"SELECT DISTINCT libelle_reg as id, libelle_reg as nom FROM results WHERE lower(libelle_reg) LIKE '%{q.lower()}%' LIMIT 15").df().to_dict(orient='records')
    return []

@app.get("/get/stats/avancees")
def get_stats_avancees(tour: int = Query(1)):
    try:
        # Inscrits stats
        ins = con.execute(f"WITH p AS (SELECT code_commune, MAX(inscrits) as inscrits FROM results WHERE tour = {tour} GROUP BY code_commune) SELECT ROUND(AVG(inscrits), 1) as mean, ROUND(MEDIAN(inscrits), 0) as med, ROUND(QUANTILE_CONT(inscrits, 0.25), 0) as p25, ROUND(QUANTILE_CONT(inscrits, 0.75), 0) as p75, ROUND(QUANTILE_CONT(inscrits, 0.90), 0) as p90, ROUND(QUANTILE_CONT(inscrits, 0.99), 0) as p99 FROM p").df().fillna(0).iloc[0].to_dict()
        
        # Seats stats by nuance
        nuances_s = con.execute(f"SELECT nuance as Nuance, SUM(sieges) as s, COUNT(DISTINCT code_commune) as nc FROM results WHERE tour = {tour} GROUP BY nuance ORDER BY s DESC").df().fillna(0).to_dict(orient='records')
        
        # Seats distribution Majorité/Opposition
        maj = con.execute(f"WITH r AS (SELECT code_commune, nuance, SUM(sieges) as s, ROW_NUMBER() OVER(PARTITION BY code_commune ORDER BY SUM(sieges) DESC) as rn FROM results WHERE tour = {tour} AND sieges > 0 GROUP BY code_commune, nuance) SELECT CASE WHEN rn=1 THEN 'Majorité' ELSE 'Opposition' END as statut, CAST(SUM(s) AS INTEGER) as total_sieges FROM r GROUP BY statut ORDER BY total_sieges DESC").df().fillna(0).to_dict(orient='records')
        
        # Seats per commune distribution
        spc = con.execute(f"WITH p AS (SELECT code_commune, SUM(sieges) as sieges FROM results WHERE tour = {tour} GROUP BY code_commune) SELECT ROUND(AVG(sieges), 1) as mean, ROUND(MEDIAN(sieges), 0) as med, ROUND(QUANTILE_CONT(sieges, 0.25), 0) as p25, ROUND(QUANTILE_CONT(sieges, 0.75), 0) as p75, ROUND(QUANTILE_CONT(sieges, 0.90), 0) as p90, ROUND(QUANTILE_CONT(sieges, 0.99), 0) as p99 FROM p").df().fillna(0).iloc[0].to_dict()

        return {
            "tour": tour, 
            "descriptive": {"inscrits": ins, "sieges_commune": spc}, 
            "repartition": {"majorite_vs_opposition": maj, "nuances_analytics": nuances_s}
        }
    except Exception as e: return {"error": str(e)}

