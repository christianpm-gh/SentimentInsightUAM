# SentimentInsightUAM

Scraper educativo con Playwright + BeautifulSoup para perfiles y reseñas en misprofesores.com. Entrada: lista de nombres. Salida: un JSON por profesor.

## Requisitos
- Python 3.11+
- Chromium de Playwright

## Instalación
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Ejecución
Extraer nombres desde Directorio UAM-Azc:
```bash
python -m src.cli nombres-uam > data/inputs/profesor_nombres.json
```

Scrapear un profesor:
```bash
python -m src.cli prof --name "Nombre Apellido"
```

## Notas
- Respeta Términos de Uso y limita la tasa de requests.
- Variables en `.env` controlan "headless" y rate limit.
