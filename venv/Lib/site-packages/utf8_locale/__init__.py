# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause

"""Detect a UTF-8-capable locale for running child processes in.

Sometimes it is useful for a program to be able to run a child process and
more or less depend on its output being valid UTF-8. This can usually be
accomplished by setting one or more environment variables, but there is
the question of what to set them to - what UTF-8-capable locale is present
on this particular system? This is where the `utf8_locale` module comes in.
"""

from .detect import (  # isort: skip
    VERSION,
    UTF8_LANGUAGES,
    UTF8_ENCODINGS,
    LOCALE_VARIABLES,
    LanguagesDetect,
    NoLanguagesError,
    UTF8Detect,
    UTF8Environment,
    detect_utf8_locale,
    get_preferred_languages,
    get_utf8_env,
    get_utf8_vars,
)

__all__ = [
    "LOCALE_VARIABLES",
    "UTF8_ENCODINGS",
    "UTF8_LANGUAGES",
    "VERSION",
    "LanguagesDetect",
    "NoLanguagesError",
    "UTF8Detect",
    "UTF8Environment",
    "detect_utf8_locale",
    "get_preferred_languages",
    "get_utf8_env",
    "get_utf8_vars",
]
