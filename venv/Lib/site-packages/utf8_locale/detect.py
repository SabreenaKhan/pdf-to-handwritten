# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause

"""Implement the actual UTF-8 locale detection."""

from __future__ import annotations

import dataclasses
import os
import re
import subprocess  # noqa: S404
import typing


if typing.TYPE_CHECKING:
    from collections.abc import Iterable


VERSION = "1.0.4"

UTF8_LANGUAGES = ("C", "en", "de", "es", "it")
UTF8_ENCODINGS = ("UTF-8", "utf8")

LOCALE_VARIABLES = (
    "LC_ALL",
    "LANG",
    "LC_MESSAGES",
    "LC_COLLATE",
    "LC_NAME",
    "LC_IDENTIFICATION",
    "LC_CTYPE",
    "LC_NUMERIC",
    "LC_TIME",
    "LC_MONETARY",
    "LC_PAPER",
    "LC_ADDRESS",
    "LC_TELEPHONE",
    "LC_MEASUREMENT",
)

RE_LOCALE_NAME = re.compile(
    r""" ^
    (?P<lang> [a-zA-Z0-9]+ )
    (?:
        _
        (?P<territory> [a-zA-Z0-9]+ )
    )?
    (?:
        \.
        (?P<codeset> [a-zA-Z0-9-]+ )
    )?
    (?:
        @
        (?P<modifier> [a-zA-Z0-9]+ )
    )?
    $ """,
    re.X,
)


class NoLanguagesError(ValueError):
    """No languages were specified to detect from."""

    def __str__(self) -> str:
        """Provide a human-readable representation of the error."""
        return "No languages specified"


@dataclasses.dataclass(frozen=True)
class _DetectState:
    """The state of processing consecutive lines of `locale -a` output."""

    priority: int
    name: str


def detect_utf8_locale(*, languages: Iterable[str] = UTF8_LANGUAGES) -> str:
    """Get a locale name that may hopefully be used for UTF-8 output.

    The `detect_utf8_locale()` function runs the external `locale` command to
    obtain a list of the supported locale names, and then picks a suitable one
    to use so that programs are more likely to output valid UTF-8 characters
    and language-neutral messages. It prefers the `C` base locale, but if
    neither `C.UTF-8` nor `C.utf8` is available, it will fall back to a list of
    other locale names that are likely to be present on the system.

    The `utf8_locale` package has a predefined list of preferred languages.
    If a program has different preferences, e.g. only expecting to parse
    messages written in English, the `detect_utf8_locale()` function may be
    passed a `languages` parameter - an iterable of strings - containing
    the language names in the preferred order. Note that `languages` should
    only contain the language name (e.g. "en") and not a territory name
    (e.g. "en_US"); locale names for the same language and different
    territories are considered equivalent. Thus, the abovementioned program
    that expects to parse messages in English may do:

        name = detect_utf8_locale(languages=["C", "en"])
    """
    weights = {}
    unweight = 0
    for lang in languages:
        if lang not in weights:
            weights[lang] = unweight
            unweight += 1
    if not weights:
        raise NoLanguagesError

    state = _DetectState(unweight, "C")
    for line in subprocess.check_output(  # noqa: S603
        ["env", "LC_ALL=C", "LANGUAGE=", "locale", "-a"],  # noqa: S607
        shell=False,
        encoding="ISO-8859-1",
    ).splitlines():
        data = RE_LOCALE_NAME.match(line)
        if not data:
            continue
        if data.group("codeset") not in UTF8_ENCODINGS:
            continue

        lang = data.group("lang")
        prio = weights.get(lang, weights.get("*", unweight))
        if prio == 0:
            return line
        if prio < state.priority:
            state = _DetectState(prio, line)

    return state.name


