from __future__ import annotations

import math
import random
import sys
import time
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, Qt, QTimer, Signal, Slot
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QPainter,
    QPaintEvent,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication, QWidget

if TYPE_CHECKING:
    from PySide6.QtCore import QEvent

from .logger_config import logger


class Particle:
    """Small particle for additional visual interest."""

    def __init__(self, center_x: float, center_y: float, size: int = 4) -> None:
        self.x = center_x + random.uniform(-50, 50)  # noqa: S311
        self.y = center_y + random.uniform(-50, 50)  # noqa: S311
        self.size = random.uniform(1, size)  # noqa: S311
        self.opacity = random.uniform(0.3, 0.7)  # noqa: S311
        self.lifetime = random.uniform(0.5, 1.5)  # Seconds  # noqa: S311
        self.age = 0

        # Movement
        self.speed = random.uniform(0.2, 1.0)  # noqa: S311
        self.angle = random.uniform(0, 2 * math.pi)  # noqa: S311
        self.dx = math.cos(self.angle) * self.speed
        self.dy = math.sin(self.angle) * self.speed

        # Color - subtle variations of blue
        r = max(0, min(255, 66 + random.randint(-20, 20)))  # noqa: S311
        g = max(0, min(255, 133 + random.randint(-20, 20)))  # noqa: S311
        b = max(0, min(255, 244 + random.randint(-20, 20)))  # noqa: S311
        self.color = QColor(r, g, b)

    def update(self, dt: float = 0.016) -> bool:
        """Update particle position and lifespan."""
        self.age += dt
        progress = self.age / self.lifetime

        if progress >= 1.0:
            return False

        # Move particle
        self.x += self.dx
        self.y += self.dy

        # Fade out as it ages
        self.opacity = 0.7 * (1.0 - progress)

        # Shrink over time
        self.size = (1 - progress) * random.uniform(1, 4)  # noqa: S311

        return True

    def draw(self, painter: QPainter) -> None:
        """Draw the particle."""
        if self.opacity <= 0.05:  # noqa: PLR2004
            return

        self.color.setAlphaF(self.opacity)
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(self.x, self.y), self.size, self.size)


class PulseCircle:
    """Circle that pulses for visual feedback during processing."""

    def __init__(
        self, size: int = 60, max_size: int = 120, duration: int = 1000
    ) -> None:
        """Initialize a pulse circle.

        Args:
            size: Initial size of the circle in pixels
            max_size: Maximum size the circle will expand to
            duration: Time in ms for a complete pulse cycle
        """
        self.initial_size = size
        self.max_size = max_size
        self.size = size
        self.opacity = 0.8
        self.progress = 0.0
        self.speed = 1.0 / duration * 16  # 16ms is roughly one frame at 60fps

        # Add rotation
        self.rotation = random.uniform(0, 360)  # noqa: S311
        self.rotation_speed = random.uniform(-0.5, 0.5)  # noqa: S311

        # Trail effect
        self.trail_positions = []
        self.max_trail_length = 5

        # Color variations
        r = max(0, min(255, 66 + random.randint(-10, 10)))  # noqa: S311
        g = max(0, min(255, 133 + random.randint(-10, 10)))  # noqa: S311
        b = max(0, min(255, 244 + random.randint(-10, 10)))  # noqa: S311
        self.color = QColor(r, g, b)

        # Secondary accent color (for gradient)
        self.accent_color = QColor(min(255, r + 40), min(255, g + 30), min(255, b + 20))

    def update(self) -> bool:
        """Update the circle's size and opacity based on animation progress."""
        self.progress += self.speed

        if self.progress >= 1.0:
            self.progress = 0.0
            self.trail_positions = []  # Reset trail
            return False  # Animation complete

        # Calculate size and opacity using easing function
        t = self.progress
        # Ease-out cubic function for smoother animation
        t = 1.0 - (1.0 - t) * (1.0 - t) * (1.0 - t)

        # Store current position for trail (each 3rd frame)
        if (
            random.random() < 0.3  # noqa: S311, PLR2004
            and len(self.trail_positions) < self.max_trail_length
        ):
            prev_size = self.size
            self.size = self.initial_size + (self.max_size - self.initial_size) * t

            # Only store if significant change
            if abs(self.size - prev_size) > 1.0:
                self.trail_positions.append((self.size, self.opacity))
        else:
            self.size = self.initial_size + (self.max_size - self.initial_size) * t

        self.opacity = 0.9 * (1.0 - t * 0.8)  # Fade out more slowly

        # Update rotation
        self.rotation += self.rotation_speed

        return True  # Animation still running

    def draw(self, painter: QPainter, center_x: float, center_y: float) -> None:
        """Draw the pulse circle on the provided painter."""
        if self.opacity <= 0.05:  # noqa: PLR2004
            return

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation)

        # Draw trail first (behind the main circle)
        for i, (trail_size, trail_opacity) in enumerate(self.trail_positions):
            # Decrease opacity for older trail positions
            fade_factor = 0.5 * (1.0 - i / len(self.trail_positions))
            trail_alpha = int(trail_opacity * fade_factor * 255)

            # Create a copy of colors with adjusted opacity
            trail_color = QColor(self.color)
            trail_color.setAlpha(trail_alpha)

            trail_accent = QColor(self.accent_color)
            trail_accent.setAlpha(trail_alpha)

            # Draw trail circle with gradient
            gradient = QRadialGradient(0, 0, trail_size / 2)
            gradient.setColorAt(0, trail_accent)
            gradient.setColorAt(0.7, trail_color)
            gradient.setColorAt(
                1, QColor(trail_color.red(), trail_color.green(), trail_color.blue(), 0)
            )

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(0, 0), trail_size / 2, trail_size / 2)

        # Draw main circle with gradient
        main_color = QColor(self.color)
        main_color.setAlpha(int(self.opacity * 255))

        accent_color = QColor(self.accent_color)
        accent_color.setAlpha(int(self.opacity * 255))

        # Create gradient
        gradient = QRadialGradient(0, 0, self.size / 2)
        gradient.setColorAt(0, accent_color)
        gradient.setColorAt(0.7, main_color)
        gradient.setColorAt(
            1, QColor(main_color.red(), main_color.green(), main_color.blue(), 0)
        )

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)

        radius = self.size / 2
        painter.drawEllipse(QPointF(0, 0), radius, radius)

        # Add a subtle ring
        if self.opacity > 0.3:  # noqa: PLR2004
            ring_pen = QPen(main_color)
            ring_pen.setWidth(2)
            painter.setPen(ring_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(0, 0), radius * 1.05, radius * 1.05)

        painter.restore()


