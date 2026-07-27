# Google Spell Check
a Sublime Text package

Package Control: https://packagecontrol.io/packages/Google%20Spell%20Check

## Description
Use Google magic to fix spelling. Select some text (or just put the cursor on a word), run the command, and the text is silently replaced with Google's recommended spelling. If Google has no clear correction, **your text is left alone**.

Google has a far better spell checker than most tools:

1. **Frequency** — Google sees misspellings all day long, so it knows what you probably meant
1. **Names** — company names like `flikr` or `tumblr`, or scifi author `jon sculzi` → `john scalzi`; typical checkers look one word at a time and have no idea
1. **Unlimited dictionary** — `kubernetes`, `hackathons`, `craigslist`
1. **Context** — the whole phrase is considered, not each word alone
1. **It just works** — Sublime's built-in checker has no idea what to do with `avalible`, `finanicals`, `maitenence`

## How to Use
1. Select some text, or put the cursor on a word
1. Run **Google Spell Check**
	* hotkey `ctrl+alt+g`
	* right-click context menu → Google Spell Check
	* Command Palette (`ctrl+shift+p` / `cmd+shift+p`) → Google Spell Check
1. The status bar shows progress, then the correction

Multiple cursors/selections are all checked in one go. Capitalization is preserved (`Avalible` → `Available`, `AVALIBLE` → `AVAILABLE`).

If nothing changes, Google thinks your spelling is fine. Select more words to give it context.

## How It Works
This uses Google's public autocomplete/suggest endpoint (`suggestqueries.google.com`), which returns explicit spell-correction metadata — Google marks *"you typed X, I think you meant Y"*. That flag is what makes silent replacement safe: without it, the plugin doesn't touch your text.

A suggestion is only accepted as a correction when it reads as a respelling — same word count, small per-word edit distance, same first letter. This is what stops Google from "correcting" `receive` into `received`, or `the quick brown fox` into `the quick brown fox jumps over the lazy dog`.

No API key required. It isn't an officially supported API, so Google changing their response format could break the plugin.

## Installation
* **Package Control** (recommended): `Package Control: Install Package` → **Google Spell Check**
* **Manual**: clone into your Sublime `Packages` folder
  ```bash
  git clone https://github.com/noahcoad/google-spell-check.git "Google Spell Check"
  ```

Requires Sublime Text 3 or later (Python 3.3+ plugin host).

## Update Notices
* *2026-07-27*, rewritten for Python 3 / ST4. The old version scraped the Google search results page for "Did you mean" — Google removed that markup, so it silently stopped working. Now uses the suggest endpoint's spell-correction metadata, checks all selections at once, and preserves case. The `st2` and `st3` branches are retired; everything lives on `master`.
* *2013-10-14*, Sublime Text 3 version added.

## Finally
See also: [Open URL](https://github.com/noahcoad/open-url), another Sublime package.

Author: [@noahcoad](http://twitter.com/noahcoad) writes software for the heck of it and to make life just a little more efficient.
