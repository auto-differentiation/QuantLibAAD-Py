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
# # European options with sensitivities
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
# This is a port of the `AdjointEuropeanEquityOption` C++ example.  It prices
# a portfolio of European put options (several underlyings, each with a range
# of strikes) over a zero curve and a black variance curve, and computes the
# sensitivities of the total portfolio value to all market inputs (the zero
# rates, the volatilities, the strikes, the underlyings, and the dividend
# yield) in a single adjoint pass.  The results are cross-checked against
# central finite differences.

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
# ### Market data
#
# The zero curve and the variance curve share the same node dates: the
# settlement date plus the offsets below.  The first rate is repeated at the
# first offset date, as in the C++ example.

# %%
offsets = [13, 41, 75, 165, 256, 345, 524, 703]
curveRates = [0.0357, 0.0349, 0.0341, 0.0355, 0.0359, 0.0368, 0.0386, 0.0401]
curveVols = [0.20, 0.18, 0.178, 0.183, 0.192, 0.203, 0.215, 0.208]

dates = [settlementDate] + [settlementDate + n for n in offsets]

# the inputs in a flat list, in the same order as the sensitivities dict:
# 9 rates, 8 volatilities, 70 strikes, 10 underlyings, the dividend yield
inputs = (
    [(f"rate {d}", r) for d, r in zip(dates, [curveRates[0]] + curveRates)]
    + [(f"vol {d}", v) for d, v in zip(dates[1:], curveVols)]
    + [(f"strike {s}", float(s)) for s in range(10, 80)]
    + [(f"underlying {s}", float(s)) for s in range(15, 61, 5)]
    + [("dividend yield", 0.01)]
)


# %% [markdown]
# ### Pricing
#
# The whole portfolio is priced inside the recording, so that the curves and
# instruments are built from the registered inputs.


# %%
def pricePortfolio(rates, vols, strikes, underlyings, dividendYield):
    termStructure = ql.ZeroCurve(dates, rates, dayCounter)
    dividendTS = ql.FlatForward(settlementDate, dividendYield, dayCounter)
    # the variance curve drops the first (settlement) date
    volTS = ql.BlackVarianceCurve(settlementDate, dates[1:], vols, dayCounter)

    exercise = ql.EuropeanExercise(maturity)
    value = ql.Real(0.0)
    for underlying in underlyings:
        process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(ql.SimpleQuote(underlying)),
            ql.YieldTermStructureHandle(dividendTS),
            ql.YieldTermStructureHandle(termStructure),
            ql.BlackVolTermStructureHandle(volTS),
        )
        engine = ql.AnalyticEuropeanEngine(process)
        for strike in strikes:
            option = ql.VanillaOption(
                ql.PlainVanillaPayoff(ql.Option.Put, strike), exercise
            )
            option.setPricingEngine(engine)
            value = value + option.NPV()
    return value


# %% [markdown]
# ### Sensitivities
#
# One adjoint pass gives the sensitivity of the portfolio value to every
# input, returned as a dict keyed by input name so the calculation can be
# reused from other code or a notebook.


# %%
def aad_sensitivities():
    rates_in = [ql.Real(r) for _, r in inputs[:9]]
    vols_in = [ql.Real(v) for _, v in inputs[9:17]]
    strikes_in = [ql.Real(s) for _, s in inputs[17:87]]
    underlyings_in = [ql.Real(u) for _, u in inputs[87:97]]
    dividendYield_in = ql.Real(inputs[97][1])

    tape.registerInputs(rates_in)
    tape.registerInputs(vols_in)
    tape.registerInputs(strikes_in)
    tape.registerInputs(underlyings_in)
    tape.registerInput(dividendYield_in)

    tape.newRecording()
    portfolioValue = pricePortfolio(
        rates_in, vols_in, strikes_in, underlyings_in, dividendYield_in
    )

    tape.registerOutput(portfolioValue)
    portfolioValue.derivative = 1.0
    tape.computeAdjoints()

    sensitivities = {}
    for d, rate in zip(dates, rates_in):
        sensitivities[f"rate {d}"] = rate.derivative
    for d, vol in zip(dates[1:], vols_in):
        sensitivities[f"vol {d}"] = vol.derivative
    for strike in strikes_in:
        sensitivities[f"strike {value(strike):.0f}"] = strike.derivative
    for underlying in underlyings_in:
        sensitivities[f"underlying {value(underlying):.0f}"] = underlying.derivative
    sensitivities["dividend yield"] = dividendYield_in.derivative
    return value(portfolioValue), sensitivities


# %%
portfolioValue, sensitivities = aad_sensitivities()
print(f"Portfolio value: {portfolioValue:.5f}")

# %%
results = []
for d in dates:
    results.append(("rho", f"rate {d}", sensitivities[f"rate {d}"]))
for d in dates[1:]:
    results.append(("vega", f"vol {d}", sensitivities[f"vol {d}"]))
for s in range(10, 80):
    results.append(("strike sensitivity", f"strike {s}", sensitivities[f"strike {s}"]))
for s in range(15, 61, 5):
    results.append(("delta", f"underlying {s}", sensitivities[f"underlying {s}"]))
results.append(("dividend rho", "dividend yield", sensitivities["dividend yield"]))

# %%
df = pd.DataFrame(results, columns=["Sensitivity", "Input", "Value"])
df.style.hide(axis="index")

# %%
if not interactive:
    print(df.to_string(index=False))

# %% [markdown]
# ### Cross-check by central differences
#
# Each input is bumped up and down in turn and the portfolio repriced
# without the tape; the central differences should match the adjoints
# above.  The largest relative difference over all 98 inputs is printed.
# As in `trade-risk.py`, each difference is relative to its own sensitivity,
# or absolute below a floor, where rounding in the central differences
# dominates: sensitivities smaller than 0.01% of the largest are compared
# against that floor.

# %%
def priceFromFlat(values):
    return value(
        pricePortfolio(
            [ql.Real(r) for r in values[:9]],
            [ql.Real(v) for v in values[9:17]],
            [ql.Real(s) for s in values[17:87]],
            [ql.Real(u) for u in values[87:97]],
            ql.Real(values[97]),
        )
    )


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
    central = (priceFromFlat(up) - priceFromFlat(down)) / (2.0 * h)
    relative = abs(sensitivities[name] - central) / max(abs(central), floor)
    if relative > worst:
        worst, worstName = relative, name
print(
    f"Largest relative difference over all {len(inputs)} inputs: "
    f"{worst:.1e} ({worstName})"
)

# %%
tape.deactivate()