class MagicAnimationWindow(QWidget):
    """Window of animation visual displayed during processing.

    Shows a clean pulse animation following the cursor.
    """

    # Signal for communication with main thread
    animation_finished = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the animation window."""
        super().__init__(parent)
        logger.info("Initializing MagicAnimationWindow...")

        self.setWindowTitle("Texta AI Processing...")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.resize(200, 200)  # Slightly larger window for the enhanced effects

        self.state = "idle"  # idle, processing, closing

        # Pulse circles with different delays for continuous effect
        self.circles = []
        self.max_circles = 3  # 3 circles with staggered timing

        # Add particles for extra visual interest
        self.particles = []
        self.max_particles = 15

        # Timer for the animation loop
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_animation_frame)

        # Timer for following the cursor
        self.position_timer = QTimer(self)
        self.position_timer.setInterval(16)  # Update roughly 60 times per second
        self.position_timer.timeout.connect(self._update_position)

        # Frame timing
        self.last_frame_time = time.time()

        logger.info("MagicAnimationWindow initialized.")

    @Slot()
    def start_effect(self) -> None:
        """Start the processing animation effect and cursor following."""
        logger.info("Starting processing animation effect and cursor following.")
        self.state = "processing"
        self.circles = []
        self.particles = []

        # Create circles with staggered start times
        for i in range(self.max_circles):
            circle = PulseCircle(
                size=20,  # Start small
                max_size=120,  # Grow to this size
                duration=1800,  # Complete cycle in 1.8 seconds (slower for more elegance)
            )
            # Stagger the starting progress to create continuous effect
            circle.progress = i * (1.0 / self.max_circles)
            self.circles.append(circle)

        if not self.animation_timer.isActive():
            self.last_frame_time = time.time()
            self.animation_timer.start(16)  # ~60fps

        if not self.position_timer.isActive():
            self._update_position()  # Position immediately
            self.position_timer.start()

        self.show()

    @Slot()
    def force_close(self) -> None:
        """Force the animation window to hide and stop following the cursor."""
        logger.info("Forcing animation window hide and stopping cursor following.")
        self.state = "closing"
        self.animation_timer.stop()
        self.position_timer.stop()  # Stop following the cursor
        self.hide()  # Hide instead of close to allow reuse

    def _update_animation_frame(self) -> None:
        """Update a frame of the animation."""
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time

        if self.state == "processing":
            # Update all pulse circles
            for circle in self.circles:
                if not circle.update():
                    # If a circle completes its animation, reset it for continuous effect
                    circle.progress = 0.0

            # Update existing particles
            self.particles = [p for p in self.particles if p.update(dt)]

            # Occasionally add new particles
            center_x = self.width() / 2
            center_y = self.height() / 2

            if (
                len(self.particles) < self.max_particles
                and random.random() < 0.1  # noqa: S311, PLR2004
            ):
                self.particles.append(Particle(center_x, center_y))

        self.update()  # Trigger paintEvent

    def _update_position(self) -> None:
        """Update the position of the window to follow the cursor."""
        if not QApplication.instance():
            return

        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if not screen:
            screen = QApplication.primaryScreen()
            if not screen:
                return

        window_width = self.width()
        window_height = self.height()

        # Center the window on the cursor
        target_x = cursor_pos.x() - window_width / 2
        target_y = cursor_pos.y() - window_height / 2

        # Keep the window within screen bounds
        screen_geometry = screen.availableGeometry()
        target_x = max(
            screen_geometry.left(),
            min(target_x, screen_geometry.right() - window_width),
        )
        target_y = max(
            screen_geometry.top(),
            min(target_y, screen_geometry.bottom() - window_height),
        )

        # Move the window only if needed
        if self.pos().x() != int(target_x) or self.pos().y() != int(target_y):
            self.move(int(target_x), int(target_y))

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002, N802
        """Draw the animation content."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the center point of the window
        center_x = self.width() / 2
        center_y = self.height() / 2

        # Draw particles first (background layer)
        for particle in self.particles:
            particle.draw(painter)

        # Draw pulse circles
        for circle in self.circles:
            circle.draw(painter, center_x, center_y)

    def closeEvent(self, event: QEvent) -> None:  # noqa: N802
        """Called when the window is about to close."""
        logger.info("MagicAnimationWindow hiding/closing.")
        self.animation_timer.stop()
        self.animation_finished.emit()  # Signal that animation is finished
        super().closeEvent(event)


if __name__ == "__main__":
    # Quick test of the animation window
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = QApplication(sys.argv)

    # Test the animation window
    test_window = MagicAnimationWindow()
    test_window.start_effect()

    # Close after 5 seconds to see the full effect
    QTimer.singleShot(5000, test_window.force_close)

    sys.exit(app.exec())
