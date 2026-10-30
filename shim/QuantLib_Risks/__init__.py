"""Deprecated alias of QuantLibAAD."""

import sys
import warnings

warnings.warn(
    "QuantLib-Risks is now QuantLibAAD: pip install QuantLibAAD and import QuantLibAAD",
    DeprecationWarning,
    stacklevel=2,
)

from QuantLibAAD import *
from QuantLibAAD import __version__, __hexversion__
from QuantLibAAD import QuantLibAAD as QuantLib_Risks, _QuantLibAAD as _QuantLib_Risks

sys.modules[__name__ + ".QuantLib_Risks"] = QuantLib_Risks
sys.modules[__name__ + "._QuantLib_Risks"] = _QuantLib_Risks

del sys, warnings
