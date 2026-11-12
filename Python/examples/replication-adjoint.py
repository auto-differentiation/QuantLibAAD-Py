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
# # Static replication of a barrier option, with sensitivities
#
# Copyright (&copy;) 2023 Xcelerit Computing Limited.
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
# This is a port of the `AdjointReplication` C++ example, which follows the
# static replication of a down-and-out barrier option with European options
# from M. Joshi, *The Concepts and Practice of Mathematical Finance*,
# chapter 17.  A portfolio is built that matches the barrier option's payoff
# on a set of points along the barrier: it starts from a put struck at the
# option's strike, a digital put and a put struck at the barrier, and then
# successively adds puts expiring at earlier dates whose notionals are chosen
# to make the portfolio worthless whenever the underlying touches the barrier
# at those dates.  Because the notionals are computed from portfolio values
# during the construction, the whole build is recorded on the tape, and the
# sensitivities of the final portfolio value to the zero rates, the strike,
# the volatility, the underlying, and the barrier level come out of a single
# adjoint pass.  The results are cross-checked against central finite
# differences.
#
# One difference from the C++ code: there, a single variable holds the flat
# 4% rate used at every curve node, so its adjoint accumulates the sum of the
# per-node sensitivities.  Here each node gets its own input (all set to
# 4%), so the rhos are reported per node; their sum is the corresponding
# single-variable sensitivity.

# %%
import QuantLibAAD as ql
from xad.adj_1st import Tape
from xad import value
import pandas as pd

# %% [markdown]
# ### Global parameters

# %%
todaysDate = ql.Date(29, ql.May, 2006)
ql.Settings.instance().evaluationDate = todaysDate
dayCounter = ql.Actual365Fixed()
maturity = todaysDate + ql.Period(1, ql.Years)

# the zero curve dates: today plus these offsets in days
offsets = [13, 41, 75, 165, 256, 345, 524, 703]
dates = [todaysDate] + [todaysDate + n for n in offsets]

# setup and activate the tape
tape = Tape()
tape.activate()

# %%
interactive = "get_ipython" in globals()

# %% [markdown]
# ### Inputs
#
# The option to replicate is a down-and-out put with strike 101 and barrier
# 70 on an underlying at 100, with volatility 0.20 and a flat 4% zero curve.

# %%
inputs = (
    [(f"rate {d}", 0.04) for d in dates]
    + [("strike", 101.0), ("volatility", 0.20),
       ("underlying", 100.0), ("barrier", 70.0)]
)
rebate = 0.0


# %% [markdown]
# ### The reference barrier option


# %%
def priceBarrierOption(rates, strike, volatility, underlying, barrier):
    termStructure = ql.ZeroCurve(dates, rates, dayCounter)
    volTS = ql.BlackConstantVol(
        0, ql.NullCalendar(), ql.QuoteHandle(ql.SimpleQuote(volatility)), dayCounter
    )
    process = ql.BlackScholesProcess(
        ql.QuoteHandle(ql.SimpleQuote(underlying)),
        ql.YieldTermStructureHandle(termStructure),
        ql.BlackVolTermStructureHandle(volTS),
    )
    option = ql.BarrierOption(
        ql.Barrier.DownOut,
        barrier,
        rebate,
        ql.PlainVanillaPayoff(ql.Option.Put, strike),
        ql.EuropeanExercise(maturity),
    )
    option.setPricingEngine(ql.AnalyticBarrierEngine(process))
    return option.NPV()


# %% [markdown]
# ### The replicating portfolio
#
# The kill loop runs over 26 fortnightly dates (B = 26 blocks of t = 2
# weeks).  Each iteration values the current portfolio and the latest put with
# the evaluation date moved to the previous kill date and the underlying set
# to the barrier, then subtracts the put with the notional that makes the
# portfolio worthless at that point.


