import base64
import hashlib
import re


def snake(s):
    return re.sub(r'[\W_]+', '_', s)


def short_hash(s) -> str:
    md5_hash = hashlib.md5()
    md5_hash.update(s.encode('utf-8'))
    md5_digest = md5_hash.digest()
    base64_encoded = base64.b64encode(md5_digest)
    return base64_encoded.decode('utf-8')
