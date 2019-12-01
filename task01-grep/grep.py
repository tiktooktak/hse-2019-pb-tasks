#!/usr/bin/env python3
"""
This script simulates GREP and can work with some flags: -E, -c, -x, -i, -l, -L, -v.
You can get more information if you run it with the flag '--help'
"""
from typing import List, Optional, Any, Tuple, Pattern
import sys
import re
import argparse
import os


def split_files_by_existence(file_names: List[str]) -> Tuple[List[Any], List[Any]]:
    """
    Gets a list of file names and exclude such files that don't exist
    :param file_names: names of files
    :return: list of the existing files
    """
    existing_files = []
    nonexistent_files = []
    for file_name in file_names:
        if os.path.isfile(file_name):
            existing_files.append(file_name)
        else:
            nonexistent_files.append(file_name)
    return existing_files, nonexistent_files


def read_files(file_names: List[str]) -> List[List[str]]:
    """
    Gets a list of file names and return a list of all lines from them (in lists)
    :param file_names: names of files
    :return: a list of all lines
    """
    all_lines = []
    for file_name in file_names:
        with open(file_name, 'r') as input_file:
            all_lines.append(input_file.readlines())
    return all_lines


def strip_lines(lines: List[str]) -> List[str]:
    """
    Strips \n symbol
    :param lines: the lines to be stripped
    :return: list of new lines
    """
    return [line.rstrip('\n') for line in lines]


def compile_regex(pattern: str, regex_mode: bool, ignore_mode: bool):
    """
    Compiles regex for searching the pattern
    :param pattern: pattern to be searched
    :param regex_mode: regular or not
    :param ignore_mode: if true the regex ignores letter cases
    :return:
    """
    if not regex_mode:
        pattern = re.escape(pattern)
    return re.compile(pattern, flags=re.IGNORECASE) if ignore_mode else re.compile(pattern)


def match_line(line: str, searcher: Pattern[str], invert_mode: bool,
               fullmatch_mode: bool) -> bool:
    """
    Check if the line matches the pattern with the flags
    :param line: the given line
    :param invert_mode: -i flag
    :param fullmatch_mode: -x flag
    :param searcher: for searching
    :return:
    """
    matched = searcher.search(line) if not fullmatch_mode else searcher.fullmatch(line)
    return invert_mode ^ bool(matched)


def filter_lines(lines: List[str], searcher: Pattern[str], invert_mode: bool,
                 fullmatch_mode: bool) -> List[str]:
    """
    Searches for lines that match pattern
    :param lines: lines to be checked
    :param invert_mode: -v flag
    :param fullmatch_mode: -x flag
    :param searcher: for searching pattern
    """
    return [line for line in lines if match_line(line, searcher, invert_mode, fullmatch_mode)]


def prepare_output(lines: List[str], source: Optional[str], counting_mode: bool,
                   only_files_mode: bool, only_not_files_mode: bool) -> List[str]:
    """
    Process the lines before output to satisfy the flags
    :param lines: the given lines
    :param source: the name of file
    :param counting_mode: -c flag
    :param only_files_mode: -l flag
    :param only_not_files_mode: -L flag
    :return: list of the output
    """
    if only_files_mode or only_not_files_mode:
        assert source
        # xor means that if only_not_files_mode is true then we are sure that
        # only_files_mode is false and we can just invert the result
        output_lines = [source] if bool(lines) ^ only_not_files_mode else []
    else:
        prefix = f'{source}:' if source else ''
        if counting_mode:
            lines = [str(len(lines))]
        output_lines = [f'{prefix}{line}' for line in lines]
    return output_lines


def print_matched_lines(output_lines: List[str]) -> None:
    """
    Prints all the given lines
    :param output_lines: lines to be printed
    """
    for line in output_lines:
        print(line)


def parse_arguments(args_str: List[str]) -> argparse.Namespace:
    """
    Gets arguments and parses them
    :param args_str: arguments
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('pattern', type=str)
    parser.add_argument('files', nargs='*')
    parser.add_argument('-E', dest='regex', action='store_true')
    parser.add_argument('-v', dest='invert', action='store_true')
    parser.add_argument('-i', dest='ignore', action='store_true')
    parser.add_argument('-x', dest='fullmatch', action='store_true')
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument('-c', dest='counting', action='store_true')
    format_group.add_argument('-l', dest='only_files', action='store_true',
                              help='Require file name to be set')
    format_group.add_argument('-L', dest='only_not_files', action='store_true',
                              help='Require file name to be set')
    return parser.parse_args(args_str)


def main(args_str: List[str]):
    """
    :param args_str: arguments of the command line
    """
    args = parse_arguments(args_str)
    if args.files:
        sources, nonexistent_files = split_files_by_existence(args.files)
        all_lines = read_files(sources)
        if nonexistent_files:
            for file in nonexistent_files:
                print(f'No such file: {file}', file=sys.stderr)
            return
    else:
        all_lines = [sys.stdin.readlines()]
        sources = [None]

    if len(args.files) == 1 and not args.only_files and not args.only_not_files:
        sources = [None]

    searcher = compile_regex(args.pattern, args.regex, args.ignore)

    for lines, source in zip(all_lines, sources):
        lines = strip_lines(lines)
        matched_lines = filter_lines(lines, searcher, args.invert, args.fullmatch)
        output_lines = prepare_output(matched_lines, source, args.counting,
                                      args.only_files, args.only_not_files)
        print_matched_lines(output_lines)


if __name__ == '__main__':
    main(sys.argv[1:])
