from citecheck import CitationChecker, parse_reference, split_references

REAL = {
    "DOI": "10.1000/real.1",
    "title": ["Attention Is All You Need"],
    "issued": {"date-parts": [[2017]]},
}


def fake_fetch(url, params=None):
    if url.endswith("/10.1000/real.1"):
        return REAL
    if url.endswith("/10.9999/fake.42"):
        return None
    if params:  # bibliographic search
        q = params["query.bibliographic"].lower()
        if "attention" in q:
            return {"items": [REAL]}
        return {"items": [{"DOI": "10.1/x", "title": ["Unrelated Paper On Soil Chemistry"], "issued": {"date-parts": [[2003]]}}]}
    return None


def test_split_numbered():
    text = "[1] A. Author, \"First paper title here\", 2020.\n[2] B. Author,\n  \"Second paper title\", 2021."
    refs = split_references(text)
    assert len(refs) == 2 and "Second paper title" in refs[1]


def test_parse_fields():
    r = parse_reference('A. Vaswani et al., "Attention Is All You Need", NeurIPS, 2017. doi:10.1000/real.1.')
    assert r.doi == "10.1000/real.1" and r.year == 2017 and r.title == "Attention Is All You Need"


def test_verdicts():
    c = CitationChecker(fetch=fake_fetch)
    assert c.check('Vaswani, "Attention Is All You Need", 2017, 10.1000/real.1').status == "verified"
    assert c.check('Smith, "A Paper That Does Not Exist", 2022, 10.9999/fake.42').status == "not_found"
    assert c.check('Vaswani, "Attention Is All You Need", 2017.').status == "verified"
    assert c.check('Vaswani, "Attention Is All You Need", 2009.').status == "suspicious"   # wrong year
    assert c.check('Doe, "Quantum Banana Networks for Urdu Poetry", 2024.').status == "not_found"
