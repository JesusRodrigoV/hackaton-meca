import re


def has_repeated_chars(s: str, max_repeats: int = 4) -> bool:
    """Return True if any character repeats max_repeats times consecutively."""
    count = 1
    prev = None
    for ch in s:
        if prev is not None and ch == prev:
            count += 1
            if count >= max_repeats:
                return True
        else:
            count = 1
        prev = ch
    return False


def has_sequential_chars(s: str, seq_len: int = 4) -> bool:
    """Return True if there is any ascending or descending sequence of length seq_len.
    Checks only alphabetic or numeric sequences (e.g. 'abcd', '4321').
    """
    if len(s) < seq_len:
        return False
    s_lower = s.lower()
    for i in range(len(s_lower) - seq_len + 1):
        chunk = s_lower[i : i + seq_len]
        if all(c.isalpha() for c in chunk) or all(c.isdigit() for c in chunk):
            inc = all(ord(chunk[j + 1]) - ord(chunk[j]) == 1 for j in range(len(chunk) - 1))
            dec = all(ord(chunk[j]) - ord(chunk[j + 1]) == 1 for j in range(len(chunk) - 1))
            if inc or dec:
                return True
    return False


def validate_password_strength_func(v: str) -> str:
    """Validate password and raise ValueError with message when invalid."""
    if len(v) < 12:
        raise ValueError('La contraseña debe tener 12 caracteres como minimo')
    if not re.search(r"[A-Z]", v):
        raise ValueError("La contraseña debe contener al menos una mayuscula")
    if not re.search(r"[a-z]", v):
        raise ValueError("La contraseña debe contener al menos una minuscula")
    if not re.search(r"[0-9]", v):
        raise ValueError("La contraseña debe contener al menos un numero")
    if not re.search(r"[!@#$%^&*()\-=_+\[\]{}|;:,.<>?]", v):
        raise ValueError("La contraseña debe contener al menos un carácter especial (!@#$%^&*...)")
    if has_repeated_chars(v, max_repeats=3):
        raise ValueError("La contraseña no puede contener el mismo caracter repetido 3 veces seguidas")
    if has_sequential_chars(v, seq_len=3):
        raise ValueError("La contraseña no puede contener secuencias de caracteres (ej. 'abc' o '123')")
    return v


def is_valid_password(v: str) -> bool:
    try:
        validate_password_strength_func(v)
        return True
    except ValueError:
        return False