def get_utf8_vars(*, languages: Iterable[str] = UTF8_LANGUAGES) -> dict[str, str]:
    """Prepare the environment variables that need to be changed.

    The `get_utf8_vars()` function invokes `detect_utf8_locale()` and then
    returns a dictionary containing the `LC_ALL` variable set to the obtained
    locale name and `LANGUAGE` set to an empty string so that recent versions
    of the gettext library do not choose a different language to output
    messages in.

    The `get_utf8_vars()` function also has an optional `languages` parameter
    that is passed directory to `detect_utf8_locale()`.
    """
    return {"LC_ALL": detect_utf8_locale(languages=languages), "LANGUAGE": ""}


def get_utf8_env(
    env: dict[str, str] | None = None,
    *,
    languages: Iterable[str] = UTF8_LANGUAGES,
) -> dict[str, str]:
    """Prepare the environment to run subprocesses in.

    The `get_utf8_env()` function invokes `detect_utf8_locale()` and then
    returns a dictionary similar to `os.environ`, but with `LC_ALL` set to
    the obtained locale name and `LANGUAGE` set to an empty string so that
    recent versions of the gettext library do not choose a different language
    to output messages in. If a dictionary is passed as the `env` parameter,
    `get_utf8_env()` uses it as a base instead of the value of `os.environ`.

    The `get_utf8_env()` function also has an optional `languages` parameter
    that is passed directory to `detect_utf8_locale()`.
    """
    subenv = dict(os.environ if env is None else env)
    subenv.update(get_utf8_vars(languages=languages))
    return subenv


def get_preferred_languages(
    env: dict[str, str] | None = None,
    *,
    names: Iterable[str] = LOCALE_VARIABLES,
) -> list[str]:
    """Determine preferred languages as per the current locale settings.

    The `get_preferred_languages()` function examines either the current
    process environment or the provided dictionary and returns a list of
    the languages specified in the locale variables (`LC_ALL`, `LANG`,
    `LC_MESSAGES`, etc) in order of preference as defined by either
    the `names` parameter passed or by the `LOCALE_VARIABLES` constant.
    It may be used by programs to add the user's currently preferred locale
    to their own settings, e.g.:

        name = detect_utf8_locale(get_preferred_languages() + ["en"])

    Note that "C" is always appended to the end of the list if it is not
    already present.
    """
    if env is None:
        env = dict(os.environ)

    res = []
    for name in names:
        value = env.get(name)
        if value is None:
            continue
        data = RE_LOCALE_NAME.match(value)
        if data is None:
            continue
        if data.group("codeset") not in UTF8_ENCODINGS:
            continue

        lang = data.group("lang")
        if lang not in res:
            res.append(lang)

    # Make sure "C" is always in the list.
    if "C" not in res:
        res.append("C")
    return res


@dataclasses.dataclass(frozen=True)
class LanguagesDetect:
    """Set up the desired parameters for detecting the preferred languages."""

    env: dict[str, str] | None = None
    names: Iterable[str] | None = None

    def detect(self) -> list[str]:
        """Determine the preferred languages."""
        names = self.names if self.names is not None else LOCALE_VARIABLES
        return get_preferred_languages(self.env, names=names)


@dataclasses.dataclass(frozen=True)
class UTF8Environment:
    """The parameters for a UTF-8-capable environment."""

    env: dict[str, str]
    env_vars: dict[str, str]
    languages: list[str]
    locale: str


@dataclasses.dataclass(frozen=True)
class UTF8Detect:
    """Set up the desired parameters for detecting the UTF-8-capable environment."""

    env: dict[str, str] | None = None
    languages: Iterable[str] | None = None

    def detect(self) -> UTF8Environment:
        """Run the detection, return the results."""
        languages = list(self.languages if self.languages is not None else UTF8_LANGUAGES)
        env = get_utf8_env(self.env, languages=languages)
        return UTF8Environment(
            env=env,
            env_vars={key: env[key] for key in ("LC_ALL", "LANGUAGE")},
            languages=languages,
            locale=env["LC_ALL"],
        )
