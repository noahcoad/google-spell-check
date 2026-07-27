# Replaces the word under the cursor or selection with Google's recommended spelling.
# Silent: if Google has no clear respelling, the text is left alone.
# Hosted at http://github.com/noahcoad/google-spell-check

import sublime, sublime_plugin
import urllib.request, urllib.parse, json, re, html, threading

SUGGEST_URL = 'https://suggestqueries.google.com/complete/search'
# psy-ab is the only client that returns explicit spell-correction metadata:
# za = "<sc>corrected</sc>", zb = "<se>what you typed</se>"
CLIENT = 'psy-ab'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36'
TIMEOUT = 8
MAX_CHARS = 200


def _detag(s):
	return html.unescape(re.sub(r'<.*?>', '', s or '')).strip()


def _fetch(text):
	url = '%s?client=%s&hl=en&gl=us&q=%s' % (SUGGEST_URL, CLIENT, urllib.parse.quote(text))
	req = urllib.request.Request(url, headers={'User-Agent': UA})
	with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
		return json.loads(resp.read().decode('utf-8', 'replace'))


def _lev(a, b):
	prev = list(range(len(b) + 1))
	for i, ca in enumerate(a, 1):
		cur = [i]
		for j, cb in enumerate(b, 1):
			cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
		prev = cur
	return prev[-1]


def _plausible(src, cand):
	# a respelling keeps the same word count and stays close per word;
	# anything else is google extending the phrase, not correcting it
	sw, cw = src.split(), cand.split()
	if len(sw) != len(cw): return False
	if cand.startswith(src) or src.startswith(cand): return False
	if _lev(src, cand) > max(2, len(src) // 4): return False
	for a, b in zip(sw, cw):
		if a == b: continue
		if _lev(a, b) > max(2, len(a) // 3): return False
		if a[0] != b[0]: return False
	return True


def _match_case(src, fix):
	if src.isupper(): return fix.upper()
	if src.istitle(): return fix.title()
	if src[:1].isupper(): return fix[:1].upper() + fix[1:]
	return fix


def correct(text):
	"""Google's respelling of text, or None if google has no clear correction."""
	src = text.strip()
	if not src or len(src) > MAX_CHARS: return None
	if not re.search(r'[a-zA-Z]', src): return None

	data = _fetch(src)
	rows = data[1] if len(data) > 1 else []
	low = src.lower()
	nwords = len(low.split())

	# google explicitly flagged a misspelling
	for row in rows:
		meta = row[3] if len(row) > 3 and isinstance(row[3], dict) else {}
		za, zb = meta.get('za'), meta.get('zb')
		if not (za and zb): continue
		if _detag(zb).lower() != low: continue
		cand = _detag(za)
		if cand.lower() != low and len(cand.split()) == nwords:
			return _match_case(src, cand)

	# no explicit flag: accept a top suggestion only if it reads as a respelling
	for row in rows[:5]:
		cand = _detag(row[0])
		cl = cand.lower()
		if cl == low: return None		# google agrees with the spelling
		if _plausible(low, cl): return _match_case(src, cand)

	return None


class GoogleSpellCheckCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		regions = []
		for sel in self.view.sel():
			r = sel if not sel.empty() else self.view.word(sel)
			if not self.view.substr(r).strip(): continue
			regions.append((r.a, r.b))
		if not regions:
			sublime.status_message('Google Spell Check: nothing to check')
			return

		self.view.set_status('google_spell_check', 'Google Spell Check: checking...')
		threading.Thread(target=self._work, args=(regions,), daemon=True).start()

	def _work(self, regions):
		fixes = []
		errors = 0
		for a, b in regions:
			text = self.view.substr(sublime.Region(a, b))
			try:
				fix = correct(text)
			except Exception:
				errors += 1
				continue
			if not fix: continue
			lead = text[:len(text) - len(text.lstrip())]		# keep any selected whitespace
			trail = text[len(text.rstrip()):]
			fix = lead + fix + trail
			if fix != text:
				fixes.append({'region': [a, b], 'text': fix})
		sublime.set_timeout(lambda: self._done(fixes, errors, len(regions)), 0)

	def _done(self, fixes, errors, total):
		self.view.erase_status('google_spell_check')
		if errors:
			sublime.status_message('Google Spell Check: could not reach Google (check your connection)')
			if not fixes: return
		if not fixes:
			sublime.status_message('Google Spell Check: spelling looks good')
			return
		self.view.run_command('google_spell_check_replace', {'fixes': fixes})
		if len(fixes) == 1:
			sublime.status_message('Google Spell Check: %s' % fixes[0]['text'])
		else:
			sublime.status_message('Google Spell Check: corrected %d of %d' % (len(fixes), total))


class GoogleSpellCheckReplaceCommand(sublime_plugin.TextCommand):
	def run(self, edit, fixes):
		# back to front so earlier replacements don't shift later regions
		for f in sorted(fixes, key=lambda x: x['region'][0], reverse=True):
			self.view.replace(edit, sublime.Region(*f['region']), f['text'])
