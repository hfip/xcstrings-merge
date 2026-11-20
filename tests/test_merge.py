import json

from xcstrings_merge.catalog import merge, write_catalog
from xcstrings_merge.strings import decode, parse_strings, unescape
from xcstrings_merge.cli import main


def unit(value, state="translated"):
    return {"stringUnit": {"state": state, "value": value}}


def catalog_payload():
    return {
        "sourceLanguage": "en",
        "version": "1.0",
        "strings": {
            "Welcome": {"localizations": {"en": unit("Welcome"), "ar": unit("أهلاً")}},
            "Follow": {"localizations": {"en": unit("Follow"), "ar": unit("")}},
            "Share": {"localizations": {"en": unit("Share")}},
            "Review": {
                "localizations": {"en": unit("Review"), "ar": unit("مراجعة", "needs_review")}
            },
            "Items": {
                "localizations": {
                    "en": {
                        "variations": {
                            "plural": {"one": unit("%lld item"), "other": unit("%lld items")}
                        }
                    }
                }
            },
        },
    }


# --- .strings parsing ------------------------------------------------------


def test_parse_basic_pairs():
    assert parse_strings('"A" = "B";\n') == {"A": "B"}


def test_parse_skips_comments():
    text = '/* header */\n// note\n"A" = "B";\n'
    assert parse_strings(text) == {"A": "B"}


def test_parse_unescapes_values():
    assert parse_strings(r'"A" = "line\nbreak \"quoted\"";')["A"] == 'line\nbreak "quoted"'


def test_parse_unicode_escape():
    assert unescape(r"\u0645") == "م"


def test_decode_utf16():
    assert decode('"A" = "مرحبا";'.encode("utf-16")) == '"A" = "مرحبا";'


# --- merging ---------------------------------------------------------------


def test_merge_fills_empty_translation():
    payload = catalog_payload()
    report = merge(payload, {"Follow": "متابعة"}, "ar")
    assert report.filled == 1
    assert payload["strings"]["Follow"]["localizations"]["ar"]["stringUnit"]["value"] == "متابعة"


def test_merge_adds_missing_language():
    payload = catalog_payload()
    report = merge(payload, {"Share": "مشاركة"}, "ar")
    assert report.added == 1
    assert "ar" in payload["strings"]["Share"]["localizations"]


def test_merge_keeps_existing_and_reports_conflict():
    payload = catalog_payload()
    report = merge(payload, {"Welcome": "مرحبا"}, "ar")
    assert report.conflicts == ["Welcome"]
    assert payload["strings"]["Welcome"]["localizations"]["ar"]["stringUnit"]["value"] == "أهلاً"


def test_merge_overwrite_replaces_needs_review():
    payload = catalog_payload()
    report = merge(payload, {"Review": "مراجعة نهائية"}, "ar", overwrite=True)
    assert report.replaced == 1
    assert (
        payload["strings"]["Review"]["localizations"]["ar"]["stringUnit"]["value"]
        == "مراجعة نهائية"
    )


def test_merge_ignores_plural_entries():
    payload = catalog_payload()
    report = merge(payload, {"Items": "عناصر"}, "ar")
    assert report.conflicts == ["Items"]
    assert "ar" not in payload["strings"]["Items"]["localizations"]


def test_merge_unknown_key_is_reported():
    payload = catalog_payload()
    report = merge(payload, {"Ghost": "شبح"}, "ar")
    assert report.unknown_keys == ["Ghost"]


def test_merge_add_new_inserts_entry():
    payload = catalog_payload()
    report = merge(payload, {"Ghost": "شبح"}, "ar", add_new=True)
    assert report.added_keys == ["Ghost"]
    assert payload["strings"]["Ghost"]["localizations"]["ar"]["stringUnit"]["value"] == "شبح"


def test_merge_ignores_empty_values():
    payload = catalog_payload()
    report = merge(payload, {"Follow": "   "}, "ar")
    assert report.filled == 0


def test_coverage_is_recomputed():
    payload = catalog_payload()
    before = merge(payload, {}, "ar").coverage
    after = merge(payload, {"Follow": "متابعة", "Share": "مشاركة"}, "ar").coverage
    assert after > before


# --- writing ---------------------------------------------------------------


def test_write_preserves_arabic(tmp_path):
    path = tmp_path / "Localizable.xcstrings"
    payload = catalog_payload()
    write_catalog(payload, path)
    raw = path.read_text(encoding="utf-8")
    assert "أهلاً" in raw


def test_write_sorts_when_asked(tmp_path):
    path = tmp_path / "c.xcstrings"
    write_catalog(catalog_payload(), path, sort_keys=True)
    keys = list(json.loads(path.read_text(encoding="utf-8"))["strings"])
    assert keys == sorted(keys)


# --- CLI -------------------------------------------------------------------


def setup(tmp_path):
    catalog = tmp_path / "Localizable.xcstrings"
    catalog.write_text(json.dumps(catalog_payload(), ensure_ascii=False), encoding="utf-8")
    strings = tmp_path / "ar.strings"
    strings.write_text('"Follow" = "متابعة";\n"Share" = "مشاركة";\n', encoding="utf-8")
    return catalog, strings


def test_cli_dry_run_does_not_write(tmp_path, capsys):
    catalog, strings = setup(tmp_path)
    before = catalog.read_text(encoding="utf-8")
    assert main(["merge", str(catalog), str(strings), "--lang", "ar"]) == 0
    assert catalog.read_text(encoding="utf-8") == before
    assert "dry run" in capsys.readouterr().out


def test_cli_write_updates_catalog(tmp_path):
    catalog, strings = setup(tmp_path)
    assert main(["merge", str(catalog), str(strings), "--lang", "ar", "--write"]) == 0
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    assert payload["strings"]["Follow"]["localizations"]["ar"]["stringUnit"]["value"] == "متابعة"


def test_cli_write_creates_backup(tmp_path):
    catalog, strings = setup(tmp_path)
    main(["merge", str(catalog), str(strings), "--lang", "ar", "--write"])
    assert (tmp_path / "Localizable.xcstrings.bak").exists()


def test_cli_json(tmp_path, capsys):
    catalog, strings = setup(tmp_path)
    assert main(["merge", str(catalog), str(strings), "--lang", "ar", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["filled"] == 1
    assert payload["added"] == 1


def test_cli_missing_catalog_exits_two(tmp_path):
    assert main(["merge", str(tmp_path / "nope.xcstrings"), "x.strings", "--lang", "ar"]) == 2


def test_cli_without_command_returns_two():
    assert main([]) == 2
