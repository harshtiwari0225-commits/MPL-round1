"""Question content helpers shared by the team routes and services.

Extracted verbatim from the old routes/main.py helpers so arena.py,
judging.py and validation.py all read question JSON fields the same way.
"""
from __future__ import annotations

import json
from typing import List, Optional

from app.models import Question


def allowed_languages(question: Question) -> Optional[List[str]]:
    if not question.allowed_languages:
        return None
    try:
        value = json.loads(question.allowed_languages)
        return [str(v).strip().lower() for v in value] if isinstance(value, list) else None
    except (json.JSONDecodeError, TypeError):
        return None


def starter_code_for(question: Question, language: str) -> Optional[str]:
    if not question.starter_code:
        return None
    try:
        data = json.loads(question.starter_code)
        return data.get(language) if isinstance(data, dict) else question.starter_code
    except (json.JSONDecodeError, TypeError):
        return question.starter_code


def starter_bundle(question: Question) -> Optional[str]:
    """Per-language starter code as the team sees it: a JSON object string.

    One entry per allowed language (default: python), empty entries dropped,
    None when the question carries no starter code at all.
    """
    languages = allowed_languages(question) or ["python"]
    starter = {lang: starter_code_for(question, lang) for lang in languages}
    starter = {k: v for k, v in starter.items() if v}
    return json.dumps(starter) if starter else None
