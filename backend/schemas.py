from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Weights(StrictModel):
    hard_skills: float = Field(default=0.50, ge=0, le=1)
    experience: float = Field(default=0.25, ge=0, le=1)
    education: float = Field(default=0.15, ge=0, le=1)
    soft_skills: float = Field(default=0.10, ge=0, le=1)

    @model_validator(mode="after")
    def valid_total(self):
        if abs(sum(self.model_dump().values()) - 1) > 0.0001:
            raise ValueError("La somme des pondérations doit être égale à 1.")
        return self


class AnalysisRequest(StrictModel):
    cv_text: str = Field(min_length=30, max_length=30000)
    job_text: str = Field(min_length=30, max_length=30000)
    weights: Weights = Field(default_factory=Weights)
    use_llm: bool = False


class Skill(StrictModel):
    name: str
    category: Literal["hard_skills", "soft_skills"]
    evidence: str
    required: bool = True


class Profile(StrictModel):
    sections: dict[str, str]
    skills: list[Skill]
    experience_years: float | None = None
    education_level: int | None = None
    degrees: list[str] = Field(default_factory=list)


class Gap(StrictModel):
    skill: str
    category: Literal["hard_skills", "soft_skills"]
    status: Literal["Couvert", "Partiel", "Absent"]
    similarity: float = Field(ge=0, le=1)
    evidence: str
    required: bool


class Component(StrictModel):
    score: float | None = Field(ge=0, le=100)
    explanation: str


class Action(StrictModel):
    skill: str
    project: str
    resource: str
    success_criterion: str


class Rewrite(StrictModel):
    original: str
    suggestion: str


class Recommendations(StrictModel):
    summary: str = Field(max_length=4000)
    strengths: list[str] = Field(max_length=15)
    priorities: list[str] = Field(max_length=15)
    rewrites: list[Rewrite] = Field(max_length=8)
    actions: list[Action] = Field(max_length=12)
    source: Literal["local", "llm"] = "local"


class AnalysisResult(StrictModel):
    score: float = Field(ge=0, le=100)
    weights: Weights
    effective_weights: dict[str, float]
    components: dict[str, Component]
    gaps: list[Gap]
    cv: Profile
    job: Profile
    recommendations: Recommendations
    warnings: list[str]
    timings_ms: dict[str, float]
    embedding_model: str


class SaveAnalysisRequest(StrictModel):
    title: str = Field(min_length=1, max_length=100)
    result: AnalysisResult
    is_demo: bool = False


class SavedAnalysisSummary(StrictModel):
    id: str
    title: str
    created_at: str
    score: float = Field(ge=0, le=100)
    is_demo: bool = False


class SavedAnalysis(SavedAnalysisSummary):
    result: AnalysisResult


class SavedAnalysisPage(StrictModel):
    items: list[SavedAnalysisSummary]
    total: int = Field(ge=0)
