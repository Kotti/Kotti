# encoding=utf-8
from kotti.testing import UnitTestBase
from kotti import get_settings
from kotti.url_normalizer import url_normalizer


class URLNormalizerTests(UnitTestBase):

    def test_normalizer(self):
        self.assertEquals(url_normalizer(unicode('simpleandsafe', 'utf-8')), unicode('simpleandsafe', 'utf-8'))
        self.assertEquals(url_normalizer(unicode(' Whitespace and capital Letters  ', 'utf-8')), unicode('whitespace-and-capital-letters', 'utf-8'))
        self.assertEquals(url_normalizer(unicode(">here's another!", 'utf-8')), unicode('heres-another', 'utf-8'))
        self.assertEquals(url_normalizer(unicode(">>>here'!--s yet another!!!", 'utf-8')), unicode("here-s-yet-another", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("Doe, Joe", 'utf-8')), unicode("doe-joe", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("umläut.doc", 'utf-8')), unicode("umläut.doc", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("ZAŻÓŁĆ GĘŚLĄ JAŹŃ", 'utf-8')), unicode("zażółć-gęślą-jaźń", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("zażółć gęślą jaźń", 'utf-8')), unicode("zażółć-gęślą-jaźń", 'utf-8'))
        self.assertEquals(url_normalizer(unicode('quote-this', 'utf-8')), unicode('quote-this', 'utf-8'))
        self.assertEquals(url_normalizer(unicode("quote 'this'!", 'utf-8')), unicode("quote-this", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("I'm not a FILE.txt", 'utf-8')), unicode("im-not-a-file.txt", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("I'm a big file.TXT", 'utf-8')), unicode("im-a-big-file.txt", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("rest `n` peace", 'utf-8')), unicode("rest-n-peace", 'utf-8'))
        self.assertEquals(len(url_normalizer(unicode("aa", 'utf-8') * 2000)), 255)
        self.assertEquals(url_normalizer(unicode("short-hello-version", 'utf-8'), max_length=10), unicode("short", 'utf-8'))


    def test_normalizer_map_non_ascii_characters(self):
        get_settings()['kotti.url_normalizer.map_non_ascii_characters'] = True
        self.assertEquals(url_normalizer(unicode('simpleandsafe', 'utf-8')), unicode('simpleandsafe', 'utf-8'))
        self.assertEquals(url_normalizer(unicode(' Whitespace and capital Letters  ', 'utf-8')), unicode('whitespace-and-capital-letters', 'utf-8'))
        self.assertEquals(url_normalizer(unicode(">here's another!", 'utf-8')), unicode('heres-another', 'utf-8'))
        self.assertEquals(url_normalizer(unicode(">>>here'!--s yet another!!!", 'utf-8')), unicode("here-s-yet-another", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("Doe, Joe", 'utf-8')), unicode("doe-joe", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("umläut.doc", 'utf-8')), unicode("umlaut.doc", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("ZAŻÓŁĆ GĘŚLĄ JAŹŃ", 'utf-8')), unicode("zazolc-gesla-jazn", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("zażółć gęślą jaźń", 'utf-8')), unicode("zazolc-gesla-jazn", 'utf-8'))
        self.assertEquals(url_normalizer(unicode('quote-this', 'utf-8')), unicode('quote-this', 'utf-8'))
        self.assertEquals(url_normalizer(unicode("quote 'this'!", 'utf-8')), unicode("quote-this", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("I'm not a FILE.txt", 'utf-8')), unicode("im-not-a-file.txt", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("I'm a big file.TXT", 'utf-8')), unicode("im-a-big-file.txt", 'utf-8'))
        self.assertEquals(url_normalizer(unicode("rest `n` peace", 'utf-8')), unicode("rest-n-peace", 'utf-8'))
        self.assertEquals(len(url_normalizer(unicode("aa", 'utf-8') * 2000)), 255)
        self.assertEquals(url_normalizer(unicode("short-hello-version", 'utf-8'), max_length=10), unicode("short", 'utf-8'))
