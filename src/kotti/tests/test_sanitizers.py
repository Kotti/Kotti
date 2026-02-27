import pytest

unsanitized = """
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
"""


def _verify_no_html(sanitized):
    assert "<" not in sanitized
    assert "external links" in sanitized


def test_no_html():

    from kotti.sanitizers import no_html

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        _verify_no_html(no_html(unsanitized))


def _verify_minimal_html(sanitized):

    # Tags not in _MINIMAL_TAGS should be stripped (their content preserved)
    assert "<marquee" not in sanitized
    assert "<script" not in sanitized

    # style attribute is NOT in _MINIMAL_ATTRS — style values stripped entirely
    assert 'style=' not in sanitized.lower()

    # <a> links preserved with rel added; target stripped (not in _MINIMAL_ATTRS)
    assert '<a href="http://external.com/"' in sanitized

    # size attribute not in _MINIMAL_ATTRS — stripped
    assert "size" not in sanitized.lower()


def test_minmal_html():

    from kotti.sanitizers import minimal_html_nh3

    _verify_minimal_html(minimal_html_nh3(unsanitized))


def _verify_xss_protection(sanitized):

    # Script tag stripped AND content removed entirely by nh3
    assert "<script>" not in sanitized
    assert "alert('XSS!')" not in sanitized

    assert "<h1>Title</h1>" in sanitized

    # nh3 adds rel="noopener noreferrer" to <a> tags
    assert '<a href="internal.html" target="_blank" rel="noopener noreferrer">internal</a>' in sanitized

    # size attribute is NOT in _XSS_SAFE_ATTRS — stripped from <b>
    assert 'size=' not in sanitized.lower()

    # <b> tag itself IS in _XSS_SAFE_TAGS — preserved
    assert '<b' in sanitized

    # style="color: red" IS preserved (style in wildcard attrs)
    assert 'style="color: red"' in sanitized

    # Unclosed <p> gets closed by nh3
    assert "Unclosed paragraph" in sanitized


def test_xss_protection():

    from kotti.sanitizers import xss_protection_nh3

    _verify_xss_protection(xss_protection_nh3(unsanitized))


def test_default_config(unresolved_settings):

    assert "kotti.sanitizers" in unresolved_settings
    assert "kotti.sanitize_on_write" in unresolved_settings

    assert (
        unresolved_settings["kotti.sanitizers"]
        == "xss_protection:kotti.sanitizers.xss_protection_nh3 minimal_html:kotti.sanitizers.minimal_html_nh3 no_html:kotti.sanitizers.no_html_nh3"
    )  # noqa
    assert (
        unresolved_settings["kotti.sanitize_on_write"]
        == "kotti.resources.Document.body:xss_protection kotti.resources.Content.title:no_html kotti.resources.Content.description:no_html"
    )  # noqa


def test_setup_sanitizers(unresolved_settings):
    from kotti.sanitizers import _setup_sanitizers
    from kotti.sanitizers import minimal_html_nh3
    from kotti.sanitizers import no_html_nh3
    from kotti.sanitizers import xss_protection_nh3

    _setup_sanitizers(unresolved_settings)

    settings = unresolved_settings["kotti.sanitizers"]

    assert "minimal_html" in settings
    assert "no_html" in settings
    assert "xss_protection" in settings

    assert settings["minimal_html"] == minimal_html_nh3
    assert settings["no_html"] == no_html_nh3
    assert settings["xss_protection"] == xss_protection_nh3


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_listeners(app, root, db_session):

    from kotti.resources import Document

    root["d"] = doc = Document(
        name="test", title="<h1>Title</h1>", description=unsanitized, body=unsanitized
    )

    db_session.flush()

    assert doc.title == "Title"
    _verify_no_html(doc.description)
    _verify_xss_protection(doc.body)

    # Test None title
    root["e"] = doc = Document(
        name="test", title=None, description=unsanitized, body=unsanitized
    )
    db_session.flush()
    assert doc.title == None


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_sanitize(app, dummy_request):

    from kotti.sanitizers import sanitize
    from kotti.resources import Document
    from kotti.views.util import TemplateAPI

    _verify_no_html(sanitize(unsanitized, "no_html"))
    _verify_minimal_html(sanitize(unsanitized, "minimal_html"))
    _verify_xss_protection(sanitize(unsanitized, "xss_protection"))

    api = TemplateAPI(Document(), dummy_request)
    _verify_no_html(api.sanitize(unsanitized, "no_html"))
    _verify_minimal_html(api.sanitize(unsanitized, "minimal_html"))
    _verify_xss_protection(api.sanitize(unsanitized, "xss_protection"))


def test_deprecation_warnings():
    import warnings
    from kotti.sanitizers import xss_protection, minimal_html, no_html

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        xss_protection("<p>test</p>")
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "xss_protection_nh3" in str(w[0].message)
        assert "Kotti 3.0" in str(w[0].message)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        minimal_html("<p>test</p>")
        assert len(w) == 1
        assert "minimal_html_nh3" in str(w[0].message)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        no_html("<p>test</p>")
        assert len(w) == 1
        assert "no_html_nh3" in str(w[0].message)


# ---------------------------------------------------------------------------
# nh3 characterization tests — updated from bleach baseline (Plan 02-01)
# These tests document EXACT nh3 behavior. The bleach characterization tests
# have been replaced by these after the nh3 migration in Plan 02-02.
# ---------------------------------------------------------------------------


def test_nh3_characterization_xss_protection():
    """Capture exact nh3 xss_protection_nh3() behavior as regression baseline."""
    from kotti.sanitizers import xss_protection_nh3

    sanitized = xss_protection_nh3(unsanitized)

    # Script tags: nh3 strips <script> tags AND REMOVES content (unlike bleach)
    assert "alert('XSS!')" not in sanitized
    assert "<script>" not in sanitized

    # Attribute handling: nh3 uses explicit allowlist — size NOT allowed on <b>
    assert 'size=' not in sanitized.lower()

    # Style preservation: style is in wildcard attrs — preserved (no trailing semicolon)
    assert 'style="color: red"' in sanitized

    # Link handling: nh3 adds rel="noopener noreferrer" to <a> tags
    assert 'target="_blank"' in sanitized
    assert 'rel="noopener noreferrer"' in sanitized

    # Tag handling: <marquee> IS in _XSS_SAFE_TAGS, so it is preserved
    assert "<marquee>" in sanitized


def test_nh3_characterization_minimal_html():
    """Capture exact nh3 minimal_html_nh3() behavior as regression baseline."""
    from kotti.sanitizers import minimal_html_nh3

    sanitized = minimal_html_nh3(unsanitized)

    # Style handling: nh3 with no style in attrs — NO style attribute at all
    assert 'style=' not in sanitized.lower()

    # Attribute stripping: size on <b> is NOT in _MINIMAL_ATTRS
    assert "size" not in sanitized.lower()

    # <a> links preserved with rel added
    assert 'rel="noopener noreferrer"' in sanitized


def test_nh3_characterization_no_html():
    """Capture exact nh3 no_html_nh3() behavior as regression baseline."""
    from kotti.sanitizers import no_html_nh3

    sanitized = no_html_nh3(unsanitized)

    # All tags removed, text content preserved
    assert "<" not in sanitized
    assert "external links" in sanitized
