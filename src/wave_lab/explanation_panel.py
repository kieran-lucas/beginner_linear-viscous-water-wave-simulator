"""Right-side interactive textbook panel for the desktop app."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from .control_panel import LabSettings, Preset
from .education import CONCEPTS, format_change, interpretation, preset_message, stability_message
from .simulation import DiagnosticSample, StabilityReport


class ExplanationPanel(QWidget):
    """Render maintainable educational copy in concise readable blocks."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("explanationPanel")
        self.setFixedWidth(300)
        self._concept = "overview"

        self.concept_title = QLabel()
        self.concept_title.setObjectName("panelHeading")
        self.explanation_label = self._text_label("explanationText")
        self.equation_note = self._text_label("helper")
        self.changed_label = self._text_label("changedText")
        self.interpretation_label = self._text_label("interpretationText")
        self.warning_label = self._text_label("explanationWarning")
        self.try_this_label = self._text_label("helper")
        self._build_layout()
        self.show_concept("overview")

    def show_concept(self, concept: str, settings: LabSettings | None = None) -> None:
        """Display one concept and optionally explain the user's latest change."""

        self._concept = concept if concept in CONCEPTS else "overview"
        copy = CONCEPTS[self._concept]
        self.concept_title.setText(copy.title)
        self.explanation_label.setText(copy.plain_english)
        self.equation_note.setText(copy.equation_note)
        self.try_this_label.setText(f"Try this: {copy.try_this}")
        if settings is not None:
            self.changed_label.setText(format_change(self._concept, settings))

    def show_preset(self, preset: Preset) -> None:
        self.changed_label.setText(preset_message(preset))

    def update_interpretation(
        self,
        diagnostic: DiagnosticSample | None,
        damping_rate: float,
    ) -> None:
        self.interpretation_label.setText(interpretation(diagnostic, damping_rate))

    def update_stability(self, report: StabilityReport) -> None:
        level, message = stability_message(report)
        self.warning_label.setProperty("level", level)
        self.warning_label.setText(message)
        self.warning_label.style().unpolish(self.warning_label)
        self.warning_label.style().polish(self.warning_label)

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel("What is happening?")
        title.setObjectName("panelHeading")
        layout.addWidget(title)
        layout.addWidget(self._divider())

        equation_heading = QLabel("Model equation")
        equation_heading.setObjectName("sectionHeading")
        layout.addWidget(equation_heading)
        equation = QLabel("u_tt + gamma u_t = c^2 u_xx")
        equation.setObjectName("equation")
        layout.addWidget(equation)
        layout.addWidget(self.equation_note)

        layout.addWidget(self._divider())
        layout.addWidget(self.concept_title)
        layout.addWidget(self.explanation_label)

        changed_heading = QLabel("What changed?")
        changed_heading.setObjectName("sectionHeading")
        layout.addWidget(changed_heading)
        self.changed_label.setText("Preset loaded: Gentle ripple. Start here.")
        layout.addWidget(self.changed_label)

        interpretation_heading = QLabel("Current interpretation")
        interpretation_heading.setObjectName("sectionHeading")
        layout.addWidget(interpretation_heading)
        layout.addWidget(self.interpretation_label)
        layout.addWidget(self.warning_label)
        layout.addStretch(1)
        layout.addWidget(self.try_this_label)

    @staticmethod
    def _text_label(object_name: str) -> QLabel:
        label = QLabel()
        label.setWordWrap(True)
        label.setObjectName(object_name)
        return label

    @staticmethod
    def _divider() -> QFrame:
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        return divider

