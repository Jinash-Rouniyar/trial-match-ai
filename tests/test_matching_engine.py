import types

from trialmatch.services import matching_engine


class DummyEmbeddingClient:
  def __call__(self, text: str):
    return [1.0, 0.0, 0.0]


def test_calculate_match_score_exclusion_zero(monkeypatch):
  # Patch get_embedding to force high similarity for exclusion criteria
  def fake_get_embedding(text: str):
    # Same vector for patient and exclusion -> cosine ~1.0
    return matching_engine.np.array([1.0, 0.0, 0.0], dtype=matching_engine.np.float32)

  monkeypatch.setattr(matching_engine, "get_embedding", fake_get_embedding)

  patient_profile = {"text_summary": "Patient has condition X"}
  trial_criteria = {"exclusion": ["condition X"], "inclusion": ["something else"]}

  score = matching_engine.calculate_match_score(patient_profile, trial_criteria)
  assert score == 0.0


def test_calculate_match_score_positive(monkeypatch):
  # Force low similarity for exclusions and high for inclusions
  def fake_get_embedding(text: str):
    if "include" in text:
      return matching_engine.np.array([1.0, 0.0, 0.0], dtype=matching_engine.np.float32)
    return matching_engine.np.array([0.0, 1.0, 0.0], dtype=matching_engine.np.float32)

  monkeypatch.setattr(matching_engine, "get_embedding", fake_get_embedding)

  patient_profile = {"text_summary": "include"}
  trial_criteria = {"exclusion": ["other"], "inclusion": ["include"]}

  score = matching_engine.calculate_match_score(patient_profile, trial_criteria)
  assert score > 0.0

