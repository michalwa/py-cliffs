from typing import Optional


class Identifiable:
    """Mixin class for any node that can be assigned a string identifier"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identifier = None  # type: Optional[str]

    def flattened(self):
        flat = super().flattened()
        flat.identifier = self.identifier
        return flat
