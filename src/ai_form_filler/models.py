"""Data models for form extraction and fill plans (domain layer)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FormField:
    """A single form field as extracted from the page."""

    key: str  # Unique key used for LLM mapping (e.g. "email", "field_0")
    tag: str  # input, textarea, select
    input_type: str  # text, email, password, checkbox, radio, etc.
    name: str | None
    id: str | None
    placeholder: str | None
    label_text: str | None
    options: list[tuple[str, str]] = field(default_factory=list)  # (value, label) for select/radio


@dataclass
class FormSchema:
    """Schema of a form: list of fields for LLM consumption."""

    fields: list[FormField] = field(default_factory=list)

    def get_field_by_key(self, key: str) -> "FormField | None":
        """Return the field with the given key, or None."""
        for f in self.fields:
            if f.key == key:
                return f
        return None

    def to_llm_description(self) -> str:
        """Serialize for LLM prompt."""
        lines = []
        for f in self.fields:
            parts = [f"key={f.key}", f"tag={f.tag}", f"type={f.input_type}"]
            if f.name:
                parts.append(f"name={f.name!r}")
            if f.id:
                parts.append(f"id={f.id!r}")
            if f.placeholder:
                parts.append(f"placeholder={f.placeholder!r}")
            if f.label_text:
                parts.append(f"label={f.label_text!r}")
            if f.options:
                parts.append(f"options={f.options}")
            lines.append(" ".join(parts))
        return "\n".join(lines)


@dataclass
class FillAction:
    """Single fill instruction from LLM: which field and what value."""

    field_key: str
    value: Any  # str, bool, or option value


@dataclass
class FillPlan:
    """Plan of actions to perform on the form."""

    actions: list[FillAction] = field(default_factory=list)


@dataclass(frozen=True)
class NavigationIntent:
    """LLM output: where to navigate before filling a form."""

    url: str
    reason: str
