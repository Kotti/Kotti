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

    _verify_no_html(no_html(unsanitized))


def _verify_minimal_html(sanitized):

    from bleach_allowlist import all_tags
    from bleach_allowlist import markdown_tags
    from bleach_allowlist import print_tags

    for tag in set(all_tags) - set(markdown_tags) - set(print_tags):
        assert f"<{tag}" not in sanitized

    assert 'style=""' in sanitized
    assert '<a href="http://external.com/">' in sanitized
    assert "size" not in sanitized.lower()


def test_minmal_html():

    from kotti.sanitizers import minimal_html

    _verify_minimal_html(minimal_html(unsanitized))


def _verify_xss_protection(sanitized):

    assert "<script>" not in sanitized
    assert "<h1>Title</h1>" in sanitized
    assert '<a href="internal.html" target="_blank">internal</a>' in sanitized
    assert 'b size="17"' in sanitized
    assert "<p>Unclosed paragraph\n</p>" in sanitized


def test_xss_protection():

    from kotti.sanitizers import xss_protection

    _verify_xss_protection(xss_protection(unsanitized))


def test_default_config(unresolved_settings):

    assert "kotti.sanitizers" in unresolved_settings
    assert "kotti.sanitize_on_write" in unresolved_settings

    assert (
        unresolved_settings["kotti.sanitizers"]
        == "xss_protection:kotti.sanitizers.xss_protection minimal_html:kotti.sanitizers.minimal_html no_html:kotti.sanitizers.no_html"
    )  # noqa
    assert (
        unresolved_settings["kotti.sanitize_on_write"]
        == "kotti.resources.Document.body:xss_protection kotti.resources.Content.title:no_html kotti.resources.Content.description:no_html"
    )  # noqa


def test_setup_sanitizers(unresolved_settings):
    from kotti.sanitizers import _setup_sanitizers
    from kotti.sanitizers import minimal_html
    from kotti.sanitizers import no_html
    from kotti.sanitizers import xss_protection

    _setup_sanitizers(unresolved_settings)

    settings = unresolved_settings["kotti.sanitizers"]

    assert "minimal_html" in settings
    assert "no_html" in settings
    assert "xss_protection" in settings

    assert settings["minimal_html"] == minimal_html
    assert settings["no_html"] == no_html
    assert settings["xss_protection"] == xss_protection


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


# ---------------------------------------------------------------------------
# Bleach characterization tests — baseline capture before nh3 migration
# These tests document EXACT bleach behavior. Plan 02-02 will update them
# to match nh3 output (DOM-equivalence approach applies there, not here).
# ---------------------------------------------------------------------------


def test_bleach_characterization_xss_protection():
    """Capture exact bleach xss_protection() output as regression baseline."""
    from kotti.sanitizers import xss_protection

    sanitized = xss_protection(unsanitized)

    # Script tags: bleach strips <script> tags but PRESERVES content
    assert "alert('XSS!')" in sanitized
    assert "<script>" not in sanitized

    # Attribute handling: bleach with lambda attributes=True preserves ALL attrs
    assert 'size="17"' in sanitized

    # Style preservation: bleach with all_styles preserves style values
    # Note: bleach normalizes CSS and adds trailing semicolon
    assert 'style="color: red;"' in sanitized

    # Link handling: bleach does NOT add rel attributes to links
    assert 'target="_blank"' in sanitized
    assert "rel=" not in sanitized

    # Tag handling: <marquee> IS in generally_xss_safe, so it is preserved
    assert "<marquee>" in sanitized


def test_bleach_characterization_minimal_html():
    """Capture exact bleach minimal_html() output as regression baseline."""
    from kotti.sanitizers import minimal_html

    sanitized = minimal_html(unsanitized)

    # Style handling: bleach with styles=[] strips CSS values but leaves empty attr
    assert 'style=""' in sanitized

    # Attribute stripping: size on <b> is NOT in markdown_attrs or print_attrs
    assert "size" not in sanitized.lower()


def test_bleach_characterization_no_html():
    """Capture exact bleach no_html() output as regression baseline."""
    from kotti.sanitizers import no_html

    sanitized = no_html(unsanitized)

    # All tags removed, text content preserved
    assert "<" not in sanitized
    assert "external links" in sanitized
