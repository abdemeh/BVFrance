# BVFrance Election Results API

This project provides a FastAPI web API to query French municipal election results using DuckDB and parquet files.

## Features
- Query results by commune, department, or for all France
- Get candidate results, participation, and abstention rates
- Fast, serverless analytics using DuckDB

## Requirements
- Python 3.8+
- Parquet files in the `parquet/` directory
- Install dependencies:
  ```sh
  pip install fastapi uvicorn duckdb
  ```

## Usage
1. Activate your virtual environment (if needed):
   ```sh
   source venv/bin/activate
   ```
2. Start the API server:
   ```sh
   uvicorn api:app --reload
   ```
3. Open your browser at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for interactive API documentation.

## Endpoints
- `/get/resultats/{id_commune}` — Results by commune
- `/get/resultats/dep/{code_departement}` — Results by department
- `/get/resultats/france` — Results for all France
- `/get/participation/dep/{code_departement}` — Participation/abstention by department
- `/get/participation/france` — Participation/abstention for all France

See `API_USAGE.md` for detailed usage and examples.

## Example
```sh
curl http://127.0.0.1:8000/get/resultats/01001
```

## License
MIT
