# encoding=utf-8
from kotti import get_settings
from kotti.url_normalizer import url_normalizer


class URLNormalizerTests:

    def test_normalizer(self):
        assert url_normalizer(u'simpleandsafe') == u'simpleandsafe'
        assert url_normalizer(u' Whitespace and capital Letters  ') == \
            u'whitespace-and-capital-letters'
        assert url_normalizer(u">here's another!") == u'heres-another'
        assert url_normalizer(u">>>here'!--s yet another!!!") == \
            u"here-s-yet-another"
        assert url_normalizer(u"Doe, Joe") == u"doe-joe"
        assert url_normalizer(u"umläut.doc") == u"umläut.doc"
        assert url_normalizer(u"ZAŻÓŁĆ GĘŚLĄ JAŹŃ") == u"zażółć-gęślą-jaźń"
        assert url_normalizer(u"zażółć gęślą jaźń") == u"zażółć-gęślą-jaźń"
        assert url_normalizer(u'quote-this') == u'quote-this'
        assert url_normalizer(u"quote 'this'!") == u"quote-this"
        assert url_normalizer(u"I'm not a FILE.txt") == u"im-not-a-file.txt"
        assert url_normalizer(u"I'm a big file.TXT") == u"im-a-big-file.txt"
        assert url_normalizer(u"rest `n` peace") == u"rest-n-peace"
        assert (len(url_normalizer(u"aa" * 2000))) == 255
        assert url_normalizer(u"short-hello-version", max_length=10) == u"short"

    def test_normalizer_map_non_ascii_characters(self):
        get_settings()['kotti.url_normalizer.map_non_ascii_characters'] = True
        assert url_normalizer(u'simpleandsafe') == u'simpleandsafe'
        assert url_normalizer(u' Whitespace and capital Letters  ') == \
            u'whitespace-and-capital-letters'
        assert url_normalizer(u">here's another!") == u'heres-another'
        assert url_normalizer(u">>>here'!--s yet another!!!") == \
            u"here-s-yet-another"
        assert url_normalizer(u"Doe, Joe") == u"doe-joe"
        assert url_normalizer(u"umläut.doc") == u"umlaut.doc"
        assert url_normalizer(u"ZAŻÓŁĆ GĘŚLĄ JAŹŃ") == u"zazolc-gesla-jazn"
        assert url_normalizer(u"zażółć gęślą jaźń") == u"zazolc-gesla-jazn"
        assert url_normalizer(u'quote-this') == u'quote-this'
        assert url_normalizer(u"quote 'this'!") == u"quote-this"
        assert url_normalizer(u"I'm not a FILE.txt") == u"im-not-a-file.txt"
        assert url_normalizer(u"I'm a big file.TXT") == u"im-a-big-file.txt"
        assert url_normalizer(u"rest `n` peace") == u"rest-n-peace"
        assert (len(url_normalizer(u"aa" * 2000))) == 255
        assert url_normalizer(u"short-hello-version", max_length=10) == u"short"
