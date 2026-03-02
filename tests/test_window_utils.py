"""Tests for the pure-Python _title_matches helper in engine/window_utils.py."""
from __future__ import annotations

import pytest

from macro_thunder.engine.window_utils import _title_matches


# ---------------------------------------------------------------------------
# Contains mode
# ---------------------------------------------------------------------------

def test_contains_mode_match():
    """Contains: substring present in window title (case-insensitive) -> True."""
    assert _title_matches("notepad", "Notepad - Untitled", "Contains") is True


def test_contains_mode_no_match():
    """Contains: substring absent -> False."""
    assert _title_matches("word", "Notepad - Untitled", "Contains") is False


def test_contains_mode_case_insensitive():
    """Contains: query uppercase, title lowercase -> True."""
    assert _title_matches("NOTEPAD", "notepad - untitled", "Contains") is True


# ---------------------------------------------------------------------------
# Exact mode
# ---------------------------------------------------------------------------

def test_exact_mode_match():
    """Exact: full title match (case-insensitive) -> True."""
    assert _title_matches("notepad - untitled", "Notepad - Untitled", "Exact") is True


def test_exact_mode_no_match():
    """Exact: partial title does not match full title -> False."""
    assert _title_matches("notepad", "Notepad - Untitled", "Exact") is False


def test_exact_mode_case_insensitive():
    """Exact: mixed-case query vs mixed-case title -> True."""
    assert _title_matches("NOTEPAD - UNTITLED", "Notepad - Untitled", "Exact") is True


# ---------------------------------------------------------------------------
# Starts With mode
# ---------------------------------------------------------------------------

def test_starts_with_mode_match():
    """Starts With: title begins with query (case-insensitive) -> True."""
    assert _title_matches("notepad", "Notepad - Untitled", "Starts With") is True


def test_starts_with_mode_no_match():
    """Starts With: query is in middle/end, not start -> False."""
    assert _title_matches("untitled", "Notepad - Untitled", "Starts With") is False


def test_starts_with_mode_case_insensitive():
    """Starts With: uppercase query, mixed-case title -> True."""
    assert _title_matches("NOTEPAD", "Notepad - Untitled", "Starts With") is True


# ---------------------------------------------------------------------------
# Empty query edge cases
# ---------------------------------------------------------------------------

def test_empty_title_query_contains_matches_any():
    """Empty title query matches any window title in Contains mode."""
    assert _title_matches("", "Anything Goes Here", "Contains") is True


def test_empty_title_query_exact_matches_empty_title():
    """Empty title query in Exact mode only matches empty titles."""
    assert _title_matches("", "", "Exact") is True


def test_empty_title_query_starts_with_matches_any():
    """Empty query in Starts With mode matches any title (every string starts with empty)."""
    assert _title_matches("", "Anything", "Starts With") is True


# ---------------------------------------------------------------------------
# Unknown mode falls back to Contains behaviour
# ---------------------------------------------------------------------------

def test_unknown_mode_falls_back_to_contains():
    """Unrecognised match_mode falls back to Contains logic."""
    assert _title_matches("note", "Notepad - Untitled", "Fuzzy") is True
