import unittest
from filter_surge import transform


class FilterTests(unittest.TestCase):
    def setUp(self):
        self.src = (
            '[Rule]\nDOMAIN,iadmusicmat.music.126.net,REJECT\n'
            'DOMAIN-SUFFIX,admusicpic.music.126.net,REJECT\n'
            'DOMAIN,httpdns.music.163.com,REJECT\n'
            '[URL Rewrite]\n'
            r'^https?:\/\/p\.c\.music\.126.net\/.*?jpg$ - reject' + '\n'
            r'^https?:\/\/p\d\.music\.126\.net\/\w+==\/\d+\.jpg$ - reject' + '\n'
            r'^https?:\/\/iadmusicmat\.music.126.net\/.*?jpg$ - reject' + '\n'
            '[Map Local]\n'
            r'^https?:\/\/p[^4](c)?\.music\.126\.net\/\w+==\/10995\d{13}\.jpg$ data-type=tiny-gif status-code=200' + '\n'
            r'^https?:\/\/interface3?\.music\.163\.com/eapi/ad data-type=tiny-gif status-code=200' + '\n'
            '[Script]\nNetEaseCloudMusic_home = type=http-response, pattern=music.163.com, script-path=x.js\n'
            '[MITM]\nhostname = %APPEND% *.music.126.net\n'
        )

    def test_cover_rules_only(self):
        out, removed = transform(self.src)
        self.assertEqual(len(removed), 3)
        self.assertEqual({r['section'] for r in removed}, {'URL Rewrite', 'Map Local'})
        for keep in ('iadmusicmat.music.126.net,REJECT', 'admusicpic.music.126.net,REJECT',
                     'iadmusicmat\\.music.126.net', 'interface3?', 'NetEaseCloudMusic_home',
                     'hostname = %APPEND% *.music.126.net'):
            self.assertIn(keep, out)
        self.assertNotIn('p\\.c\\.music\\.126.net', out)
        self.assertNotIn('p[^4](c)?', out)

    def test_fail_closed(self):
        with self.assertRaises(ValueError):
            transform('[URL Rewrite]\n^https://example.org - reject\n[MITM]\nhostname=example.org\n')


if __name__ == '__main__':
    unittest.main()
