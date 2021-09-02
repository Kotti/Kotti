from kotti import get_settings


def test_url_normalizer(config):
    from kotti.url_normalizer import url_normalizer
    assert url_normalizer("simpleandsafe") == "simpleandsafe"
    assert (
        url_normalizer(" Whitespace and capital Letters  ")
        == "whitespace-and-capital-letters"
    )
    assert url_normalizer(">here's another!") == "heres-another"
    assert url_normalizer(">>>here'!--s yet another!!!") == "here-s-yet-another"
    assert url_normalizer("Doe, Joe") == "doe-joe"
    assert url_normalizer("umläut.doc") == "umlaut.doc"
    assert url_normalizer("ZAŻÓŁĆ GĘŚLĄ JAŹŃ") == "zazolc-gesla-jazn"
    assert url_normalizer("zażółć gęślą jaźń") == "zazolc-gesla-jazn"
    assert url_normalizer("quote-this") == "quote-this"
    assert url_normalizer("quote 'this'!") == "quote-this"
    assert url_normalizer("I'm not a FILE.txt") == "im-not-a-file.txt"
    assert url_normalizer("I'm a big file.TXT") == "im-a-big-file.txt"
    assert url_normalizer("rest `n` peace") == "rest-n-peace"
    assert (len(url_normalizer("aa" * 2000))) == 255
    assert url_normalizer("short-hello-version", max_length=10) == "short"


def test_url_normalizer_map_non_ascii_characters(config):
    from kotti.url_normalizer import url_normalizer
    get_settings()["kotti.url_normalizer.map_non_ascii_characters"] = True
    assert url_normalizer("simpleandsafe") == "simpleandsafe"
    assert (
        url_normalizer(" Whitespace and capital Letters  ")
        == "whitespace-and-capital-letters"
    )
    assert url_normalizer(">here's another!") == "heres-another"
    assert url_normalizer(">>>here'!--s yet another!!!") == "here-s-yet-another"
    assert url_normalizer("Doe, Joe") == "doe-joe"
    assert url_normalizer("umläut.doc") == "umlaut.doc"
    assert url_normalizer("ZAŻÓŁĆ GĘŚLĄ JAŹŃ") == "zazolc-gesla-jazn"
    assert url_normalizer("zażółć gęślą jaźń") == "zazolc-gesla-jazn"
    assert url_normalizer("quote-this") == "quote-this"
    assert url_normalizer("quote 'this'!") == "quote-this"
    assert url_normalizer("I'm not a FILE.txt") == "im-not-a-file.txt"
    assert url_normalizer("I'm a big file.TXT") == "im-a-big-file.txt"
    assert url_normalizer("rest `n` peace") == "rest-n-peace"
    assert (len(url_normalizer("aa" * 2000))) == 255
    assert url_normalizer("short-hello-version", max_length=10) == "short"
