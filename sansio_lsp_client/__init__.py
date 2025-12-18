"""Client library for managing language server requests & responses."""

from .client import *
from .events import *
from .structs import *

# i merged this version https://github.com/PurpleMyst/sansio-lsp-client/tree/de46dbf5fef94652dda2a3c47e5eedd5e3ed965f
# __init__.py shows 0.12.0 but in fact it is 13 or 14, because 12 was before introducing pydantic2 , and they already published in pypi v13 which is old, so the master repo in github have to version wrong, it is 14 at least
__version__ = "0.12.0"
