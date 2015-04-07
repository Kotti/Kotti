# -*- coding: utf-8 -*-

unsanitized = u'''
<h1>Title</h1>
<div class="teaser umlaut">Descrüptiön</div>
<p>
  Paragraph with
  <a href="internal.html" target="_blank">internal</a> and
  <a href="http://external.com/" target="_blank">external</a> links.
</p>
<marquee>Fancy marquee!</marquee>
<b SIZE=17 style="color: red">IMPORTANT!</b>
<script>
  alert('XSS!')
</script>
<p>Unclosed paragraph
'''


def _verify_no_html(sanitized):
    assert u'<' not in sanitized
    assert u'external links' in sanitized


def test_no_html():

    from kotti.sanitizers import no_html

    _verify_no_html(no_html(unsanitized))


def _verify_minimal_html(sanitized):

    from bleach_whitelist import all_tags
    from bleach_whitelist import markdown_tags
    from bleach_whitelist import print_tags

    for tag in set(all_tags) - set(markdown_tags) - set(print_tags):
        assert u'<{0}'.format(tag) not in sanitized

    assert u'style=""' in sanitized
    assert u'<a href="http://external.com/">' in sanitized
    assert u'size' not in sanitized.lower()


def test_minmal_html():

    from kotti.sanitizers import minimal_html

    _verify_minimal_html(minimal_html(unsanitized))


def _verify_xss_protection(sanitized):

    assert u'<script>' not in sanitized
    assert u'<h1>Title</h1>' in sanitized
    assert u'<a href="internal.html" target="_blank">internal</a>' in sanitized
    assert u'b size="17"' in sanitized
    assert u'<p>Unclosed paragraph\n</p>' in sanitized


def test_xss_protection():

    from kotti.sanitizers import xss_protection

    _verify_xss_protection(xss_protection(unsanitized))


def test_default_config(unresolved_settings):

    assert u'kotti.sanitizers' in unresolved_settings
    assert u'kotti.sanitize_on_write' in unresolved_settings

    assert unresolved_settings[u'kotti.sanitizers'] == u'xss_protection:kotti.sanitizers.xss_protection minimal_html:kotti.sanitizers.minimal_html no_html:kotti.sanitizers.no_html'  # noqa
    assert unresolved_settings[u'kotti.sanitize_on_write'] == u'kotti.resources.Document.body:xss_protection kotti.resources.Content.title:no_html kotti.resources.Content.description:no_html'  # noqa


def test_setup_sanitizers(unresolved_settings):
    from kotti.sanitizers import _setup_sanitizers
    from kotti.sanitizers import minimal_html
    from kotti.sanitizers import no_html
    from kotti.sanitizers import xss_protection

    _setup_sanitizers(unresolved_settings)

    settings = unresolved_settings[u'kotti.sanitizers']

    assert u'minimal_html' in settings
    assert u'no_html' in settings
    assert u'xss_protection' in settings

    assert settings[u'minimal_html'] == minimal_html
    assert settings[u'no_html'] == no_html
    assert settings[u'xss_protection'] == xss_protection


def test_listeners(app, root, db_session):

    from kotti.resources import Document

    root[u'd'] = doc = Document(
        name=u'test',
        title=u'<h1>Title</h1>',
        description=unsanitized,
        body=unsanitized)

    db_session.flush()

    assert doc.title == u'Title'
    _verify_no_html(doc.description)
    _verify_xss_protection(doc.body)


def test_sanitize(app, dummy_request):

    from kotti.sanitizers import sanitize
    from kotti.resources import Document
    from kotti.views.util import TemplateAPI

    _verify_no_html(sanitize(unsanitized, 'no_html'))
    _verify_minimal_html(sanitize(unsanitized, 'minimal_html'))
    _verify_xss_protection(sanitize(unsanitized, 'xss_protection'))

    api = TemplateAPI(Document(), dummy_request)
    _verify_no_html(api.sanitize(unsanitized, 'no_html'))
    _verify_minimal_html(api.sanitize(unsanitized, 'minimal_html'))
    _verify_xss_protection(api.sanitize(unsanitized, 'xss_protection'))
