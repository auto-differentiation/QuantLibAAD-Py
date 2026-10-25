/******************************************************************************
 *  Conversion of xad.adj_1st.Tape arguments to xad::Tape<double>&.
 *
 *  This file is part of QuantLib-Risks, a Python wrapper for QuantLib enabled
 *  for risk computation using automatic differentiation. It uses XAD,
 *  a fast and comprehensive C++ library for automatic differentiation.
 *
 *  Copyright (C) 2010-2024 Xcelerit Computing Ltd.
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Affero General Public License as published
 *  by the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Affero General Public License for more details.
 *
 *  You should have received a copy of the GNU Affero General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *   
 ******************************************************************************/

#ifndef tape_i
#define tape_i

%{
    #include "converters.hpp"
    #include <XAD/XAD.hpp>

    typedef xad::Tape<double> Tape;
%}

typedef xad::Tape<double> Tape;

%typemap(in) xad::Tape<double>& {
    try {
        $1 = &make_Tape_ref($input);
    }
    catch(...) {
        SWIG_exception(SWIG_TypeError, "XAD tape conversion error");
    }
}


%define QL_TYPECHECK_TAPE 4899 %enddef

%typecheck(QL_TYPECHECK_TAPE) xad::Tape<double>& {
    $1 = check_Tape($input) ? 1 : 0;
}

#endif
