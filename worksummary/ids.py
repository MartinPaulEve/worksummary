import hashlib
import os
from collections.abc import Iterable


class AmbiguousIdError(Exception):
    def __init__(self, prefix: str, candidates: list[str]):
        self.prefix = prefix
        self.candidates = candidates
        super().__init__(f"prefix {prefix!r} matches {len(candidates)} items")


class NotFoundError(Exception):
    def __init__(self, prefix: str):
        self.prefix = prefix
        super().__init__(f"no item matches prefix {prefix!r}")


def generate_id(description: str, created_at: str) -> str:
    """Compute a 40-char SHA-1 hash from description, timestamp, and a random salt."""
    salt = os.urandom(16).hex()
    payload = f"{description}\0{created_at}\0{salt}".encode()
    return hashlib.sha1(payload).hexdigest()


def shortest_unique_prefixes(hashes: list[str]) -> dict[str, int]:
    """Return the minimum prefix length for each hash to be unique within the set."""
    result: dict[str, int] = {}
    for h in hashes:
        k = 1
        while True:
            prefix = h[:k]
            collisions = [other for other in hashes if other != h and other.startswith(prefix)]
            if not collisions:
                result[h] = k
                break
            k += 1
            if k > len(h):
                result[h] = len(h)
                break
    return result


def resolve(prefix: str, hashes: Iterable[str]) -> str:
    """Return the single hash starting with `prefix`, or raise."""
    matches = [h for h in hashes if h.startswith(prefix)]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise NotFoundError(prefix)
    raise AmbiguousIdError(prefix, matches)
