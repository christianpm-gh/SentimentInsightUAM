"""
Módulo para parsear perfiles y reseñas de profesores de MisProfesores.com

Este módulo contiene funciones para extraer información estructurada de HTML
de páginas de profesores, incluyendo calificaciones, etiquetas y reseñas.
"""
import re
import math
from typing import Optional, Dict, List, Any

from bs4 import BeautifulSoup

# Mapeo de abreviaciones de meses en español a números
MONTHS = {
    "Ene": "01", "Feb": "02", "Mar": "03", "Abr": "04", "May": "05", "Jun": "06",
    "Jul": "07", "Ago": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dic": "12"
}


def _num(txt: str) -> Optional[float]:
    """
    Extrae el primer número encontrado en un texto.

    Args:
        txt: Texto que contiene un número

    Returns:
        Número como float o None si no se encuentra
    """
    if not txt:
        return None
    m = re.search(r"\d+(?:[.,]\d+)?", txt.replace(",", "."))  # 9.4 o 97
    return float(m.group(0)) if m else None


def _date_ddMonYYYY(s: str) -> Optional[str]:
    """
    Convierte una fecha en formato DD/Mon/YYYY a formato ISO YYYY-MM-DD.

    Args:
        s: Fecha en formato DD/Mon/YYYY (ej: "15/Ene/2024")

    Returns:
        Fecha en formato ISO o None si no es válida
    """
    m = re.match(r"\s*(\d{2})/([A-Za-z]{3})/(\d{4})", s)
    if not m:
        return None
    dd, mon, yy = m.groups()
    mon = MONTHS.get(mon[:3].title(), "01")
    return f"{yy}-{mon}-{dd}"


def parse_profile(html: str) -> Dict[str, Any]:
    """
    Extrae información del perfil de un profesor desde el HTML de MisProfesores.com

    Parsea el HTML para extraer calificaciones generales, nivel de dificultad,
    porcentaje de recomendación y etiquetas asociadas al profesor.

    Args:
        html: Contenido HTML de la página del perfil del profesor

    Returns:
        Dict con las claves:
            - name: Nombre del profesor
            - overall_quality: Calificación general (float o None)
            - difficulty: Nivel de dificultad (float o None)
            - recommend_percent: Porcentaje de recomendación (float o None)
            - tags: Lista de diccionarios con 'label' y 'count'
    """
    s = BeautifulSoup(html, "lxml")
    rb = s.select_one("div.rating-breakdown")
    name = (s.select_one(".prof_headers h1") or s.select_one("h1") or s.select_one("title"))
    if not rb:
        return {
            "name": name.get_text(strip=True) if name else "Perfil",
            "overall_quality": None,
            "difficulty": None,
            "recommend_percent": None,
            "tags": []
        }

    # Extraer métricas principales del profesor
    overall = _num(rb.select_one(".quality .grade").get_text(strip=True))
    recommend = _num(rb.select_one(".takeAgain .grade").get_text(strip=True))  # 97%
    difficulty = _num(rb.select_one(".difficulty .grade").get_text(strip=True))

    # Extraer etiquetas asociadas al profesor con sus conteos
    tags = []
    for sp in s.select(".right-breakdown .tag-box .tag-box-choosetags"):
        t = sp.get_text(strip=True)
        m = re.match(r"(.+?)\s*\((\d+)\)\s*$", t)
        tags.append({
            "label": m.group(1).strip() if m else t,
            "count": int(m.group(2)) if m else None
        })

    return {
        "name": name.get_text(strip=True) if name else "Perfil",
        "overall_quality": overall,
        "difficulty": difficulty,
        "recommend_percent": recommend,
        "tags": tags
    }


