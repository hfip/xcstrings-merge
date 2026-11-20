# xcstrings-merge

Xcode 15 turned `Localizable.strings` into `.xcstrings`, and any translation that lived in
a `.strings` file (or came back from a translation service as one) is now stranded. Hand
copying dozens of strings into the catalog editor is exactly the kind of work that ends with
a typo in a key.

```
$ xcm merge Localizable.xcstrings ar.lproj/Localizable.strings --lang ar
Localizable.xcstrings · ar
  filled     12
  added       3
  replaced    0
  unchanged  40
  conflicts   2 (existing translations; use --overwrite)
  unknown     1 keys not in the catalog (use --add-new)
  coverage   78%

dry run.
```

## What counts as a change

| situation | what happens |
| --- | --- |
| catalog has no entry for the language | added |
| entry exists, value is empty | filled |
| entry exists with the same text | unchanged |
| entry exists with different text | conflict, reported by key |
| entry uses plural variations | conflict, never flattened |
| key not in the catalog | ignored unless `--add-new` |

Conflicts are the important part. A translator's newer text should not silently overwrite a
reviewed string, so `--overwrite` is opt-in and the keys are listed first.

## Install

```bash
pipx install git+https://github.com/hfip/xcstrings-merge.git
```

Both `xcstrings-merge` and `xcm` are installed.

## Use

```bash
xcm merge Localizable.xcstrings ar.lproj/Localizable.strings --lang ar
xcm merge Localizable.xcstrings ar.strings --lang ar --write
xcm merge Localizable.xcstrings ar.strings --lang ar --write --overwrite
xcm merge Localizable.xcstrings ar.strings --lang ar --write --add-new --sort
xcm merge Localizable.xcstrings ar.strings --lang ar --json
```

Writes a `Localizable.xcstrings.bak` next to the file unless you pass `--no-backup`.

## Details that matter

- `.strings` files exported from older Xcode are often UTF-16; both UTF-16 and UTF-8 are read.
- Escapes (`\n`, `\"`, `\u0645`) are decoded before writing.
- The catalog's JSON is rewritten with `indent=2` and `ensure_ascii=False`, so Arabic stays
  readable in the diff. Key order is preserved unless you pass `--sort`.
- `--json` gives the counts for a CI report.

## What it does not do

- It cannot create plural variations from a single string, so plural entries are reported
  and skipped.
- It does not talk to the App Store or any translation service.
- It does not validate that the translation is correct, only that the JSON stays valid.

## بالعربي

<div dir="rtl" align="right">

إذا عندك ترجمات قديمة في `Localizable.strings` وتبي تنقلها إلى `Localizable.xcstrings`،
النسخ اليدوي يسبب أخطاء في المفاتيح. الأمر يدمج الملفين مع تقرير واضح:

```bash
xcm merge Localizable.xcstrings ar.lproj/Localizable.strings --lang ar --write
```

الترجمات الموجودة ما تنستبدل إلا مع `--overwrite`، والمفاتيح اللي فيها جمع (plural) تظهر
كـ conflict لأنها تحتاج بنية مختلفة.

</div>

## License

MIT. See [LICENSE](LICENSE).
