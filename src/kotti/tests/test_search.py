from kotti.testing import DummyRequest


def _create_contents(root):
    from kotti.resources import Content, File

    doc1 = root["doc1"] = Content(title="First Document", description="I am the first.")
    doc11 = root["doc1"]["doc11"] = Content(
        title="Second Document", description="And I am the second."
    )
    doc12 = root["doc1"]["doc12"] = Content(title="Third Document")
    file1 = root["doc1"]["file1"] = File(
        title="First File", description="this is a file"
    )
    return doc1, doc11, doc12, file1


def _create_contents_with_tags(root=None):
    from kotti.resources import get_root
    from kotti.resources import Content, File

    if root is None:
        root = get_root()

    animals = root["animals"] = Content(title="Animals")
    cat = root["animals"]["cat"] = Content(title="Cat")
    dog = root["animals"]["dog"] = Content(title="Dog")
    monkey = root["animals"]["monkey"] = Content(title="Monkey")
    gorilla = root["animals"]["gorilla"] = Content(title="Gorilla")
    monkey_file = root["animals"]["monkey_file"] = File(
        title="Monkey File",
        description="A Rhesus Macaque and a Green Monkey walk into a bar...",
    )

    root["animals"]["cat"].tags = ["Animals", "Cat"]
    root["animals"]["dog"].tags = ["Animals", "Dog"]
    root["animals"]["monkey"].tags = ["Animals", "Monkey", "Primate"]
    root["animals"]["monkey_file"].tags = ["Animals", "Monkey", "Primate"]
    root["animals"]["gorilla"].tags = ["Animals", "Gorilla", "Primate"]

    return animals, cat, dog, monkey, gorilla, monkey_file


def test_search_empty_content(db_session):
    from kotti.views.util import search_content

    request = DummyRequest()
    results = search_content("teststring", request)
    assert results == []


def test_search_content(root):
    from kotti.views.util import search_content
    from kotti import DBSession
    from kotti.resources import Tag

    request = DummyRequest()
    doc1, doc11, doc12, file1 = _create_contents(root)
    results = search_content("First Document", request)
    assert len(results) == 1
    assert results[0]["name"] == "doc1"
    assert results[0]["title"] == "First Document"
    results = search_content("Document", request)
    # The frontpage contains 'Documentation' in its body!
    assert len(results) == 4
    assert results[1]["name"] == "doc11"
    assert results[1]["title"] == "Second Document"
    assert results[1]["path"] == "/doc1/doc11/"
    assert results[1]["path"][-1] == "/"

    animals, cat, dog, monkey, gorilla, monkey_file = _create_contents_with_tags()

    tags = DBSession.query(Tag).all()
    assert len(tags) == 6
    results = search_content("Animals", request)
    assert len(results) == 6
    results = search_content("Cat", request)
    assert len(results) == 1
    results = search_content("Primate", request)
    assert len(results) == 3

    # Tags were included in general search by modifying the pre-existing
    # approach, wherein searching first worked on title and description,
    # then on body, so that the search order became:
    #
    #     first on title + description
    #         then on tags
    #             then on body
    #
    # So we test here to assure search results come back in that order.
    # Searching on 'Animals', we should find all 6 content items, and the
    # first item should be the Animals folder, found with a title hit, and
    # the other items were found via tags.
    #
    # Note: this ordering is done to have some method, but it does not
    #       necessarily constitute a specification.
    #
    results = search_content("Animals", request)
    assert len(results) == 6
    assert results[0]["name"] == "animals"


def test_search_file_description(root):
    from kotti.views.util import search_content

    request = DummyRequest()
    doc1, doc11, doc12, file1 = _create_contents(root)
    results = search_content("this is a file", request)
    assert len(results) == 1
    assert results[0]["name"] == "file1"
    assert results[0]["title"] == "First File"
    assert results[0]["path"] == "/doc1/file1/"


def test_search_content_without_permission(config, root):
    from kotti.views.util import search_content

    request = DummyRequest()
    _create_contents(root)
    config.testing_securitypolicy(permissive=False)
    results = search_content("Document", request)
    assert len(results) == 0


def test_search_functional(webtest, root):

    doc1, doc11, doc12, file1 = _create_contents(root)

    resp = webtest.app.get("/")

    search_form = resp.forms["form-search"]
    search_form["search-term"] = "First Document"
    resp = search_form.submit()
    assert "I am the first" in resp.text
    assert "And I am the second" not in resp.text

    search_form = resp.forms["form-search"]
    search_form["search-term"] = "Document"
    resp = search_form.submit()
    assert "I am the first" in resp.text
    assert "And I am the second" in resp.text

    search_form = resp.forms["form-search"]
    search_form["search-term"] = "is a file"
    resp = search_form.submit()
    assert "And I am the second" not in resp.text
    assert "Third" not in resp.text
    assert "First File" in resp.text
