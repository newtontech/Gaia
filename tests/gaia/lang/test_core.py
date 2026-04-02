from gaia.lang import Package, claim, question, setting


def test_setting_creates_knowledge():
    with Package("test_pkg"):
        s = setting("Background assumption.")
    assert s.type == "setting"
    assert s.content == "Background assumption."


def test_claim_creates_knowledge():
    with Package("test_pkg"):
        c = claim("A scientific assertion.")
    assert c.type == "claim"
    assert c.content == "A scientific assertion."


def test_question_creates_knowledge():
    with Package("test_pkg"):
        q = question("An open question?")
    assert q.type == "question"


def test_claim_with_given_creates_strategy():
    with Package("test_pkg"):
        a = claim("Premise A.")
        b = claim("Premise B.")
        c = claim("Conclusion.", given=[a, b])
    assert c.type == "claim"
    assert c.strategy is not None
    assert c.strategy.type == "noisy_and"
    assert a in c.strategy.premises
    assert b in c.strategy.premises


def test_claim_with_background():
    with Package("test_pkg"):
        bg = setting("Context.")
        c = claim("Assertion.", background=[bg])
    assert bg in c.background


def test_universal_claim_with_parameters():
    with Package("test_pkg"):
        u = claim("∀x. P(x)", parameters=[{"name": "x", "type": "material"}])
    assert len(u.parameters) == 1
    assert u.parameters[0]["name"] == "x"


def test_package_collects_all_knowledge():
    with Package("test_pkg") as pkg:
        setting("BG.")
        claim("Claim.")
        question("Q?")
    assert len(pkg.knowledge) == 3


def test_package_namespace():
    with Package("test_pkg", namespace="galileo") as pkg:
        pass
    assert pkg.namespace == "galileo"