# %%
def pricePortfolio(rates, strike, volatility, underlying, barrier):
    termStructure = ql.ZeroCurve(dates, rates, dayCounter)
    volTS = ql.BlackConstantVol(
        0, ql.NullCalendar(), ql.QuoteHandle(ql.SimpleQuote(volatility)), dayCounter
    )
    underlyingQuote = ql.SimpleQuote(underlying)
    process = ql.BlackScholesProcess(
        ql.QuoteHandle(underlyingQuote),
        ql.YieldTermStructureHandle(termStructure),
        ql.BlackVolTermStructureHandle(volTS),
    )
    engine = ql.AnalyticEuropeanEngine(process)
    exercise = ql.EuropeanExercise(maturity)
    payoff = ql.PlainVanillaPayoff(ql.Option.Put, strike)

    portfolio = ql.CompositeInstrument()
    # final payoff first, as shown in Joshi: a put struck at K...
    put = ql.EuropeanOption(payoff, exercise)
    put.setPricingEngine(engine)
    portfolio.add(put)
    # ...minus a digital put struck at B of notional K-B...
    digitalPut = ql.EuropeanOption(
        ql.CashOrNothingPayoff(ql.Option.Put, barrier, 1.0), exercise
    )
    digitalPut.setPricingEngine(engine)
    portfolio.subtract(digitalPut, strike - barrier)
    # ...minus a put struck at B.
    lowerPut = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.Option.Put, barrier), exercise
    )
    lowerPut.setPricingEngine(engine)
    portfolio.subtract(lowerPut)

    # now use puts struck at B to kill the value of the portfolio
    # on a number of points (B, t)
    B = 26  # number of dates
    t = 2  # spacing of the dates, in weeks
    for i in range(B * t, t - 1, -t):
        innerExercise = ql.EuropeanExercise(todaysDate + ql.Period(i, ql.Weeks))
        innerPut = ql.EuropeanOption(
            ql.PlainVanillaPayoff(ql.Option.Put, barrier), innerExercise
        )
        innerPut.setPricingEngine(engine)
        # evaluate the current portfolio and the latest put at (B, t)...
        killDate = todaysDate + ql.Period(i - t, ql.Weeks)
        ql.Settings.instance().evaluationDate = killDate
        underlyingQuote.setValue(barrier)
        portfolioValue = portfolio.NPV()
        putValue = innerPut.NPV()
        # ...and subtract the put with the notional that kills the value
        portfolio.subtract(innerPut, portfolioValue / putValue)

    ql.Settings.instance().evaluationDate = todaysDate
    underlyingQuote.setValue(underlying)
    return portfolio.NPV()


# %% [markdown]
# ### Sensitivities of the replicating portfolio
#
# One adjoint pass gives the sensitivity of the portfolio value to every
# input, returned as a dict keyed by input name so the calculation can be
# reused from other code or a notebook.


# %%
def aad_sensitivities():
    rates_in = [ql.Real(v) for _, v in inputs[:9]]
    strike_in = ql.Real(inputs[9][1])
    volatility_in = ql.Real(inputs[10][1])
    underlying_in = ql.Real(inputs[11][1])
    barrier_in = ql.Real(inputs[12][1])

    tape.registerInputs(rates_in)
    tape.registerInput(strike_in)
    tape.registerInput(volatility_in)
    tape.registerInput(underlying_in)
    tape.registerInput(barrier_in)

    tape.newRecording()
    portfolioValue = pricePortfolio(
        rates_in, strike_in, volatility_in, underlying_in, barrier_in
    )

    tape.registerOutput(portfolioValue)
    portfolioValue.derivative = 1.0
    tape.computeAdjoints()

    sensitivities = {f"rate {d}": r.derivative for d, r in zip(dates, rates_in)}
    sensitivities["strike"] = strike_in.derivative
    sensitivities["volatility"] = volatility_in.derivative
    sensitivities["underlying"] = underlying_in.derivative
    sensitivities["barrier"] = barrier_in.derivative
    return value(portfolioValue), sensitivities


# %%
portfolioValue, sensitivities = aad_sensitivities()

# the reference barrier option, priced without the tape
barrierValue = value(
    priceBarrierOption(
        [ql.Real(v) for _, v in inputs[:9]],
        ql.Real(inputs[9][1]),
        ql.Real(inputs[10][1]),
        ql.Real(inputs[11][1]),
        ql.Real(inputs[12][1]),
    )
)
print(f"Original barrier option value: {barrierValue:.15f}")
print(f"Replicating portfolio value  : {portfolioValue:.15f}")

# %%
sensitivities_rows = [("rho", f"rate {d}", sensitivities[f"rate {d}"]) for d in dates]
sensitivities_rows += [
    ("strike sensitivity", "strike", sensitivities["strike"]),
    ("vega", "volatility", sensitivities["volatility"]),
    ("delta", "underlying", sensitivities["underlying"]),
    ("barrier sensitivity", "barrier", sensitivities["barrier"]),
]

# %%
df = pd.DataFrame(sensitivities_rows, columns=["Sensitivity", "Input", "Value"])
df.style.hide(axis="index")

# %%
if not interactive:
    print(df.to_string(index=False))

# %% [markdown]
# ### Cross-check by central differences
#
# Each input is bumped up and down in turn and the portfolio rebuilt and
# repriced without the tape; the central differences should match the
# adjoints above.  The largest relative difference over all 13 inputs is
# printed.  As in `trade-risk.py`, each difference is relative to its own
# sensitivity, or absolute below a floor, where rounding in the central
# differences dominates: sensitivities smaller than 0.01% of the largest
# are compared against that floor.
#
# The largest difference is on a small rate sensitivity (2.7e-3), where the
# central differences are at their noise floor through the 26-step kill
# loop; the large sensitivities agree to about 1e-8.

# %%
def priceFromFlat(values):
    return value(
        pricePortfolio(
            [ql.Real(r) for r in values[:9]],
            ql.Real(values[9]),
            ql.Real(values[10]),
            ql.Real(values[11]),
            ql.Real(values[12]),
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
