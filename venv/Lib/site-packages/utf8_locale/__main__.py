# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""The u8loc command-line tool."""

from __future__ import annotations

import argparse
import dataclasses
import os
import subprocess  # noqa: S404
import sys
import typing

from . import detect


if typing.TYPE_CHECKING:
    from collections.abc import Callable


@dataclasses.dataclass(frozen=True)
class Config:
    """Runtime configuration for the u8loc command-line tool."""

    preferred: bool


@dataclasses.dataclass(frozen=True)
class QueryConfig(Config):
    """Runtime configuration for `u8loc -q variable`."""

    query: str


@dataclasses.dataclass(frozen=True)
class RunConfig(Config):
    """Runtime configuration for `u8loc -r program [arg...]`."""

    run_program: list[str]


@dataclasses.dataclass(frozen=True, order=True)
class QueryDef:
    """A parameter for the -q option."""

    name: str
    early: bool
    handler: Callable[[QueryConfig, detect.UTF8Environment], None]
    descr: str


def query_env(cfg: QueryConfig, env: detect.UTF8Environment) -> None:
    """Output the value of an environment variable."""
    value = env.env_vars.get(cfg.query)
    if value is None:
        sys.exit(f"Internal error: query_env(): no value for {cfg.query!r} in {env.env_vars!r}")

    print(value)


def query_list(_cfg: QueryConfig, _env: detect.UTF8Environment) -> None:
    """List the available query options."""
    for qdef in sorted(QUERY_HANDLERS_LIST):
        print(f"{qdef.name:20s} - {qdef.descr}")


def query_preferred(_cfg: QueryConfig, _env: detect.UTF8Environment) -> None:
    """Display the list of preferred languages as per the locale variables."""
    print("\n".join(detect.LanguagesDetect().detect()))


QUERY_HANDLERS_LIST = [
    QueryDef(
        name="LC_ALL",
        early=False,
        handler=query_env,
        descr="The LC_ALL environment variable",
    ),
    QueryDef(
        name="LANGUAGE",
        early=False,
        handler=query_env,
        descr="The LANGUAGE environment variable",
    ),
    QueryDef(
        name="list",
        early=True,
        handler=query_list,
        descr="List the available query parameters",
    ),
    QueryDef(
        name="preferred",
        early=True,
        handler=query_preferred,
        descr="List the preferred languages as per the locale variables",
    ),
]

QUERY_HANDLERS = {qdef.name: qdef for qdef in QUERY_HANDLERS_LIST}


def parse_args() -> Config:
    """Parse the u8loc tool's command-line options."""
    parser = argparse.ArgumentParser(prog="u8loc")
    parser.add_argument(
        "-p",
        dest="preferred",
        action="store_true",
        help="use a locale specified in the LANG and LC_* variables if appropriate",
    )
    parser.add_argument(
        "-q",
        dest="query",
        type=str,
        choices=sorted(QUERY_HANDLERS.keys()),
        help="output the value of an environment variable",
    )
    parser.add_argument(
        "-r",
        dest="run",
        action="store_true",
        help="run the specified program in a UTF-8-friendly environment",
    )
    parser.add_argument(
        "--features",
        action="store_true",
        help="display the features supported by the program and exit",
    )
    parser.add_argument(
        "program",
        type=str,
        nargs="*",
        help="the program to run if -r is specified",
    )

    args = parser.parse_args()

    if args.features:
        print(f"Features: u8loc={detect.VERSION} query-env=0.1 query-preferred=0.1 run=0.1")
        sys.exit(0)

    if int(args.query is not None) + int(args.run) != 1:
        sys.exit("Exactly one of -q or -r must be specified.")

    if args.query:
        return QueryConfig(preferred=args.preferred, query=args.query)

    if args.run:
        if not args.program:
            sys.exit("No program to run specified")
        return RunConfig(preferred=args.preferred, run_program=args.program)

    sys.exit(f"Did not expect to reach the end of parse_args() with {args!r}")


def main() -> None:
    """Parse command-line arguments, dispatch commands."""
    cfg = parse_args()

    if isinstance(cfg, QueryConfig) and QUERY_HANDLERS[cfg.query].early:
        QUERY_HANDLERS[cfg.query].handler(
            cfg,
            detect.UTF8Environment(env={}, env_vars={}, locale="", languages=[]),
        )
        return

    try:
        languages = (
            detect.LanguagesDetect().detect() if cfg.preferred else list(detect.UTF8_LANGUAGES)
        )
        env = detect.UTF8Detect(languages=iter(languages)).detect()
        if env.languages != languages:
            sys.exit(f"utf8-locale internal error: env {env.languages!r} != {languages!r}")
    except (detect.NoLanguagesError, OSError, subprocess.CalledProcessError) as err:
        sys.exit(f"Could not determine an appropriate UTF-8 locale: {err}")

    if isinstance(cfg, RunConfig):
        try:
            os.execvpe(cfg.run_program[0], cfg.run_program, env.env)  # noqa: S606
        except OSError as err:
            sys.exit(f"Could not run '{' '.join(cfg.run_program)}': {err}")

    if isinstance(cfg, QueryConfig):
        QUERY_HANDLERS[cfg.query].handler(cfg, env)
        return

    sys.exit(f"Did not expect to reach the end of main() with {cfg!r}")


if __name__ == "__main__":
    main()
