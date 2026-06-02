"""Reusable PySide6 canvas for a readable one-dimensional wave profile."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from .simulation import DiagnosticSample


@dataclass(frozen=True)
class PlotMargins:
    left: float = 66.0
    top: float = 48.0
    right: float = 24.0
    bottom: float = 56.0


@dataclass(frozen=True)
class PlotTransform:
    """Map physical wave coordinates into a plot rectangle."""

    rectangle: QRectF
    x_minimum: float
    x_maximum: float
    y_extent: float

    def __post_init__(self) -> None:
        if self.x_maximum <= self.x_minimum:
            raise ValueError("x_maximum must exceed x_minimum")
        if self.y_extent <= 0:
            raise ValueError("y_extent must be greater than zero")

    def to_canvas(self, x_value: float, y_value: float) -> QPointF:
        x_ratio = (x_value - self.x_minimum) / (self.x_maximum - self.x_minimum)
        y_ratio = (self.y_extent - y_value) / (2.0 * self.y_extent)
        return QPointF(
            self.rectangle.left() + x_ratio * self.rectangle.width(),
            self.rectangle.top() + y_ratio * self.rectangle.height(),
        )

    def x_from_canvas(self, canvas_x: float) -> float:
        ratio = (canvas_x - self.rectangle.left()) / self.rectangle.width()
        return self.x_minimum + ratio * (self.x_maximum - self.x_minimum)


class WaveCanvas(QWidget):
    """Calm scientific profile plot that consumes simulation state snapshots.

    The widget does not advance the solver. It renders supplied values and can
    therefore be reused for playback, comparisons, and exported screenshots.
    """

    BACKGROUND = QColor("#F7F8FA")
    PLOT_BACKGROUND = QColor("#FFFFFF")
    TEXT = QColor("#172033")
    SECONDARY_TEXT = QColor("#5B667A")
    GRID = QColor("#DCE2EA")
    EQUILIBRIUM = QColor("#8290A4")
    CURRENT_WAVE = QColor("#1769AA")
    SNAPSHOT = QColor("#C77C18")
    MARKER = QColor("#26734D")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(640, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._positions: tuple[float, ...] = ()
        self._displacement: tuple[float, ...] = ()
        self._comparison: tuple[float, ...] | None = None
        self._comparison_diagnostics: DiagnosticSample | None = None
        self._diagnostics: DiagnosticSample | None = None
        self._initial_amplitude = 1.0
        self._vertical_extent = 1.2
        self._wavelength: float | None = None
        self._hover_index: int | None = None
        self._show_learning_markers = True

    def set_wave_data(
        self,
        positions: Sequence[float],
        displacement: Sequence[float],
        diagnostics: DiagnosticSample | None = None,
        *,
        initial_amplitude: float | None = None,
        wavelength: float | None = None,
    ) -> None:
        """Render a new wave state while keeping the vertical scale stable."""

        if len(positions) != len(displacement):
            raise ValueError("positions and displacement must have matching lengths")
        if len(positions) < 2:
            raise ValueError("wave data must contain at least two points")
        if positions[-1] <= positions[0]:
            raise ValueError("positions must increase across the domain")

        self._positions = tuple(positions)
        self._displacement = tuple(displacement)
        self._diagnostics = diagnostics
        self._wavelength = wavelength if wavelength and wavelength > 0 else None
        if initial_amplitude is not None:
            self._initial_amplitude = max(abs(initial_amplitude), 1e-9)
            self._vertical_extent = max(1.2 * self._initial_amplitude, 1e-6)
        self.update()

    def set_snapshot(self, displacement: Sequence[float] | None) -> None:
        """Set an optional comparison curve without taking ownership of state.

        Kept as a compatibility alias for early snapshot-based callers.
        """

        self.set_comparison_data(displacement)

    def set_comparison_data(
        self,
        displacement: Sequence[float] | None,
        diagnostics: DiagnosticSample | None = None,
        *,
        initial_amplitude: float | None = None,
    ) -> None:
        """Set a synchronized B overlay using the same physical plot scale."""

        if displacement is None:
            self._comparison = None
            self._comparison_diagnostics = None
        else:
            if self._positions and len(displacement) != len(self._positions):
                raise ValueError("snapshot or comparison must match the current wave grid")
            self._comparison = tuple(displacement)
            self._comparison_diagnostics = diagnostics
            if initial_amplitude is not None:
                self._vertical_extent = max(
                    self._vertical_extent,
                    1.2 * max(abs(initial_amplitude), 1e-9),
                )
        self.update()

    def set_learning_markers_visible(self, visible: bool) -> None:
        self._show_learning_markers = visible
        self.update()

    def render_to_image(self, width: int = 1200, height: int = 700):
        """Return a raster snapshot suitable for a later export action."""

        from PySide6.QtGui import QImage

        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(self.BACKGROUND)
        painter = QPainter(image)
        self._draw(painter, QRectF(0.0, 0.0, float(width), float(height)))
        painter.end()
        return image

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt callback name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw(painter, QRectF(self.rect()))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt callback name
        transform = self._transform(QRectF(self.rect()))
        if transform is None or not transform.rectangle.contains(event.position()):
            self._hover_index = None
        else:
            x_value = transform.x_from_canvas(event.position().x())
            self._hover_index = min(
                range(len(self._positions)),
                key=lambda index: abs(self._positions[index] - x_value),
            )
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt callback name
        self._hover_index = None
        self.update()

    def _draw(self, painter: QPainter, bounds: QRectF) -> None:
        painter.fillRect(bounds, self.BACKGROUND)
        transform = self._transform(bounds)
        if transform is None:
            self._draw_centered_text(painter, bounds, "Preparing wave profile...")
            return

        plot = transform.rectangle
        painter.fillRect(plot, self.PLOT_BACKGROUND)
        self._draw_title(painter, bounds)
        self._draw_grid(painter, transform)
        if self._comparison:
            self._draw_profile(
                painter,
                transform,
                self._comparison,
                self.SNAPSHOT,
                1.7,
                Qt.PenStyle.DashLine,
            )
        self._draw_profile(painter, transform, self._displacement, self.CURRENT_WAVE, 2.6)
        if self._show_learning_markers:
            self._draw_amplitude_marker(painter, transform)
            self._draw_wavelength_marker(painter, transform)
        self._draw_hover_readout(painter, transform)
        self._draw_status(painter, bounds)

    def _transform(self, bounds: QRectF) -> PlotTransform | None:
        if len(self._positions) < 2:
            return None
        margins = PlotMargins()
        plot = bounds.adjusted(margins.left, margins.top, -margins.right, -margins.bottom)
        if plot.width() <= 0 or plot.height() <= 0:
            return None
        return PlotTransform(plot, self._positions[0], self._positions[-1], self._vertical_extent)

    def _draw_title(self, painter: QPainter, bounds: QRectF) -> None:
        painter.setPen(self.TEXT)
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QPointF(66.0, 29.0), "Surface displacement over space")

        painter.setPen(self.SECONDARY_TEXT)
        font.setPointSize(9)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(QPointF(bounds.right() - 190.0, 29.0), "A current")
        painter.setPen(QPen(self.CURRENT_WAVE, 2.6))
        painter.drawLine(
            QPointF(bounds.right() - 212.0, 25.0),
            QPointF(bounds.right() - 196.0, 25.0),
        )
        if self._comparison:
            painter.setPen(self.SECONDARY_TEXT)
            painter.drawText(QPointF(bounds.right() - 92.0, 29.0), "B compare")
            painter.setPen(QPen(self.SNAPSHOT, 1.7, Qt.PenStyle.DashLine))
            painter.drawLine(
                QPointF(bounds.right() - 114.0, 25.0),
                QPointF(bounds.right() - 98.0, 25.0),
            )

    def _draw_grid(self, painter: QPainter, transform: PlotTransform) -> None:
        plot = transform.rectangle
        painter.setFont(QFont(painter.font().family(), 8))
        for index in range(6):
            x_value = (
                transform.x_minimum
                + index * (transform.x_maximum - transform.x_minimum) / 5.0
            )
            point = transform.to_canvas(x_value, 0.0)
            painter.setPen(QPen(self.GRID, 1.0))
            painter.drawLine(QPointF(point.x(), plot.top()), QPointF(point.x(), plot.bottom()))
            painter.setPen(self.SECONDARY_TEXT)
            painter.drawText(QPointF(point.x() - 13.0, plot.bottom() + 19.0), f"{x_value:.0f}")

        for index in range(-2, 3):
            y_value = index * transform.y_extent / 2.0
            point = transform.to_canvas(transform.x_minimum, y_value)
            pen = QPen(self.EQUILIBRIUM if index == 0 else self.GRID, 1.4 if index == 0 else 1.0)
            painter.setPen(pen)
            painter.drawLine(QPointF(plot.left(), point.y()), QPointF(plot.right(), point.y()))
            painter.setPen(self.SECONDARY_TEXT)
            painter.drawText(QPointF(plot.left() - 48.0, point.y() + 4.0), f"{y_value:.1f}")

        painter.setPen(self.SECONDARY_TEXT)
        painter.drawText(
            QPointF(plot.center().x() - 35.0, plot.bottom() + 41.0),
            "Position x (m)",
        )
        painter.save()
        painter.translate(17.0, plot.center().y() + 62.0)
        painter.rotate(-90.0)
        painter.drawText(QPointF(0.0, 0.0), "Displacement u (m)")
        painter.restore()

    def _draw_profile(
        self,
        painter: QPainter,
        transform: PlotTransform,
        displacement: Sequence[float],
        color: QColor,
        width: float,
        style: Qt.PenStyle = Qt.PenStyle.SolidLine,
    ) -> None:
        path = QPainterPath()
        start = transform.to_canvas(self._positions[0], displacement[0])
        path.moveTo(start)
        for x_value, y_value in zip(self._positions[1:], displacement[1:]):
            path.lineTo(transform.to_canvas(x_value, y_value))
        painter.setPen(
            QPen(color, width, style, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        )
        painter.drawPath(path)

    def _draw_amplitude_marker(self, painter: QPainter, transform: PlotTransform) -> None:
        if not self._displacement:
            return
        peak_index = max(
            range(len(self._displacement)),
            key=lambda index: abs(self._displacement[index]),
        )
        peak_value = self._displacement[peak_index]
        peak = transform.to_canvas(self._positions[peak_index], peak_value)
        equilibrium = transform.to_canvas(self._positions[peak_index], 0.0)
        painter.setPen(QPen(self.MARKER, 1.2, Qt.PenStyle.DashLine))
        painter.drawLine(equilibrium, peak)
        painter.setPen(self.MARKER)
        label_y = min(peak.y(), equilibrium.y()) - 7.0
        painter.drawText(QPointF(peak.x() + 7.0, label_y), f"amplitude {abs(peak_value):.2f} m")

    def _draw_wavelength_marker(self, painter: QPainter, transform: PlotTransform) -> None:
        if self._wavelength is None:
            return
        start_x = transform.x_minimum + 0.08 * (transform.x_maximum - transform.x_minimum)
        end_x = min(start_x + self._wavelength, transform.x_maximum)
        if end_x <= start_x:
            return
        y_value = -0.82 * transform.y_extent
        start = transform.to_canvas(start_x, y_value)
        end = transform.to_canvas(end_x, y_value)
        painter.setPen(QPen(self.MARKER, 1.2))
        painter.drawLine(start, end)
        painter.drawLine(QPointF(start.x(), start.y() - 4.0), QPointF(start.x(), start.y() + 4.0))
        painter.drawLine(QPointF(end.x(), end.y() - 4.0), QPointF(end.x(), end.y() + 4.0))
        label_position = QPointF((start.x() + end.x()) / 2.0 - 36.0, start.y() - 7.0)
        painter.drawText(label_position, f"wavelength {self._wavelength:.1f} m")

    def _draw_hover_readout(self, painter: QPainter, transform: PlotTransform) -> None:
        if self._hover_index is None or self._hover_index >= len(self._displacement):
            return
        x_value = self._positions[self._hover_index]
        y_value = self._displacement[self._hover_index]
        point = transform.to_canvas(x_value, y_value)
        painter.setPen(QPen(self.CURRENT_WAVE, 1.2))
        painter.setBrush(self.PLOT_BACKGROUND)
        painter.drawEllipse(point, 4.0, 4.0)

        label = f"x = {x_value:.2f} m   u = {y_value:.3f} m"
        metrics = QFontMetrics(painter.font())
        text_width = metrics.horizontalAdvance(label)
        box_x = min(point.x() + 12.0, transform.rectangle.right() - text_width - 18.0)
        box_y = max(point.y() - 34.0, transform.rectangle.top() + 7.0)
        box = QRectF(box_x, box_y, text_width + 12.0, 24.0)
        painter.fillRect(box, self.PLOT_BACKGROUND)
        painter.setPen(QPen(self.GRID, 1.0))
        painter.drawRect(box)
        painter.setPen(self.TEXT)
        painter.drawText(QPointF(box.left() + 6.0, box.top() + 16.0), label)

    def _draw_status(self, painter: QPainter, bounds: QRectF) -> None:
        if self._diagnostics is None:
            return
        diagnostic = self._diagnostics
        painter.setPen(self.SECONDARY_TEXT)
        comparison = ""
        if self._comparison_diagnostics is not None:
            comparison = (
                f"    B max |u| = {self._comparison_diagnostics.maximum_amplitude:.3f} m"
            )
        painter.drawText(
            QPointF(bounds.left() + 66.0, bounds.bottom() - 10.0),
            f"t = {diagnostic.time:.2f} s    "
            f"A max |u| = {diagnostic.maximum_amplitude:.3f} m"
            f"{comparison}    A energy = {diagnostic.normalized_energy:.1%}",
        )

    def _draw_centered_text(self, painter: QPainter, bounds: QRectF, text: str) -> None:
        painter.setPen(self.SECONDARY_TEXT)
        painter.drawText(bounds, Qt.AlignmentFlag.AlignCenter, text)
