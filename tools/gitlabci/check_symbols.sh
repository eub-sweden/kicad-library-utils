#!/bin/bash
source $(dirname ${BASH_SOURCE[0]})/common.sh

# print python version
python3 -V

# clone required repos
git clone --depth 1 https://gitlab.com/kicad/libraries/kicad-footprints.git $CI_BUILDS_DIR/kicad-footprints

# get the list of files we want to compare
echo "Comparing range $BASE_SHA to $TARGET_SHA"
LIBS_NEW=$(git diff-tree --diff-filter=AMR --no-commit-id --oneline --name-only -r "$BASE_SHA" "$TARGET_SHA" | grep '\.kicad_sym$') #| sed -e "s#^#$CI_PROJECT_DIR/#;")
LIBS_OLD=$(git diff-tree --diff-filter=DMR --no-commit-id --oneline --name-only -r "$BASE_SHA" "$TARGET_SHA" | grep '\.kicad_sym$')

# do some debug output
echo "Found new Libraries: $LIBS_NEW"
echo "Found old Libraries: $LIBS_OLD"

# checkout the previous version of the 'old' files so we can compare against them
mkdir -p $CI_BUILDS_DIR/kicad-symbols-prev
for LIBNAME in $LIBS_OLD; do
  git cat-file blob "$BASE_SHA:$LIBNAME" > "$CI_BUILDS_DIR/kicad-symbols-prev/$LIBNAME"
done

# now run comparelibs
$CI_BUILDS_DIR/kicad-library-utils/klc-check/comparelibs.py -v --old $CI_BUILDS_DIR/kicad-symbols-prev/* --new $LIBS_NEW --check --check-derived --footprint_directory $CI_BUILDS_DIR/kicad-footprints -m
SYM_ERROR_CNT=$?
echo "SymbolErrorCount $SYM_ERROR_CNT" >> metrics.txt

# check lib table
$CI_BUILDS_DIR/kicad-library-utils/klc-check/check_lib_table.py $CI_PROJECT_DIR/*.kicad_sym --table $CI_PROJECT_DIR/sym-lib-table
TAB_ERROR_CNT=$?
echo "LibTableErrorCount $TAB_ERROR_CNT" >> metrics.txt

exit $(($SYM_ERROR_CNT + $TAB_ERROR_CNT))
