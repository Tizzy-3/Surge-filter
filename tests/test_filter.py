import unittest
from filter_surge import transform

class FilterTests(unittest.TestCase):
    def test_only_rewrite_removed(self):
        src = ('#!name=Test\n[Rule]\nDOMAIN,ad.music.126.net,REJECT\n'
               '[URL Rewrite]\n^https://p\\.music\\.126\\.net/a - reject\n'
               '^https://other.example/a - reject\n'
               '[MITM]\nhostname = %APPEND% *.music.126.net, other.example\n')
        out, removed = transform(src, r'music\.126')
        self.assertEqual(len(removed), 1)
        self.assertIn('DOMAIN,ad.music.126.net,REJECT', out)
        self.assertIn('hostname = %APPEND% *.music.126.net, other.example', out)
        self.assertIn('other.example/a - reject', out)
        self.assertNotIn('p\\.music\\.126\\.net/a', out)

    def test_fail_closed(self):
        src = '[URL Rewrite]\n^https://example.org - reject\n[MITM]\nhostname=example.org\n'
        with self.assertRaises(ValueError):
            transform(src, r'music\.126')

if __name__ == '__main__':
    unittest.main()
