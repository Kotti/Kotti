import pytest


@pytest.mark.user("admin")
def test_traversal(webtest, root):
    from kotti.resources import Document
    d1 = root["d1"] = Document(title="Title 1", body="Body 1")
    d2 = d1["d2"] = Document(title="Title 2", body="Body 2")
    d2["d3"] = Document(title="Title 3", body="Body 3")
    app = webtest.app

    resp = app.get("/d1")
    assert "Title 1" in resp.text
    assert "Body 1" in resp.text

    resp = app.get("/d1/d2")
    assert "Title 1" in resp.text
    assert "Title 2" in resp.text
    assert "Body 2" in resp.text

    resp = app.get("/d1/d2/d3")
    assert "Title 1" in resp.text
    assert "Title 2" in resp.text
    assert "Title 3" in resp.text
    assert "Body 3" in resp.text
