# Live tests against Google's suggest endpoint -- needs a network connection.
#   python3 tests/test_correct.py
# Stubs the sublime modules so the plugin imports outside the editor.

import os, sys, time, types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_sublime = types.ModuleType('sublime')
_sublime.status_message = lambda *a: None
_sublime.set_timeout = lambda *a: None
class _Region:
	def __init__(self, a, b=None): self.a, self.b = a, b
_sublime.Region = _Region
sys.modules['sublime'] = _sublime

_plugin = types.ModuleType('sublime_plugin')
class _TextCommand:
	def __init__(self, *a): pass
_plugin.TextCommand = _TextCommand
sys.modules['sublime_plugin'] = _plugin

import GoogleSpellCheck as gsc

THROTTLE = 0.8		# the suggest endpoint returns 500s under rapid-fire use

# misspellings -> the correction we expect, or None for "any correction will do"
MISSPELLED = [
	('avalible', 'available'),
	('maitenence', 'maintenance'),
	('recieve', 'receive'),
	('seperate', 'separate'),
	('definately', 'definitely'),
	('occurance', 'occurrence'),
	('tommorrow', 'tomorrow'),
	('wierd', 'weird'),
	('accomodate', 'accommodate'),
	('concious', 'conscious'),
	('goverment', 'government'),
	('embarass', 'embarrass'),
	('flikr', 'flickr'),
	('craigslsit', 'craigslist'),
	('kubernets', 'kubernetes'),
	('jon sculzi', 'john scalzi'),			# names, via phrase context
	('pyton scrpit', 'python script'),
	('sublme text', 'sublime text'),
	('battery terminalss', 'battery terminals'),	# doubled trailing letter
	# google only offers extensions for the whole phrase, so this needs the
	# per-word pass; "additionassl" corrects fine on its own
	('additionassl microcontrollers', 'additional microcontrollers'),
	('recieve the pakcage', 'receive the package'),	# two bad words in one phrase
]

# correctly spelled -- must be left completely alone
CORRECT = [
	'definitely',
	'receive',				# google suggests "received"; must not be applied
	'maintenance',
	'available',
	'separate',
	'tomorrow',
	'weird',
	'asynchronous',
	'kubernetes',
	'python',
	'avocado',
	'the quick brown fox',	# must not be extended to "...jumps over the lazy dog"
	'hello world',
	'battery terminals',
	'John Scalzi',
	'Sublime Text',
	'git rebase',
	'spell check',
	# the per-word pass must not "fix" words that are already right
	'additional microcontrollers',
	'the microcontroller reads the sensor',
	'sublime text package control',
	'wire the terminals to the battery',
]

# (input, expected) pairs that don't need the network
OFFLINE = [
	('', None),
	('   ', None),
	('123', None),
	('!!!', None),
	('x' * 500, None),
]


def main():
	fails = []

	for text, expected in OFFLINE:
		got = gsc.correct(text)
		if got is not None:
			fails.append('offline %r -> %r, wanted None' % (text[:20], got))

	print('checking %d misspellings' % len(MISSPELLED))
	for text, expected in MISSPELLED:
		got = gsc.correct(text)
		time.sleep(THROTTLE)
		ok = got is not None and (expected is None or got.lower() == expected.lower())
		print('  %s %-20r -> %r' % ('ok  ' if ok else 'FAIL', text, got))
		if not ok:
			fails.append('%r -> %r, wanted %r' % (text, got, expected))

	print('checking %d correctly spelled' % len(CORRECT))
	for text in CORRECT:
		got = gsc.correct(text)
		time.sleep(THROTTLE)
		ok = got is None
		print('  %s %-20r -> %r' % ('ok  ' if ok else 'FAIL', text, got))
		if not ok:
			fails.append('%r changed to %r, wanted no change' % (text, got))

	# capitalization is carried over from what was typed
	for text, expected in [('Avalible', 'Available'), ('AVALIBLE', 'AVAILABLE')]:
		got = gsc.correct(text)
		time.sleep(THROTTLE)
		if got != expected:
			fails.append('case %r -> %r, wanted %r' % (text, got, expected))

	total = len(OFFLINE) + len(MISSPELLED) + len(CORRECT) + 2
	if fails:
		print('\n%d of %d failed:' % (len(fails), total))
		for f in fails: print('  ' + f)
		return 1
	print('\nall %d passed' % total)
	return 0


if __name__ == '__main__':
	sys.exit(main())
