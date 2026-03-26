"""Tests for fuzzy slash command suggestions (typo correction)."""

from hermes_cli.commands import COMMANDS, suggest_similar_commands


# Fixed set of known commands for deterministic tests
KNOWN = {"/help", "/history", "/update", "/background", "/model", "/config",
         "/quit", "/clear", "/new", "/tools", "/toolsets", "/skills",
         "/prompt", "/voice", "/plan", "/reasoning", "/compact", "/skin"}


class TestFuzzySuggestions:
    """suggest_similar_commands() returns close matches for typos."""

    def test_hlep_suggests_help(self):
        result = suggest_similar_commands("/hlep", KNOWN)
        assert "/help" in result

    def test_udpate_suggests_update(self):
        result = suggest_similar_commands("/udpate", KNOWN)
        assert "/update" in result

    def test_bakground_suggests_background(self):
        result = suggest_similar_commands("/bakground", KNOWN)
        assert "/background" in result

    def test_modle_suggests_model(self):
        result = suggest_similar_commands("/modle", KNOWN)
        assert "/model" in result

    def test_confg_suggests_config(self):
        result = suggest_similar_commands("/confg", KNOWN)
        assert "/config" in result

    def test_tolos_suggests_tools(self):
        result = suggest_similar_commands("/tolos", KNOWN)
        assert "/tools" in result

    def test_skils_suggests_skills(self):
        result = suggest_similar_commands("/skils", KNOWN)
        assert "/skills" in result

    def test_completely_unrelated_returns_empty(self):
        """A string with no similarity to any command yields no suggestions."""
        result = suggest_similar_commands("/zzzzxxx", KNOWN)
        assert result == []

    def test_max_three_suggestions(self):
        """At most 3 suggestions are returned by default."""
        result = suggest_similar_commands("/co", KNOWN)
        assert len(result) <= 3

    def test_without_leading_slash(self):
        """Works even when the typed input has no leading slash."""
        result = suggest_similar_commands("hlep", KNOWN)
        assert "/help" in result

    def test_against_real_commands(self):
        """Verify fuzzy matching works against the actual COMMANDS dict."""
        result = suggest_similar_commands("/hlep")
        assert "/help" in result

    def test_exact_match_not_needed(self):
        """An exact command doesn't go through fuzzy — but if it did, it'd match."""
        result = suggest_similar_commands("/help", KNOWN)
        assert "/help" in result
