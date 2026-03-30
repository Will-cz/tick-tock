"""PyInstaller runtime hook that sets prototype as packaged default.

Current build policy keeps prototype as the default launch mode for packaged
EXEs unless the user explicitly sets a different mode.
"""

import os

os.environ.setdefault("TICK_TOCK_DEFAULT_ENV", "prototype")
