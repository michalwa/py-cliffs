from typing import Optional


class StIdentifiable:
    """Mixin class for any node that can be assigned an identifier"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identifier = None  # type: Optional[str]
