"""Pruebas unitarias para la lógica de conteo y validación de caché."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.mp.parser import review_count
from src.mp.scrape_prof import _remote_review_stats, _cache_is_valid


def _html_with_review_count(count: int) -> str:
    return f"""
    <html>
        <body>
            <div class="table-toggle rating-count active">{count} Reseñas</div>
            <div class="rating-filter togglable">
                <table class="tftable">
                    <tr><th>Encabezado</th></tr>
                </table>
            </div>
        </body>
    </html>
    """


def test_review_count_returns_exact_integer():
    html = _html_with_review_count(21)
    assert review_count(html) == 21


def test_cache_invalidates_when_remote_count_increases():
    initial_html = _html_with_review_count(20)
    updated_html = _html_with_review_count(21)

    initial_stats = _remote_review_stats(initial_html)
    updated_stats = _remote_review_stats(updated_html)

    # Verificación de que el conteo remoto es preciso
    assert initial_stats["precise"] is True
    assert updated_stats["precise"] is True

    # Caché vigente cuando los conteos coinciden
    assert _cache_is_valid(20, initial_stats) is True

    # Si aumenta el número real de reseñas, se debe re-scrapear
    assert _cache_is_valid(20, updated_stats) is False
