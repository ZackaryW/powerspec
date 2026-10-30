from powerspec.utils.sections import compose_sections


def test_sections_follow_the_intro_in_order():
    text = compose_sections("Pick one.", [("alpha", "A body"), ("beta", "B body")])

    assert text == "Pick one.\n\n### alpha\n\nA body\n\n### beta\n\nB body"


def test_empty_sections_are_omitted_and_one_section_stays_labeled():
    assert compose_sections("Pick one.", [("alpha", ""), ("beta", "B body")]) == \
        "Pick one.\n\n### beta\n\nB body"


def test_no_content_produces_nothing():
    assert compose_sections("Pick one.", [("alpha", ""), ("beta", None)]) == ""
    assert compose_sections("Pick one.", []) == ""


def test_repeated_labels_keep_the_first_section():
    assert compose_sections("Intro", [("a", "first"), ("a", "second")]) == "Intro\n\n### a\n\nfirst"
