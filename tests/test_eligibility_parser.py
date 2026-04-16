from trialmatch.services import eligibility_parser


def test_fast_parse_ctgov_sections_without_llm(monkeypatch):
    criteria_text = """Inclusion Criteria:

* controlled asthma
* age 18-30 years

Exclusion Criteria:

* heart disease
* hypertension
"""

    def fail_get_client():
        raise AssertionError("LLM should not be called for structured criteria")

    monkeypatch.setattr(eligibility_parser, "get_reasoning_client", fail_get_client)

    parsed = eligibility_parser.parse_eligibility_criteria(criteria_text)

    assert parsed == {
        "inclusion": ["controlled asthma", "age 18-30 years"],
        "exclusion": ["heart disease", "hypertension"],
    }


def test_fast_parse_handles_nested_bullets_and_plain_lines():
    criteria_text = """Inclusion Criteria:

Asthmatic Subjects
* Males and women aged 18-65
* A weight of >=50 kg

Exclusion Criteria:

* Pregnancy.
  * Current pregnancy
* Smoking in last year
"""

    parsed = eligibility_parser.parse_eligibility_criteria(criteria_text)

    assert "Asthmatic Subjects" in parsed["inclusion"]
    assert "Males and women aged 18-65" in parsed["inclusion"]
    assert "A weight of >=50 kg" in parsed["inclusion"]
    assert "Pregnancy." in parsed["exclusion"]
    assert "Current pregnancy" in parsed["exclusion"]
    assert "Smoking in last year" in parsed["exclusion"]


def test_falls_back_to_llm_when_sections_missing(monkeypatch):
    class FakeClient:
        def chat_completion(self, **kwargs):
            assert kwargs["max_tokens"] == 192
            assert kwargs["temperature"] == 0.0

            class Response:
                choices = [
                    type(
                        "Choice",
                        (),
                        {
                            "message": {
                                "content": '{"inclusion": ["criterion a"], "exclusion": ["criterion b"]}'
                            }
                        },
                    )()
                ]

            return Response()

    monkeypatch.setattr(eligibility_parser, "get_reasoning_client", lambda: FakeClient())

    parsed = eligibility_parser.parse_eligibility_criteria(
        "Adults with asthma may be eligible. Exclude severe infection."
    )

    assert parsed == {
        "inclusion": ["criterion a"],
        "exclusion": ["criterion b"],
    }