def parse_reviews(html: str) -> List[Dict[str, Any]]:
    """
    Extrae todas las reseñas de un profesor desde el HTML de MisProfesores.com

    Parsea las filas de la tabla de reseñas para extraer fecha, curso, calificaciones,
    asistencia, comentarios y etiquetas de cada reseña.

    Args:
        html: Contenido HTML de la página con las reseñas del profesor

    Returns:
        Lista de diccionarios, cada uno representa una reseña con las claves:
            - date: Fecha en formato ISO (YYYY-MM-DD)
            - course: Nombre del curso (str o None)
            - overall: Calificación general (float o None)
            - ease: Facilidad del curso (float o None)
            - attendance: Tipo de asistencia (str o None)
            - grade_received: Calificación recibida (str o None)
            - interest: Nivel de interés (str o None)
            - tags: Lista de etiquetas de la reseña
            - comment: Comentario adicional (str)
    """
    s = BeautifulSoup(html, "lxml")
    rows = s.select("div.rating-filter.togglable table.tftable tr")[1:]  # Saltar header
    out = []
    for tr in rows:
        td_r = tr.select_one("td.rating")
        td_c = tr.select_one("td.class")
        td_com = tr.select_one("td.comments")
        if not td_r or not td_c:
            continue

        # Extraer fecha de la reseña
        date = _date_ddMonYYYY(td_r.select_one(".date").get_text(strip=True))

        # Extraer calificaciones (calidad general y facilidad)
        overall = ease = None
        for box in td_r.select(".breakdown .descriptor-container"):
            desc_elem = box.select_one(".descriptor")
            desc = desc_elem.get_text(strip=True).lower() if desc_elem else ""
            score_elem = box.select_one(".score")
            val = _num(score_elem.get_text(strip=True)) if score_elem else None
            if "calidad" in desc:
                overall = val
            if "facilidad" in desc:
                ease = val

        # Extraer clase y metadatos
        course_elem = td_c.select_one(".name .response")
        course = course_elem.get_text(strip=True) if course_elem else None
        attendance_elem = td_c.select_one(".attendance .response")
        attendance = attendance_elem.get_text(strip=True) if attendance_elem else None

        grade_received = interest = None
        for g in td_c.select(".grade"):
            txt = g.get_text(strip=True)
            if "Calificación Recibida" in txt:
                response_elem = g.select_one(".response")
                grade_received = response_elem.get_text(strip=True) if response_elem else None
            if "Interés" in txt:
                response_elem = g.select_one(".response")
                interest = response_elem.get_text(strip=True) if response_elem else None

        # Extraer comentario y etiquetas de la reseña
        comment_elem = td_com.select_one("p.commentsParagraph")
        comment = comment_elem.get_text(strip=True) if comment_elem else ""
        rtags = [
            t.get_text(strip=True)
            for t in td_com.select(".tagbox .tag-box-choosetags, .tagbox a, .tagbox span")
            if t.get_text(strip=True)
        ]

        out.append({
            "date": date,
            "course": course,
            "overall": overall,
            "ease": ease,
            "attendance": attendance,
            "grade_received": grade_received,
            "interest": interest,
            "tags": rtags,
            "comment": comment
        })
    return out


def review_count(html: str, soup: Optional[BeautifulSoup] = None) -> Optional[int]:
    """Obtiene el número total de reseñas disponibles para un profesor.

    Extrae el contador mostrado en el conmutador de la tabla de reseñas
    (``div.table-toggle.rating-count.active``). Si el contador no está
    presente o no se puede interpretar, retorna ``None``.

    Args:
        html: Contenido HTML de la página con reseñas.
        soup: Instancia opcional de :class:`BeautifulSoup` para reutilizar
            un árbol ya parseado.

    Returns:
        Número total de reseñas o ``None`` si no se encuentra el contador.
    """

    s = soup if soup is not None else BeautifulSoup(html, "lxml")
    cnt = s.select_one("div.table-toggle.rating-count.active")
    if not cnt:
        return None

    n = _num(cnt.get_text())
    return int(n) if n is not None else None


def page_count(html: str, soup: Optional[BeautifulSoup] = None) -> int:
    """
    Calcula el número total de páginas de reseñas disponibles.

    Extrae el conteo total de reseñas y calcula cuántas páginas hay
    (5 reseñas por página), o busca el número máximo en la paginación.

    Args:
        html: Contenido HTML de la página con reseñas
        soup: Instancia opcional de :class:`BeautifulSoup` ya parseada

    Returns:
        Número total de páginas (mínimo 1)
    """
    s = soup if soup is not None else BeautifulSoup(html, "lxml")

    # Preferir contador total de reseñas (5 reseñas por página)
    total_reviews = review_count(html, soup=s)
    if total_reviews is not None:
        return max(1, math.ceil(total_reviews / 5))

    # Fallback: buscar el número máximo en los botones de paginación
    nums = [
        int(m.group())
        for a in s.select("ul.pagination li a")
        if (m := re.search(r"\d+", a.get_text()))
    ]
    return max(nums) if nums else 1
