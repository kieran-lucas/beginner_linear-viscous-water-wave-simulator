"""Collapsible timeline graphs for amplitude, energy, and numerical stability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .education import stability_message
from .design_system import color, set_accessible_tooltip, set_button_role
from .simulation import DiagnosticSample, StabilityReport


@dataclass(frozen=True)
class GraphSeries:
    samples: Sequence[DiagnosticSample]
    color: QColor
    style: Qt.PenStyle


class TrendCanvas(QWidget):
    """Small dependency-free graph for one timeline metric."""

    BACKGROUND = color("canvas_background")
    TEXT = color("text_secondary")
    GRID = color("border")
    A_COLOR = color("primary")
    B_COLOR = color("comparison")

    def __init__(
        self,
        title: str,
        value_label: str,
        extractor: Callable[[DiagnosticSample], float],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.title = title
        self.value_label = value_label
        self.extractor = extractor
        self._history_a: Sequence[DiagnosticSample] = ()
        self._history_b: Sequence[DiagnosticSample] = ()
        self.setMinimumHeight(108)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_histories(
        self,
        history_a: Sequence[DiagnosticSample],
        history_b: Sequence[DiagnosticSample] | None = None,
    ) -> None:
        self._history_a = history_a
        self._history_b = history_b or ()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt callback name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.BACKGROUND)
        bounds = QRectF(self.rect())
        plot = bounds.adjusted(42.0, 25.0, -12.0, -24.0)
        self._draw_grid(painter, plot)
        self._draw_series(
            painter,
            plot,
            GraphSeries(self._history_a, self.A_COLOR, Qt.PenStyle.SolidLine),
        )
        self._draw_series(
            painter,
            plot,
            GraphSeries(self._history_b, self.B_COLOR, Qt.PenStyle.DashLine),
        )
        self._draw_labels(painter, bounds, plot)

    def _draw_grid(self, painter: QPainter, plot: QRectF) -> None:
        painter.setPen(QPen(self.GRID, 1.0))
        for index in range(3):
            y_value = plot.top() + index * plot.height() / 2.0
            painter.drawLine(QPointF(plot.left(), y_value), QPointF(plot.right(), y_value))
        for index in range(5):
            x_value = plot.left() + index * plot.width() / 4.0
            painter.drawLine(QPointF(x_value, plot.top()), QPointF(x_value, plot.bottom()))

    def _draw_series(self, painter: QPainter, plot: QRectF, series: GraphSeries) -> None:
        if not series.samples:
            return
        samples = self._downsample(series.samples, max(2, int(plot.width())))
        time_maximum = max(self._history_a[-1].time if self._history_a else 0.0, samples[-1].time)
        if self._history_b:
            time_maximum = max(time_maximum, self._history_b[-1].time)
        time_maximum = max(time_maximum, 1e-9)
        value_maximum = max(
            [self.extractor(sample) for sample in self._history_a]
            + [self.extractor(sample) for sample in self._history_b]
            + [1e-9]
        )

        path = QPainterPath()
        for index, sample in enumerate(samples):
            x_value = plot.left() + sample.time / time_maximum * plot.width()
            y_value = plot.bottom() - self.extractor(sample) / value_maximum * plot.height()
            point = QPointF(x_value, y_value)
            if index == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
        painter.setPen(QPen(series.color, 1.8, series.style))
        painter.drawPath(path)

    def _draw_labels(self, painter: QPainter, bounds: QRectF, plot: QRectF) -> None:
        painter.setFont(QFont(painter.font().family(), 8))
        painter.setPen(self.TEXT)
        painter.drawText(QPointF(bounds.left() + 5.0, 15.0), self.title)
        painter.drawText(QPointF(bounds.left() + 5.0, plot.top() + 4.0), self.value_label)
        time_maximum = max(
            self._history_a[-1].time if self._history_a else 0.0,
            self._history_b[-1].time if self._history_b else 0.0,
        )
        painter.drawText(QPointF(plot.left(), bounds.bottom() - 5.0), "0 s")
        painter.drawText(
            QPointF(plot.right() - 42.0, bounds.bottom() - 5.0),
            f"{time_maximum:.2f} s",
        )

    @staticmethod
    def _downsample(
        samples: Sequence[DiagnosticSample],
        maximum_points: int,
    ) -> Sequence[DiagnosticSample]:
        if len(samples) <= maximum_points:
            return samples
        stride = max(1, len(samples) // maximum_points)
        selected = list(samples[::stride])
        if selected[-1] is not samples[-1]:
            selected.append(samples[-1])
        return selected


class DiagnosticsPanel(QWidget):
    """Bottom scientific readout with compact trend plots and collapse support."""

    expanded_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("diagnosticsPanel")
        self.toggle_button = QPushButton("Hide diagnostics")
        set_button_role(self.toggle_button, "ghost")
        set_accessible_tooltip(
            self.toggle_button,
            "Collapse or restore timeline graphs. Keyboard shortcut: Ctrl+G.",
        )
        self.summary_label = QLabel()
        self.summary_label.setObjectName("diagnosticsSummary")
        self.summary_label.setWordWrap(True)
        self.stability_label = QLabel()
        self.stability_label.setObjectName("diagnosticsStability")
        self.stability_label.setWordWrap(True)
        self.performance_label = QLabel()
        self.performance_label.setObjectName("helper")
        self.performance_label.setVisible(False)

        self.amplitude_graph = TrendCanvas(
            "Maximum amplitude over time",
            "height",
            lambda sample: sample.maximum_amplitude,
        )
        self.energy_graph = TrendCanvas(
            "Approximate energy trend",
            "energy",
            lambda sample: sample.normalized_energy,
        )
        self.graph_frame = QFrame()
        self._build_layout()
        self.toggle_button.clicked.connect(self._toggle_graphs)

    def update_data(
        self,
        history_a: Sequence[DiagnosticSample],
        stability: StabilityReport,
        history_b: Sequence[DiagnosticSample] | None = None,
    ) -> None:
        self.amplitude_graph.set_histories(history_a, history_b)
        self.energy_graph.set_histories(history_a, history_b)
        if history_a:
            current = history_a[-1]
            comparison = ""
            if history_b:
                compare = history_b[-1]
                comparison = (
                    f"   B: max height {compare.maximum_amplitude:.3f} m, "
                    f"energy {compare.normalized_energy:.0%}."
                )
            self.summary_label.setText(
                f"Time {current.time:.2f} s   A: max height "
                f"{current.maximum_amplitude:.3f} m, energy "
                f"{current.normalized_energy:.0%}.{comparison}"
            )
        level, message = stability_message(stability)
        self.stability_label.setProperty("level", level)
        self.stability_label.setText(message)
        self.stability_label.style().unpolish(self.stability_label)
        self.stability_label.style().polish(self.stability_label)

    def set_advanced_visible(self, visible: bool) -> None:
        self.performance_label.setVisible(visible)

    def set_render_rate(self, frames_per_second: float) -> None:
        self.performance_label.setText(
            f"Advanced performance: approximately {frames_per_second:.1f} rendered frames/s."
        )

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)

        header = QHBoxLayout()
        heading = QLabel("Diagnostics")
        heading.setObjectName("sectionHeading")
        legend = QLabel("A blue solid   B amber dashed")
        legend.setObjectName("helper")
        header.addWidget(heading)
        header.addSpacing(8)
        header.addWidget(legend)
        header.addStretch(1)
        header.addWidget(self.toggle_button)
        layout.addLayout(header)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.stability_label)
        layout.addWidget(self.performance_label)

        graphs = QHBoxLayout(self.graph_frame)
        graphs.setContentsMargins(0, 0, 0, 0)
        graphs.setSpacing(8)
        graphs.addWidget(self.amplitude_graph)
        graphs.addWidget(self.energy_graph)
        layout.addWidget(self.graph_frame)

    def _toggle_graphs(self) -> None:
        visible = self.graph_frame.isHidden()
        self.graph_frame.setVisible(visible)
        self.toggle_button.setText("Hide diagnostics" if visible else "Show diagnostics")
        self.expanded_changed.emit(visible)
