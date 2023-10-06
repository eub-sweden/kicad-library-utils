# EUB fork changes/additions
The following changes were made to the `klc-check/check_footprint.py` and `klc-check/check_symbol.py` scripts.

They are used to check if a symbol library or footprint follows the [KiCad Library Convention (KLC)](klc.kicad.org).

## Rule exceptions
We have added functionality to ignore specific warnings/errors for specific footprints/symbols.

This is done by adding a list of the ignored rules in a custom field.

For symbols, add a new field with the name `klc-exceptions` and list the rules in the value column. The show checkbox should not be checked.

For footprints, add a new field in footprint properties, in the text items column write `klc-exceptions=` and list the rules at the end in the same column. The layer should be User.1 and the show checkbox should not be checked.

The rules should be listed in all upper case with comma as delimiter and no spaces. like this "S4.4,S6.2".

## Rule ignoring
The `klc-check/check_footprint.py` script has been extended with an additional argument "-i" that makes it possible to ignore specific rules when running the script.

This is useful when a rule should be ignored for every single footprint in a library.

For example, if you want to ignore the 3D model requirements, run the following: `check_footprint.py -i F9.3 -vv <FOOTPRINT_LIB_FOLDER>/*.kicad_mod`



# KiCad Library Utils

This repository contains a variety of tools related to the libraries used in [KiCad](https://kicad.org/):

* symbols
* footprints
* 3D models

These tools can be used for the development of the [official KiCad libraries](https://gitlab.com/kicad/libraries) as well as for custom (internal) libraries.

The tools are currently mainly concerned with quality and style checks (e.g. for CI tests) according to the [KLC rules](https://klc.kicad.org/).

Adding custom (internal) rules for your own libraries is a bit cumbersome at the moment (you need to maintain your private fork of this repository), but their usage is within the targeted scope of these tools.
Your contribution for improving this situation is welcome.

Other tools (beside style and quality checks) are welcome to this repository, too.


# Repository content

## klc-check directory

**check_symbol.py**: Script for checking [KLC][] compliance of symbol files.

**check_footprint.py**: Script for checking [KLC][] compliance of footprint files.

**check_3d_coverage.py**: Script for checking which KiCad footprints in a `.pretty` library have 3D models. It also shows unused 3D model files.

**comparelibs.py**: Script to compare two versions of the same library. Used as part of the `kicad-symbols` CI.

[KLC]: http://kicad.org/libraries/klc/

### gitlabci directory

Contains helper scripts to run the CI for the following repos
* kicad-symbols
* kicad-footprints

## common directory

Contains various python libraries used by the check scripts and the generators.
* **kicad_mod.py**: A Python module for loading, editing, and saving KiCad footprint files.
* **kicad_sym.py**: A Python module for loading, editing, and saving KiCad symbol libraries.

## symbol-generators

**example-generator.py**: An example on how to create symbols using python

## tools directory

**compare_sexpr_files.sh**: Normalizes and compares two sexpr files. Those can be `kicad_sym` or `kicad_mod` files.

## test directory

**read_write_kicad_sym.sh** Opens `.kicad_sym` files, parses them and writes them to a temp-file. Then the temp-file and original file are normalized and compared. If the reader and writer implementation are correct there should be no differences.

In the future it is planned to run this over the whole library to check if the scripts are working properly.

How to use
==========

## Symbol Library Checker

    # first get into klc-check directory
    cd kicad-library-utils/klc-check

    # run the script passing the files to be checked
    ./check_symbol.py path_to_lib1 path_to_lib2

    # to check a specific component you can use the -c flag
    ./check_symbol.py -c component_name path_to_lib1

    # run the following 'h'elp command to see other options
    ./check_symbol.py -h

## Footprint Checker

    # first get into klc-check directory
    cd kicad-library-utils/klc-check

    # run the script passing the files to be checked
    ./check_footprint.py path_to_fp1.kicad_mod path_to_fp2.kicad_mod

    # Add `-v`, `-vv`, or `-vvv` for extra verbose output. The most useful is `-vv`, which explains in details the violations. Ex:
    ./check_footprint.py path_to_fp1.kicad_mod path_to_fp2.kicad_mod -vv

    # run the following 'h'elp command to see other options
    ./check_footprint.py -h


## 3D Coverage Checker

    # first get into klc-check directory
    cd kicad-library-utils/klc-check

    # run the script to check all footprints
    ./check_3d_coverage.py

    # run the script to check only the specified .pretty folder
    ./check_3d_coverage.py --pretty Package_SO

    # run the following 'h'elp command to see other options
    ./check_3d_coverage.py -h

## Compare Symbol Libraries

    # first get into klc-check directory
    cd kicad-library-utils/klc-check

    # run the script passing the libraries to be compared
    ./comparelibs.py --new path_to_new_lib --old path_to_old_lib

    # to also do a KLC check for each new or changed symbol use the --check flag
    ./comparelibs.py --new path_to_new_lib --old path_to_old_lib --check

    # run the following 'h'elp command to see other options
    ./comparelibs.py -h

# Contributing

Please keep in mind, that this repository is mainly targeted at the [official KiCad libraries](gitlab.com/kicad/libraries/).
Thus you should manage your custom rules outside of this repository.
Re-usable infrastructure (e.g. for supporting custom rules) is welcome, of course.

## Python code style

The tools [black](https://black.readthedocs.io/) and [isort](https://pycqa.github.io/isort/) are used for formatting the code.
You should apply this format before committing code:
```shell
make style
```

All python code should follow [PEP8](https://www.python.org/dev/peps/pep-0008/).
This style and many other issues can be tested via [flake8](https://flake8.pycqa.org/en/latest/) (also executed as part of the CI tests):
```shell
make lint
```

Please refrain from using recently introduced features of the Python language, which are not yet supported by the most recent stable release of major distributions (e.g. Debian).


## Check before committing

Usually, you commit the footprint (or symbol) and let CI check your job.
You can let git pass the check before actually committing. If it's red,
fix your footprint (or symbol) !

To automate the call, place a hook file in the footprint git's hooks directory,
**/somewhere/kicad/kicad-footprints/.git/hooks** named **pre-commit**
with the following content:
```
#!/bin/bash

ERR=0
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
for F in $STAGED_FILES; do
  if [[ "${F: -10}"  == ".kicad_mod" ]] ; then
    x=$(python3  /somewhere/kicad-library-utils/klc-check/check_footprint.py  -vv "$F")
    echo "$x"
    echo "$x" | grep -q "Violating" &&  ERR=1
  fi
done
exit $ERR
```
diff-filter=ACM stands for Added, Copied, Modified

The script skips non footprint-files. Use **git commit --no-verify** to bypass the hook.

Place the script in the footprint (or symbol) directory, not in the library-utils' git !


Notice
======

The scripts use a different algorithm to generate files in relation to the KiCad saving action. That will result output files with more modified lines than expected, because the line generally are repositioned. However, the file still functional.

Always check the generated files by opening them on KiCad. Additionally, if you are working over a git repository (if not, you should) you can commit your work before proceed with the scripts, this will put you safe of any trouble. Also, you would use git diff to give a look at the modifications.
