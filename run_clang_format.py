#!/usr/bin/python3
'''
Run clang-format.
Helper script to make it easier to use.
'''

import argparse
import re
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List
from termcolor import colored, cprint

@dataclass(order=True)
class Version:
    """ Class for version handling """
    major: int
    minor: int
    patch: int

    def __repr__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

CLANG_FORMAT_VER_REQ = Version(13, 0, 1)

CLANG_FORMAT_VER_REGEX = re.compile(
    r'clang-format version (?P<major>\d+).(?P<minor>\d+).(?P<patch>\d+)'
)

def main() -> int:
    """
    Run clang-format

    Helper script to make it easier to use in Makefiles.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Directory or file", type=str, nargs='+')
    args = parser.parse_args()

    # Check clang-format version
    try:
        clang_format_ver = subprocess.run(["clang-format", "--version"],
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          check=True)
    except subprocess.CalledProcessError as err:
        print(err)
        return -1

    search = CLANG_FORMAT_VER_REGEX.search(clang_format_ver.stdout.decode('UTF-8'))
    assert search, "Incorrect clang-format version output?"

    version = Version(int(search.group('major')),
                      int(search.group('minor')),
                      int(search.group('patch')))
    if version < CLANG_FORMAT_VER_REQ:
        cprint("ERROR: clang-format version is too old!", "red")
        cprint(f"       Requires version {CLANG_FORMAT_VER_REQ} but is {version}", "red")
        return -1

    print(f"Using clang-format version {version}")

    if version.major > CLANG_FORMAT_VER_REQ.major:
        cprint(
            (f"NOTE: Major version used is greater than tested ({CLANG_FORMAT_VER_REQ.major})," +
             " might behave differently."),
            "yellow"
        )

    # Find all .c and .h files
    globbed_files: List[Path] = []
    for input_str in args.path:
        path = Path(input_str)
        if not path.exists() or not (path.is_dir() or path.is_file()):
            print(colored("WARN:", "yellow"),
                  f"{path} doesn't exist or is not file or dir, ignoring")
            continue
        if path.is_dir():
            globbed_files.extend(sorted(path.glob("**/*.c")))
            globbed_files.extend(sorted(path.glob("**/*.h")))
        else:
            assert path.is_file(), "Something is off, should be a file?"
            globbed_files.append(path)

    globbed_files_str = " ".join([str(f.resolve()) for f in globbed_files])
    clang_format_cmd = f"clang-format -i --verbose {globbed_files_str}"

    # Run clang-format on all files
    try:
        format_res = subprocess.run(clang_format_cmd.split(),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    check=True)
    except subprocess.CalledProcessError as err:
        print(err.stderr.decode('UTF-8'))
        return -1

    if format_res.stdout:
        print(format_res.stdout.decode('UTF-8').rstrip())
    if format_res.stderr:
        print(format_res.stderr.decode('UTF-8').rstrip())

    return 0

if __name__ == "__main__":
    sys.exit(main())
