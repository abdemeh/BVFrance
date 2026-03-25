# API Usage Instructions

## Prerequisites
- Python 3.8+
- Install dependencies:
  ```sh
  pip install fastapi uvicorn duckdb
  ```
- Place your parquet files in the `parquet/` directory.

## How to Launch the API

1. Activate your virtual environment (if needed):
   ```sh
   source venv/bin/activate
   ```
2. Start the FastAPI server:
   ```sh
   uvicorn api:app --reload
   ```
   The API will be available at http://127.0.0.1:8000

## Endpoints

### 1. Résultats par commune
- `GET /get/resultats/{id_commune}`
- Returns: commune name, all candidates, results for each candidate, illimite boolean

### 2. Résultats par département
- `GET /get/resultats/dep/{code_departement}`
- Returns: department name, results by nuance/list

### 3. Résultats France
- `GET /get/resultats/france`
- Returns: results by nuance/list for all France

### 4. Participation/Abstention par département
- `GET /get/participation/dep/{code_departement}`
- Returns: department name, % abstention, % participation

### 5. Participation/Abstention France
- `GET /get/participation/france`
- Returns: % abstention, % participation for all France

## Example Usage
- `GET http://127.0.0.1:8000/get/resultats/01001`
- `GET http://127.0.0.1:8000/get/resultats/dep/01`
- `GET http://127.0.0.1:8000/get/resultats/france`
- `GET http://127.0.0.1:8000/get/participation/dep/01`
- `GET http://127.0.0.1:8000/get/participation/france`

---

You can also access the interactive docs at http://127.0.0.1:8000/docs
