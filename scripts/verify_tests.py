"""CI cannot silently count missing source integration tests as a pass."""
import sys
import unittest

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover('tests')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.skipped:
        print('Required tests were skipped:', result.skipped, file=sys.stderr)
    sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
