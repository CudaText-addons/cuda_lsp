import sys
from cudatext import *
from cudax_lib import get_translation
_ = get_translation(__file__)  # I18N

# if python too old - give msgbox and disable plugin
ver = sys.version_info
if (ver.major, ver.minor) < (3, 8):
    msg = _('LSP: current Python version is not supported. '
            'Please upgrade to Python 3.8 or newer.')
    callback = lambda *args, msg=msg, **vargs: msg_box(msg, MB_OK or MB_ICONWARNING)
    timer_proc(TIMER_START_ONE, callback, 1000)
else:
    from .lsp import Command