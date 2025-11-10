# app/utils/encoding.py
import re
from fastapi import HTTPException

_RE_BAD = re.compile(r"\uFFFD")
_RE_HAS_WORD = re.compile(r"\w", re.UNICODE)

def is_likely_broken(q: str | None) -> bool:
    if not q:
        return False
    if _RE_BAD.search(q):
        return True
    return not bool(_RE_HAS_WORD.search(q))

def validate_utf8_or_raise(q: str | None) -> None:
    if is_likely_broken(q):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "BAD_QUERY_ENCODING",
                "message": "Query must be UTF-8 percent-encoded (RFC 3986). "
                           "Пример: /employees/?q=%D0%B8%D0%B2%D0%B0%D0%BD%D0%BE%D0%B2%D0%B0",
            },
        )
