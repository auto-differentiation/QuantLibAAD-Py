# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # American options with sensitivities
#
# Copyright (&copy;) 2004, 2005, 2006, 2007 StatPro Italia srl
# Copyright (&copy;) 2024 Xcelerit Computing Limited.
#
# This file is part of QuantLibAAD, a Python wrapper for QuantLib enabled
# for risk computation using automatic differentiation. It uses XAD,
# a fast and comprehensive C++ library for automatic differentiation.
#
# QuantLibAAD and XAD are free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# QuantLibAAD is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# QuantLib is free software: you can redistribute it and/or modify it under the
# terms of the QuantLib license.  You should have received a copy of the
# license along with this program; if not, please email
# <quantlib-dev@lists.sf.net>. The license is also available online at
# <https://www.quantlib.org/license.shtml>.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the license for more details.

# %% [markdown]
# This is a port of the `AdjointAmericanEquityOption` C++ example.  It prices
# an American put option with the finite-difference Black-Scholes engine and
# computes the sensitivities of the price to the risk-free rate, the strike,
# the volatility, the underlying, and the dividend yield in a single adjoint
# pass.  The results are cross-checked against central finite differences.

# %%
import QuantLibAAD as ql
from xad.adj_1st import Tape
from xad import value
import pandas as pd

# %% [markdown]
# ### Global parameters

# %%
calendar = ql.TARGET()
todaysDate = ql.Date(15, ql.May, 1998)
settlementDate = ql.Date(17, ql.May, 1998)
ql.Settings.instance().evaluationDate = todaysDate
dayCounter = ql.Actual365Fixed()
maturity = ql.Date(17, ql.May, 1999)

# setup and activate the tape
tape = Tape()
tape.activate()

# %%
interactive = "get_ipython" in globals()

# %% [markdown]
# ### Market data and option inputs

# %%
inputs = [
    ("risk-free rate", 0.06),
    ("strike", 40.0),
    ("volatility", 0.20),
    ("underlying", 36.0),
    ("dividend yield", 0.00),
]


# %% [markdown]
# ### Pricing
#
# The option and its engine are built inside the recording, so that they are
# constructed from the registered inputs.


# %%
def priceAmerican(riskFreeRate, strike, volatility, underlying, dividendYield):
    termStructure = ql.FlatForward(settlementDate, riskFreeRate, dayCounter)
    dividendTS = ql.FlatForward(settlementDate, dividendYield, dayCounter)
    volTS = ql.BlackConstantVol(settlementDate, calendar, volatility, dayCounter)
    process = ql.BlackScholesMertonProcess(
        ql.QuoteHandle(ql.SimpleQuote(underlying)),
        ql.YieldTermStructureHandle(dividendTS),
        ql.YieldTermStructureHandle(termStructure),
        ql.BlackVolTermStructureHandle(volTS),
    )
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.Option.Put, strike),
        ql.AmericanExercise(settlementDate, maturity),
    )
    timeSteps = 801
    option.setPricingEngine(
        ql.FdBlackScholesVanillaEngine(process, timeSteps, timeSteps - 1)
    )
    return option.NPV()


# %% [markdown]
# ### Greeks
#
# One adjoint pass gives the sensitivity of the option price to every
# input, returned as a dict keyed by input name so the calculation can be
# reused from other code or a notebook.


# %%
def aad_sensitivities():
    riskFreeRate_in = ql.Real(inputs[0][1])
    strike_in = ql.Real(inputs[1][1])
    volatility_in = ql.Real(inputs[2][1])
    underlying_in = ql.Real(inputs[3][1])
    dividendYield_in = ql.Real(inputs[4][1])

    tape.registerInput(riskFreeRate_in)
    tape.registerInput(strike_in)
    tape.registerInput(volatility_in)
    tape.registerInput(underlying_in)
    tape.registerInput(dividendYield_in)

    tape.newRecording()
    optionValue = priceAmerican(
        riskFreeRate_in, strike_in, volatility_in, underlying_in, dividendYield_in
    )

    tape.registerOutput(optionValue)
    optionValue.derivative = 1.0
    tape.computeAdjoints()

    return value(optionValue), {
        "risk-free rate": riskFreeRate_in.derivative,
        "strike": strike_in.derivative,
        "volatility": volatility_in.derivative,
        "underlying": underlying_in.derivative,
        "dividend yield": dividendYield_in.derivative,
    }


# %%
optionValue, sensitivities = aad_sensitivities()
print(f"American option value: {optionValue:.10f}")

# %%
greeks = [
    ("Rho", sensitivities["risk-free rate"]),
    ("Strike sensitivity", sensitivities["strike"]),
    ("Vega", sensitivities["volatility"]),
    ("Delta", sensitivities["underlying"]),
    ("Dividend rho", sensitivities["dividend yield"]),
]

# %%
df = pd.DataFrame(greeks, columns=["Greek", "Value"])
df.style.hide(axis="index")

# %%
if not interactive:
    print(df.to_string(index=False))

# %% [markdown]
# ### Cross-check by central differences
#
# Each input is bumped up and down in turn and the option repriced without
# the tape; the central differences should match the adjoints above.  The
# largest relative difference over all 5 inputs is printed.  As in
# `trade-risk.py`, each difference is relative to its own sensitivity, or
# absolute below a floor, where rounding in the central differences
# dominates: sensitivities smaller than 0.01% of the largest are compared
# against that floor.
#
# The agreement is at the 1e-5 level rather than 1e-8: the option is priced
# on a fixed 801-step finite-difference grid, so the bumped values
# themselves carry grid noise of that size in the rate, the volatility and
# the dividend yield.  The strike and the underlying agree to about 1e-7.

# %%
h = 1e-5
base = [v for _, v in inputs]
largest = max(abs(s) for s in sensitivities.values())
floor = 1e-4 * largest
worst = 0.0
worstName = None
for i, (name, _) in enumerate(inputs):
    up = list(base)
    up[i] += h
    down = list(base)
    down[i] -= h
    central = (
        value(priceAmerican(*[ql.Real(v) for v in up]))
        - value(priceAmerican(*[ql.Real(v) for v in down]))
    ) / (2.0 * h)
    relative = abs(sensitivities[name] - central) / max(abs(central), floor)
    if relative > worst:
        worst, worstName = relative, name
print(
    f"Largest relative difference over all {len(inputs)} inputs: "
    f"{worst:.1e} ({worstName})"
)

# %%
tape.deactivate()
