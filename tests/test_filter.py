import unittest
from filter_surge import transform


class FilterTests(unittest.TestCase):
    def test_rewrite_and_domain_rules_only(self):
        src = (
            '#!name=Test\n'
            '[Rule]\n'
            'DOMAIN,ad.music.126.net,REJECT\n'
            'DOMAIN-SUFFIX,music.126.net,REJECT\n'
            'DOMAIN,ad.other.example,REJECT\n'
            'DOMAIN,admusic.126.net,REJECT\n'
            '[URL Rewrite]\n'
            '^https://p\\.music\\.126\\.net/a - reject\n'
            '^https://iadmusicmat.music.126.net/a - reject\n'
            '^https://other.example/a - reject\n'
            '[MITM]\n'
            'hostname = %APPEND% *.music.126.net, other.example\n'
        )
        out, removed = transform(src, r'music\.126')
        self.assertEqual(len(removed), 4)
        self.assertNotIn('DOMAIN,ad.music.126.net,REJECT', out)
        self.assertNotIn('DOMAIN-SUFFIX,music.126.net,REJECT', out)
        self.assertIn('DOMAIN,ad.other.example,REJECT', out)
        self.assertIn('DOMAIN,admusic.126.net,REJECT', out)
        self.assertIn('other.example/a - reject', out)
        self.assertIn('hostname = %APPEND% *.music.126.net, other.example', out)

    def test_fail_closed(self):
        src = '[URL Rewrite]\n^https://example.org - reject\n[MITM]\nhostname=example.org\n'
        with self.assertRaises(ValueError):
            transform(src)

    def test_script_match_fails_closed(self):
        src = ('[URL Rewrite]\n^https://music\\.126/a - reject\n'
               '[Script]\nfoo = type=http-response, pattern=music\\.126, script-path=x.js\n'
               '[MITM]\nhostname=other.example\n')
        with self.assertRaises(ValueError):
            transform(src)


if __name__ == '__main__':
    unittest.main()
