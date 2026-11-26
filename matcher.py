"""TF-IDF similarity, skill comparison and recommendations."""
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from preprocess import clean_text, extract_skills, for_tfidf
from skills_db import SKILL_TO_CATEGORY, get_resources

SKILL_WEIGHT, TEXT_WEIGHT = 0.7, 0.3


def text_similarity(cv_clean: str, jd_clean: str) -> float:
    """Cosine similarity (0-1) of TF-IDF vectors for the CV and job description."""
    try:
        vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)  # stop-words/stemming done in preprocess
        m = vec.fit_transform([for_tfidf(cv_clean), for_tfidf(jd_clean)])
        return float(cosine_similarity(m[0], m[1])[0][0])
    except ValueError:  # empty vocabulary
        return 0.0


def verdict(score: float) -> str:
    if score >= 75: return "Strong overlap"
    if score >= 50: return "Moderate overlap"
    if score >= 25: return "Partial overlap"
    return "Low overlap"


def analyze(cv_raw: str, jd_raw: str, progress=None) -> dict:
    """Run the full analysis. `progress` is an optional callback(stage, info_dict) fired as each real
    pipeline stage completes, so a UI can show genuine progress. It does not affect the result."""
    def _step(stage, **info):
        if progress is not None:
            progress(stage, info)

    cv, jd = clean_text(cv_raw), clean_text(jd_raw)
    _step("clean", cv_chars=len(cv), jd_chars=len(jd))
    cv_sk, jd_sk = extract_skills(cv), extract_skills(jd)
    _step("skills", cv_skills=len(cv_sk), jd_skills=len(jd_sk))

    matched = sorted(set(cv_sk) & set(jd_sk), key=lambda s: -jd_sk[s])
    missing = sorted(set(jd_sk) - set(cv_sk), key=lambda s: -jd_sk[s])  # most-mentioned first
    extra = sorted(set(cv_sk) - set(jd_sk))

    sim = text_similarity(cv, jd)
    _step("similarity", similarity=round(sim * 100, 1))
    coverage = len(matched) / len(jd_sk) if jd_sk else None
    score = (SKILL_WEIGHT * coverage + TEXT_WEIGHT * sim) if coverage is not None else sim
    score = round(min(score, 1.0) * 100, 1)

    rows = []
    for s in sorted(set(cv_sk) | set(jd_sk)):
        status = "Matched" if s in cv_sk and s in jd_sk else "Missing" if s in jd_sk else "Extra"
        rows.append({"Skill": s.title(), "Category": SKILL_TO_CATEGORY[s], "Status": status,
                     "Job mentions": jd_sk.get(s, 0), "CV mentions": cv_sk.get(s, 0)})
    table = pd.DataFrame(rows, columns=["Skill", "Category", "Status", "Job mentions", "CV mentions"])
    if not table.empty:
        order = {"Missing": 0, "Matched": 1, "Extra": 2}
        table = table.sort_values(by=["Status", "Job mentions"], key=lambda c: c.map(order) if c.name == "Status" else -c)
    required = table[table["Status"] != "Extra"]
    categories = (required.groupby(["Category", "Status"]).size().unstack(fill_value=0)
                  .reindex(columns=["Matched", "Missing"], fill_value=0))

    _step("score", score=score, verdict=verdict(score))
    return {
        "score": score, "verdict": verdict(score), "text_similarity": round(sim * 100, 1),
        "skill_coverage": None if coverage is None else round(coverage * 100, 1),
        "matched": matched, "missing": missing, "extra": extra,
        "jd_skill_count": len(jd_sk), "categories": categories, "table": table,
        "recommendations": {s: get_resources(s) for s in missing[:10]},
    }
