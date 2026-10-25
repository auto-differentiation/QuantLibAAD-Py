#!/usr/bin/env bash
##############################################################################
#  Syncs SWIG/ with a QuantLib-SWIG release and re-applies the XAD changes:
#
#    tools/sync-swig.sh <tag> [<QuantLib-SWIG checkout>]
#        copies SWIG/*.i of <tag> into SWIG/ and applies SWIG/patches/*.patch;
#        failed hunks are left in SWIG/*.rej
#    tools/sync-swig.sh --update-patches <tag> [<QuantLib-SWIG checkout>]
#        regenerates SWIG/patches/ from SWIG/ against <tag>, after resolving
#
#  Without a checkout, <tag> is cloned from GitHub. The XAD-only files
#  (tape.i, date_extra.i, fdm_extra.i, vectors_extra.i) are kept as they are.
#
#  This file is part of QuantLib-Risks, a Python wrapper for QuantLib enabled
#  for risk computation using automatic differentiation. It uses XAD,
#  a fast and comprehensive C++ library for automatic differentiation.
#
#  Copyright (C) 2010-2026 Xcelerit Computing Ltd.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

set -euo pipefail

xad_only="tape.i date_extra.i fdm_extra.i vectors_extra.i"
url=https://github.com/lballabio/QuantLib-SWIG.git

update=0
if [ "${1:-}" = "--update-patches" ]; then
    update=1
    shift
fi
if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    sed -n '3,12p' "$0" | sed 's/^# \{0,2\}//'
    exit 2
fi
tag=$1
root=$(cd "$(dirname "$0")/.." && pwd)
swig=$root/SWIG
patches=$swig/patches

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

if [ $# -eq 2 ]; then
    upstream=$(cd "$2" && pwd)
    git -C "$upstream" rev-parse -q --verify "$tag^{commit}" >/dev/null ||
        git -C "$upstream" fetch -q origin tag "$tag"
else
    upstream=$tmp/QuantLib-SWIG
    git clone -q --depth 1 --branch "$tag" "$url" "$upstream"
fi

# pristine upstream SWIG/*.i of <tag>
mkdir -p "$tmp/a/SWIG"
git -C "$upstream" archive "$tag" SWIG | tar -x -C "$tmp/a"
find "$tmp/a/SWIG" -mindepth 1 ! -name '*.i' -exec rm -rf {} +

is_xad_only() {
    case " $xad_only " in *" $1 "*) return 0 ;; esac
    return 1
}

if [ $update -eq 1 ]; then
    rm -f "$patches"/*.patch
    mkdir -p "$patches"
    for f in "$swig"/*.i; do
        name=$(basename "$f")
        is_xad_only "$name" && continue
        [ -f "$tmp/a/SWIG/$name" ] || { echo "not in $tag: SWIG/$name" >&2; exit 1; }
        mkdir -p "$tmp/b/SWIG"
        cp "$f" "$tmp/b/SWIG/$name"
        (cd "$tmp" && git diff --no-index --no-prefix --no-color \
            "a/SWIG/$name" "b/SWIG/$name" || true) |
            sed '/^index /d' > "$patches/$name.patch"
        [ -s "$patches/$name.patch" ] || rm "$patches/$name.patch"
    done
    echo "SWIG/patches updated against $tag"
    exit 0
fi

for f in "$swig"/*.i; do
    name=$(basename "$f")
    is_xad_only "$name" || rm "$f"
done
cp "$tmp"/a/SWIG/*.i "$swig/"
rm -f "$swig"/*.rej "$swig"/*.orig

failed=0
for p in "$patches"/*.patch; do
    [ -e "$p" ] || continue
    if ! git -C "$root" apply --reject --whitespace=nowarn "$p" 2>"$tmp/err"; then
        echo "conflict: $(basename "$p")" >&2
        sed 's/^/  /' "$tmp/err" >&2
        failed=1
    fi
done

if [ $failed -ne 0 ]; then
    echo "resolve SWIG/*.rej, then run: $0 --update-patches $tag" >&2
    exit 1
fi
echo "SWIG/ synced with QuantLib-SWIG $tag"
