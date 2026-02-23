#!/usr/bin/env python3
"""
Bench my DNS - Fixed Version
Per-server averages, working security cards, modern scrollbars
"""

import os
import sys

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

import csv
import random
import statistics
import string
import time
import warnings
from dataclasses import dataclass

import dns.message
import dns.query
import dns.rdatatype
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

warnings.filterwarnings("ignore")


class DrawArrowButton(QWidget):
    """
    Lightweight arrow button implemented as a QWidget to avoid any native button chrome.
    Emits a `clicked` signal when mouse is released inside. Supports 'up' and 'down'
    directions and hover/disabled visual states.
    """

    clicked = pyqtSignal()

    def __init__(self, direction="up", parent=None):
        super().__init__(parent)
        self.direction = direction  # 'up' or 'down'
        self._hover = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(18, 16)
        # enable hover events
        try:
            self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        except Exception:
            # older Qt compatibility fallback — not fatal
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # choose color based on state
        if not self.isEnabled():
            color = QColor(0, 0, 0, 64)
        elif self._hover:
            color = QColor("#0D47A1")  # slightly darker on hover
        else:
            color = QColor("#1565C0")

        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)

        w = float(self.width())
        h = float(self.height())
        path = QPainterPath()

        if self.direction == "up":
            path.moveTo(w * 0.5, h * 0.20)
            path.lineTo(w * 0.85, h * 0.80)
            path.lineTo(w * 0.15, h * 0.80)
            path.closeSubpath()
        else:
            path.moveTo(w * 0.15, h * 0.20)
            path.lineTo(w * 0.85, h * 0.20)
            path.lineTo(w * 0.50, h * 0.82)
            path.closeSubpath()

        painter.fillPath(path, painter.brush())

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(
            event.pos()
        ):
            # emit clicked and update visuals briefly (if needed)
            try:
                self.clicked.emit()
            except Exception:
                pass
        super().mouseReleaseEvent(event)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.update()


class ModernSpinWidget(QWidget):
    """
    Lightweight custom spin widget with modern arrow buttons that avoids native platform
    up/down controls. Implements a small subset of QSpinBox/QDoubleSpinBox API used
    in this project:
      - value()
      - setValue(v)
      - setRange(min, max)
      - setSingleStep(step)
      - setDecimals(d) (for double mode)
    Construct with:
      ModernSpinWidget(minimum=..., maximum=..., value=..., is_double=False, step=1)
    """

    def __init__(
        self, minimum=0, maximum=100, value=0, is_double=False, step=1, parent=None
    ):
        super().__init__(parent)
        self._is_double = bool(is_double)
        self._min = minimum
        self._max = maximum
        self._step = step
        self._decimals = 1 if self._is_double else 0

        self._line = QLineEdit(self)
        self._line.setText(str(value))
        self._line.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._line.setFixedHeight(30)
        # reduce minimum width so widget is more compact
        self._line.setMinimumWidth(48)
        # Ensure the text is visible and selection matches the app theme
        self._line.setStyleSheet(
            "QLineEdit {"
            " color: #333333;"
            " background: transparent;"
            " border: none;"
            " padding: 4px;"
            " font-size: 13px;"
            " selection-background-color: #1565C0;"
            " selection-color: white;"
            "}"
        )

        # Use DrawArrowButton which paints the arrow directly (no SVG data URIs)
        self._up = DrawArrowButton("up", self)
        self._down = DrawArrowButton("down", self)

        # Layout: place line edit left, buttons stacked vertically on right
        layout = QHBoxLayout(self)
        # slightly tighter margins to reduce overall control width
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)
        layout.addWidget(self._line)
        btns = QVBoxLayout()
        btns.setContentsMargins(0, 0, 0, 0)
        btns.setSpacing(2)
        btns.addWidget(self._up)
        btns.addWidget(self._down)
        layout.addLayout(btns)

        # Make the whole widget compact and fixed width so it doesn't stretch too much
        try:
            self.setFixedWidth(110)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        except Exception:
            # gracefully ignore if size policy constants differ on older Qt
            pass

        # Initialize values
        self.setRange(self._min, self._max)
        self.setSingleStep(self._step)
        self.setValue(value)

        # Connections
        self._up.clicked.connect(lambda: self._step_value(1))
        self._down.clicked.connect(lambda: self._step_value(-1))
        self._line.editingFinished.connect(self._on_edit_finished)

        # Make widget look like the other spinboxes
        self.setStyleSheet(
            "ModernSpinWidget { background-color: white; border: 1px solid #E0E0E0; border-radius: 6px; }"
        )

    def _on_edit_finished(self):
        text = self._line.text().strip()
        try:
            if self._is_double:
                val = float(text)
            else:
                val = int(float(text))
        except:
            val = self._min
        self.setValue(val)

    def _clamp(self, v):
        if v is None:
            return self._min
        if self._is_double:
            v = float(v)
            if v < self._min:
                return float(self._min)
            if v > self._max:
                return float(self._max)
            return v
        else:
            v = int(round(float(v)))
            if v < self._min:
                return int(self._min)
            if v > self._max:
                return int(self._max)
            return v

    def _step_value(self, direction):
        try:
            cur = self.value()
        except:
            cur = self._min
        newv = cur + (self._step * direction)
        self.setValue(newv)

    def value(self):
        text = self._line.text().strip()
        try:
            if self._is_double:
                return float(text)
            else:
                return int(round(float(text)))
        except:
            return self._min

    def setValue(self, v):
        v = self._clamp(v)
        if self._is_double:
            fmt = f"{{:.{self._decimals}f}}"
            self._line.setText(fmt.format(v))
        else:
            self._line.setText(str(int(round(float(v)))))

    def setRange(self, minimum, maximum):
        self._min = minimum
        self._max = maximum
        # adjust current value if outside
        try:
            self.setValue(self.value())
        except:
            self.setValue(self._min)

    def setSingleStep(self, step):
        self._step = step

    def setDecimals(self, d):
        if self._is_double:
            self._decimals = int(d)

    def setEnabled(self, en: bool):
        super().setEnabled(en)
        self._line.setEnabled(en)
        self._up.setEnabled(en)
        self._down.setEnabled(en)


# New: PopupList and SimpleCombo - fully custom combobox-like widget so we avoid
# platform popup chrome, blue focus box and other native artifacts.
from PyQt6.QtCore import QModelIndex, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QFrame, QPushButton


class PopupList(QFrame):
    """
    Fully custom-painted popup list (no QListWidget) to avoid any OS-native chrome.
    - Paints items directly for full control over visuals.
    - Emits `activated(index)` when an item is clicked.
    - Supports hover highlighting and wheel scrolling.
    """

    activated = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(
            parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)
        # Keep a minimal stylesheet for the frame itself; item visuals are painted manually.
        self.setStyleSheet("""
            QFrame { background-color: white; border: 1px solid #E0E0E0; border-radius: 8px; }
        """)
        self._items = []
        self._hover_index = -1
        self._item_height = 36
        self._padding_v = 6
        self._padding_h = 10
        self._vscroll = 0  # vertical pixel scroll offset
        self.setMouseTracking(True)
        self.setMinimumWidth(120)
        self._max_visible_items = 8

    def addItems(self, items):
        # Replace items and reset state
        self._items = list(items)
        self._hover_index = -1
        self._vscroll = 0
        # compute a reasonable width based on longest item
        fm = QFontMetrics(self.font())
        max_w = 0
        for it in self._items:
            w = fm.horizontalAdvance(it)
            if w > max_w:
                max_w = w
        content_w = max_w + self._padding_h * 2
        # width should be at least current width; allow caller to resize parent if needed
        self.setMinimumWidth(content_w + 8)
        # height based on visible items but clamp to max_visible
        visible = min(len(self._items), self._max_visible_items)
        total_h = visible * self._item_height + self._padding_v * 2
        self.setFixedHeight(total_h)
        self.update()

    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        # Background and border: the stylesheet provides background; draw items on top.
        content_rect = QRect(
            rect.left() + 0,
            rect.top() + self._padding_v,
            rect.width(),
            rect.height() - self._padding_v * 2,
        )

        # Determine visible item range based on _vscroll
        start_pixel = self._vscroll
        first_index = max(0, start_pixel // self._item_height)
        y_offset = -(start_pixel % self._item_height)

        fm = QFontMetrics(self.font())
        for i in range(first_index, len(self._items)):
            y = content_rect.top() + y_offset + (i - first_index) * self._item_height
            if y > rect.bottom():
                break

            item_rect = QRect(
                content_rect.left() + self._padding_h,
                y,
                content_rect.width() - self._padding_h * 2,
                self._item_height,
            )
            # Draw hover/selection background
            if i == self._hover_index:
                painter.setBrush(QBrush(QColor("#1565C0")))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(
                    QRect(
                        content_rect.left() + 6,
                        y + 4,
                        content_rect.width() - 12,
                        self._item_height - 8,
                    ),
                    6,
                    6,
                )
                painter.setPen(QColor("#FFFFFF"))
            else:
                painter.setPen(QColor("#333333"))

            # Draw text vertically centered
            text_y = y + (self._item_height + fm.ascent() - fm.descent()) // 2
            painter.drawText(item_rect.left(), text_y, self._items[i])

        painter.end()

    def _index_at_pos(self, pos):
        # pos is in local coordinates
        content_top = self._padding_v
        y = pos.y() + self._vscroll - content_top
        if y < 0:
            return -1
        idx = y // self._item_height
        if 0 <= idx < len(self._items):
            return int(idx)
        return -1

    def mouseMoveEvent(self, ev):
        idx = self._index_at_pos(ev.position().toPoint())
        if idx != self._hover_index:
            self._hover_index = idx
            self.update()
        super().mouseMoveEvent(ev)

    def leaveEvent(self, ev):
        self._hover_index = -1
        self.update()
        super().leaveEvent(ev)

    def mousePressEvent(self, ev):
        idx = self._index_at_pos(ev.position().toPoint())
        if idx != -1:
            try:
                self.activated.emit(int(idx))
            except Exception:
                pass
            self.hide()
        super().mousePressEvent(ev)

    def wheelEvent(self, ev):
        # Vertical wheel scroll: adjust _vscroll (in pixels) and clamp
        delta = int(ev.angleDelta().y() / 8)  # degrees
        # convert degrees to pixels (rough)
        pixels = int(delta * 0.5)
        max_scroll = max(
            0,
            len(self._items) * self._item_height - self.height() + self._padding_v * 2,
        )
        self._vscroll = max(0, min(self._vscroll - pixels, max_scroll))
        self.update()
        ev.accept()

    def show_at(self, widget):
        # position directly below widget (or above if not enough space)
        geo = widget.geometry()
        global_pos = widget.mapToGlobal(geo.topLeft())
        x = global_pos.x()
        y = global_pos.y() + geo.height()
        # try to fit below screen bounds if possible; fallback above
        desktop = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        # ensure width at least as wide as widget
        if self.width() < widget.width():
            self.setFixedWidth(widget.width())
        # if not enough space below, show above
        if (
            y + self.height() > desktop.bottom()
            and global_pos.y() - self.height() > desktop.top()
        ):
            y = global_pos.y() - self.height()
        self.move(x, y)
        self.show()


class ArrowWidget(QWidget):
    """
    Small triangle-only widget used inside the SimpleCombo button.
    Paints a downward triangle and keeps a transparent background so no
    rounded button chrome shows behind it.
    """

    def __init__(self, parent=None, color="#1565C0"):
        super().__init__(parent)
        self._color = QColor(color)
        # Make background transparent so only our triangle is visible.
        try:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        except Exception:
            pass
        self.setFixedSize(16, 16)
        # This widget should not capture mouse events (button handles clicks).
        try:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        except Exception:
            pass

    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = self._color if self.isEnabled() else QColor(0, 0, 0, 64)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        w = float(self.width())
        h = float(self.height())
        path = QPainterPath()
        # downward triangle
        path.moveTo(w * 0.2, h * 0.4)
        path.lineTo(w * 0.8, h * 0.4)
        path.lineTo(w * 0.5, h * 0.7)
        path.closeSubpath()
        painter.fillPath(path, painter.brush())
        painter.end()


class SimpleCombo(QWidget):
    """
    Replacement for QComboBox for this app's use:
    - Renders a rounded white control with label text and a small triangular arrow on the right.
    - Uses PopupList as the popup to avoid OS chrome.
    - Exposes `currentIndex()` and `currentText()` and a `currentIndexChanged(int)` signal.
    """

    currentIndexChanged = pyqtSignal(int)

    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self.items = items or []
        self._index = 0

        self._btn = QPushButton(self)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 36px 8px 12px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
                color: #333333;
                font-size: 13px;
            }
            QPushButton:focus { border-color: #0D47A1; }
        """)
        self._btn.clicked.connect(self._toggle_popup)

        # draw the small arrow on the button via a dedicated ArrowWidget so no
        # rounded button background shows behind it.
        self._arrow = ArrowWidget(self._btn, color="#1565C0")
        # position will be adjusted in resizeEvent
        self._arrow.show()

        self._popup = PopupList(self)
        if self.items:
            self._popup.addItems(self.items)
        self._popup.activated.connect(self._on_activated)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._btn)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        # position arrow inside button
        self._arrow.move(
            self._btn.width() - 28, (self._btn.height() - self._arrow.height()) // 2
        )

    def paintEvent(self, ev):
        # Nothing special here — the ArrowWidget child paints the triangle itself.
        super().paintEvent(ev)

    def _toggle_popup(self):
        if self._popup.isVisible():
            self._popup.hide()
        else:
            # refresh items
            self._popup.addItems(self.items)
            self._popup.show_at(self._btn)

    def addItems(self, items):
        self.items = list(items)
        self._popup.addItems(self.items)
        if self.items and self._index >= len(self.items):
            self._index = 0
        self._update_button_text()

    def _update_button_text(self):
        text = self.items[self._index] if self.items else ""
        self._btn.setText(text)

    def currentIndex(self):
        return int(self._index)

    def currentText(self):
        return self.items[self._index] if self.items else ""

    def setCurrentIndex(self, idx):
        if 0 <= idx < len(self.items):
            self._index = idx
            self._update_button_text()
            self.currentIndexChanged.emit(self._index)

    def _on_activated(self, idx):
        self.setCurrentIndex(idx)


@dataclass
class ServerResult:
    name: str
    ip: str
    cached_avg: float = 0
    uncached_avg: float = 0
    overall_avg: float = 0
    min_time: float = 0
    max_time: float = 0
    reliability: float = 0
    total_queries: int = 0
    successful: int = 0


DNS_SERVERS = {
    "Google": "8.8.8.8",
    "Google Secondary": "8.8.4.4",
    "Cloudflare": "1.1.1.1",
    "Cloudflare Secondary": "1.0.0.1",
    "Cloudflare Malware": "1.1.1.2",
    "Cloudflare Family": "1.1.1.3",
    "Quad9": "9.9.9.9",
    "Quad9 Secondary": "149.112.112.112",
    "Quad9 Unsecured": "9.9.9.10",
    "OpenDNS": "208.67.222.222",
    "OpenDNS Secondary": "208.67.220.220",
    "OpenDNS Family": "208.67.222.123",
    "NextDNS": "45.90.28.0",
    "NextDNS Secondary": "45.90.30.0",
    "AdGuard": "94.140.14.14",
    "AdGuard Secondary": "94.140.15.15",
    "AdGuard Family": "94.140.14.15",
    "CleanBrowsing": "185.228.168.9",
    "CleanBrowsing Adult": "185.228.168.10",
    "CleanBrowsing Family": "185.228.168.168",
    "Level3": "4.2.2.1",
    "Level3 Alt 1": "4.2.2.2",
    "Level3 Alt 2": "4.2.2.3",
    "Level3 Alt 3": "4.2.2.4",
    "Verisign": "64.6.64.6",
    "Verisign Secondary": "64.6.65.6",
    "DNS.WATCH": "84.200.69.80",
    "DNS.WATCH Secondary": "84.200.70.40",
    "Comodo Secure": "8.26.56.26",
    "Comodo Secondary": "8.20.247.20",
    "Yandex": "77.88.8.8",
    "Yandex Secondary": "77.88.8.1",
    "Hurricane Electric": "74.82.42.42",
    "Neustar": "156.154.70.1",
    "Neustar Secondary": "156.154.71.1",
    "Alternate DNS": "76.76.19.19",
    "Alternate Secondary": "76.223.122.150",
    "Control D": "76.76.2.0",
    "Control D Secondary": "76.76.10.0",
    "Mullvad": "194.242.2.2",
    "Mullvad Secondary": "193.19.108.2",
    "Oracle Dyn": "216.146.35.35",
    "Dyn Secondary": "216.146.36.36",
}


class BenchThread(QThread):
    progress = pyqtSignal(int, str)
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, servers, query_count):
        super().__init__()
        self.servers = servers
        self.query_count = query_count
        self._is_running = True

    def run(self):
        results = []
        total = len(self.servers)

        try:
            for idx, (name, ip) in enumerate(self.servers.items()):
                if not self._is_running:
                    break

                try:
                    progress_val = int((idx / total) * 100)
                    self.progress.emit(progress_val, f"Testing {name}...")
                except:
                    pass

                try:
                    result = self.test_single_server(name, ip)
                    results.append(result)
                except Exception as e:
                    print(f"Error testing {name}: {e}")
                    results.append(ServerResult(name=name, ip=ip))

            if self._is_running:
                try:
                    self.progress.emit(100, "Complete!")
                    self.finished_signal.emit(results)
                except Exception as e:
                    self.error_signal.emit(str(e))

        except Exception as e:
            self.error_signal.emit(str(e))

    def test_single_server(self, name, ip):
        cached_times = []
        uncached_times = []

        try:
            for i in range(self.query_count):
                if not self._is_running:
                    break
                try:
                    query = dns.message.make_query("google.com", "A")
                    start = time.perf_counter()
                    dns.query.udp(query, ip, timeout=2.0)
                    elapsed = (time.perf_counter() - start) * 1000
                    if elapsed > 0:
                        cached_times.append(elapsed)
                except:
                    pass

            for i in range(self.query_count):
                if not self._is_running:
                    break
                try:
                    domain = (
                        f"{''.join(random.choices(string.ascii_lowercase, k=8))}.com"
                    )
                    query = dns.message.make_query(domain, "A")
                    start = time.perf_counter()
                    dns.query.udp(query, ip, timeout=2.0)
                    elapsed = (time.perf_counter() - start) * 1000
                    if elapsed > 0:
                        uncached_times.append(elapsed)
                except:
                    pass

            all_times = cached_times + uncached_times
            cached_avg = statistics.mean(cached_times) if cached_times else 0
            uncached_avg = statistics.mean(uncached_times) if uncached_times else 0
            overall_avg = (
                (cached_avg + uncached_avg) / 2
                if cached_avg and uncached_avg
                else max(cached_avg, uncached_avg)
            )

            return ServerResult(
                name=name,
                ip=ip,
                cached_avg=cached_avg,
                uncached_avg=uncached_avg,
                overall_avg=overall_avg,
                min_time=min(all_times) if all_times else 0,
                max_time=max(all_times) if all_times else 0,
                reliability=(len(all_times) / (self.query_count * 2) * 100)
                if self.query_count
                else 0,
                total_queries=self.query_count * 2,
                successful=len(all_times),
            )
        except Exception as e:
            print(f"Server test error: {e}")
            return ServerResult(name=name, ip=ip)

    def stop(self):
        self._is_running = False


class SecurityThread(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(str, str)
    finished_signal = pyqtSignal()

    def __init__(self, servers):
        super().__init__()
        self.servers = servers
        self._is_running = True

    def run(self):
        try:
            for i, (name, ip) in enumerate(self.servers.items()):
                if not self._is_running:
                    break

                status = "error"
                try:
                    query = dns.message.make_query(
                        "cloudflare.com", dns.rdatatype.DNSKEY
                    )
                    query.want_dnssec(True)
                    response = dns.query.udp(query, ip, timeout=2.0)
                    has_dnskey = any(
                        rrset.rdtype == dns.rdatatype.DNSKEY
                        for rrset in response.answer
                    )
                    has_rrsig = any(
                        rrset.rdtype == dns.rdatatype.RRSIG for rrset in response.answer
                    )
                    status = (
                        "valid" if has_rrsig else "signed" if has_dnskey else "unsigned"
                    )
                except:
                    status = "error"

                try:
                    self.result.emit(name, status)
                    self.progress.emit(int((i + 1) / len(self.servers) * 100))
                except:
                    pass

            self.finished_signal.emit()
        except:
            self.finished_signal.emit()

    def stop(self):
        self._is_running = False


class ResultsChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = []
        self.max_val = 100
        self.setMinimumHeight(500)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_results(self, results):
        self.results = results
        if results:
            all_vals = []
            for r in results:
                if r.cached_avg > 0:
                    all_vals.append(r.cached_avg)
                if r.uncached_avg > 0:
                    all_vals.append(r.uncached_avg)
                if r.overall_avg > 0:
                    all_vals.append(r.overall_avg)
            if all_vals:
                self.max_val = max(max(all_vals) * 1.2, 50)

        height = max(600, len(results) * 65 + 100)
        self.setMinimumHeight(height)
        self.update()

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.results:
            painter.setPen(QColor("#333333"))
            font = QFont("Segoe UI", 14)
            painter.setFont(font)
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Click START BENCHMARK to begin",
            )
            return

        left_margin = 180
        right_margin = 30
        top_margin = 40
        bar_height = 16
        spacing = 58

        chart_width = self.width() - left_margin - right_margin

        painter.setPen(QPen(QColor("#E8E8E8"), 1))
        for j in range(7):
            x = left_margin + (chart_width * j / 6)
            painter.drawLine(
                int(x),
                top_margin - 10,
                int(x),
                top_margin + len(self.results) * spacing,
            )
            painter.setPen(QColor("#999999"))
            font = QFont("Segoe UI", 9)
            painter.setFont(font)
            val = self.max_val * j / 6
            painter.drawText(
                int(x) - 25,
                top_margin - 15,
                50,
                20,
                Qt.AlignmentFlag.AlignCenter,
                f"{val:.0f}",
            )
            painter.setPen(QPen(QColor("#E8E8E8"), 1))

        for i, result in enumerate(self.results):
            y = top_margin + i * spacing

            painter.setPen(QColor("#212121"))
            font = QFont("Segoe UI", 11, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(
                10,
                y,
                left_margin - 15,
                22,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                result.name,
            )

            font = QFont("Segoe UI", 9)
            painter.setFont(font)
            painter.setPen(QColor("#888888"))
            painter.drawText(
                10,
                y + 20,
                left_margin - 15,
                16,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                result.ip,
            )

            if result.cached_avg > 0:
                width = min(
                    (result.cached_avg / self.max_val) * chart_width, chart_width
                )
                painter.fillRect(
                    left_margin, y + 6, int(width), bar_height, QColor("#4CAF50")
                )

            if result.uncached_avg > 0:
                width = min(
                    (result.uncached_avg / self.max_val) * chart_width, chart_width
                )
                painter.fillRect(
                    left_margin, y + 36, int(width), bar_height, QColor("#F44336")
                )

            if result.overall_avg > 0:
                avg_width = min(
                    (result.overall_avg / self.max_val) * chart_width, chart_width
                )
                # Center the average line between cached bar (y+6 to y+22) and uncached bar (y+36 to y+52)
                # Center point = (22 + 36) / 2 = 29, so y + 29
                avg_y = y + 29
                painter.setPen(QPen(QColor("#1565C0"), 3))
                painter.drawLine(
                    left_margin, avg_y, int(left_margin + avg_width), avg_y
                )
                painter.setPen(QColor("#1565C0"))
                font = QFont("Segoe UI", 9, QFont.Weight.Bold)
                painter.setFont(font)
                avg_text = f"{result.overall_avg:.1f}"
                text_x = int(left_margin + avg_width) + 5
                if text_x + 35 > self.width() - right_margin:
                    text_x = int(left_margin + avg_width) - 40
                painter.drawText(
                    text_x, avg_y - 8, 35, 18, Qt.AlignmentFlag.AlignLeft, avg_text
                )

            dot_x = self.width() - 18
            dot_y = y + 22
            if result.reliability > 95:
                painter.setBrush(QBrush(QColor("#4CAF50")))
            elif result.reliability > 80:
                painter.setBrush(QBrush(QColor("#FF9800")))
            else:
                painter.setBrush(QBrush(QColor("#F44336")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(dot_x, dot_y, 10, 10)

        painter.setPen(QColor("#666666"))
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.drawText(
            left_margin,
            top_margin + len(self.results) * spacing + 25,
            "Response Time (ms)",
        )

        legend_y = top_margin + len(self.results) * spacing + 50
        painter.fillRect(left_margin, legend_y, 20, 12, QColor("#4CAF50"))
        painter.setPen(QColor("#333333"))
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.drawText(
            left_margin + 25, legend_y - 2, 60, 16, Qt.AlignmentFlag.AlignLeft, "Cached"
        )

        painter.fillRect(left_margin + 100, legend_y, 20, 12, QColor("#F44336"))
        painter.drawText(
            left_margin + 125,
            legend_y - 2,
            80,
            16,
            Qt.AlignmentFlag.AlignLeft,
            "Uncached",
        )

        painter.setPen(QPen(QColor("#1565C0"), 3))
        painter.drawLine(
            left_margin + 210, legend_y + 5, left_margin + 230, legend_y + 5
        )
        painter.setPen(QColor("#333333"))
        painter.drawText(
            left_margin + 235,
            legend_y - 2,
            60,
            16,
            Qt.AlignmentFlag.AlignLeft,
            "Average",
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bench my DNS")
        self.setMinimumSize(1400, 900)

        self.results = []
        self.filtered_results = []
        self.bench_thread = None
        self.sec_thread = None

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #1565C0;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(25, 18, 25, 18)

        title = QLabel("Bench my DNS")
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background-color: transparent;")
        hl.addWidget(title)

        st = QLabel("Find your fastest DNS server")
        st.setStyleSheet(
            "color: #E3F2FD; font-size: 14px; background-color: transparent;"
        )
        hl.addWidget(st)
        hl.addStretch()

        layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.create_run_tab()
        self.create_results_tab()
        self.create_security_tab()
        layout.addWidget(self.tabs)

        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet(
            "background-color: #424242; color: white; font-size: 12px;"
        )

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #FAFAFA; }
            QWidget { background-color: #FAFAFA; font-family: 'Segoe UI'; }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: none;
                background-color: transparent;
                margin-top: 0px;
                padding: 0px;
                color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: padding;
                left: 0px;
                padding: 0px;
                color: #333333;
                background-color: transparent;
            }
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #0D47A1; }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: #9E9E9E;
            }
            QCheckBox {
                color: #333333;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #BDBDBD;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }
            QCheckBox::indicator:hover {
                border-color: #9E9E9E;
            }
            QSpinBox, QDoubleSpinBox {
                color: #333333;
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                min-width: 60px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus { border-color: #1565C0; }

            /* Hide native spinbox up/down buttons completely.
               ModernSpinWidget provides its own arrow buttons so native controls are removed. */
            QSpinBox::up-button, QSpinBox::down-button,
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 0px;
                height: 0px;
                border: none;
                background: transparent;
            }

            QComboBox {
                color: #333333;
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px 30px 8px 12px;
                font-size: 13px;
                min-width: 120px;
            }
            QComboBox:focus, QComboBox:hover { border-color: #1565C0; }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 30px;
                border: none;
                background: transparent;
            }
            /* Use a subtle triangular down-arrow that matches theme */
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 8px solid #1565C0;
            }
            /* Dropdown list (popup) styling - keep it simple and let the view handle window flags */
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                selection-background-color: #1565C0;
                selection-color: white;
                padding: 6px;
                outline: none;
            }
            QLabel { color: #333333; font-size: 13px; background: transparent; }
            QProgressBar {
                border: none;
                border-radius: 8px;
                text-align: center;
                height: 22px;
                color: white;
                font-weight: 600;
                font-size: 11px;
                background-color: #E0E0E0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 8px;
            }
            QScrollArea { border: none; background-color: transparent; }
            QTabWidget::pane { border: none; background-color: #FAFAFA; top: -1px; }
            QTabBar::tab {
                padding: 12px 24px;
                background-color: transparent;
                color: #666666;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-bottom: 3px solid transparent;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                color: #1565C0;
                border-bottom: 3px solid #1565C0;
            }
            QTabBar::tab:hover:!selected { color: #1565C0; }
            QScrollBar:vertical {
                background-color: transparent;
                width: 8px;
                margin: 4px 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #D0D0D0;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background-color: #BDBDBD; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
            QScrollBar:horizontal {
                background-color: transparent;
                height: 8px;
                margin: 2px 4px;
            }
            QScrollBar::handle:horizontal {
                background-color: #D0D0D0;
                border-radius: 4px;
                min-width: 30px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
        """)

    def create_run_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(30)
        layout.setContentsMargins(30, 25, 30, 25)

        left = QVBoxLayout()

        title_label = QLabel("DNS Servers")
        title_label.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #333333; margin-bottom: 8px;"
        )
        left.addWidget(title_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(350)
        scroll.setStyleSheet(
            "QScrollArea { background-color: white; border: 1px solid #E0E0E0; border-radius: 8px; }"
        )

        container = QWidget()
        container.setStyleSheet("background-color: white;")
        cl = QVBoxLayout(container)
        cl.setSpacing(6)
        cl.setContentsMargins(12, 10, 12, 10)

        self.checkboxes = {}
        for name, ip in sorted(DNS_SERVERS.items()):
            cb = QCheckBox(f"{name}  ({ip})")
            cb.setChecked(True)
            self.checkboxes[name] = cb
            cl.addWidget(cb)

        cl.addStretch()
        scroll.setWidget(container)
        left.addWidget(scroll)

        bl = QHBoxLayout()
        bl.setSpacing(10)
        sa = QPushButton("Select All")
        sa.setStyleSheet(
            "background-color: #E8F5E9; color: #2E7D32; border: none; border-radius: 6px; padding: 8px 16px; font-size: 12px; font-weight: 600;"
        )
        sa.clicked.connect(
            lambda: [c.setChecked(True) for c in self.checkboxes.values()]
        )
        da = QPushButton("Deselect All")
        da.setStyleSheet(
            "background-color: #FFEBEE; color: #C62828; border: none; border-radius: 6px; padding: 8px 16px; font-size: 12px; font-weight: 600;"
        )
        da.clicked.connect(
            lambda: [c.setChecked(False) for c in self.checkboxes.values()]
        )
        bl.addWidget(sa)
        bl.addWidget(da)
        bl.addStretch()
        left.addLayout(bl)

        left.addStretch()
        layout.addLayout(left, 1)

        right = QVBoxLayout()

        settings_title = QLabel("Settings")
        settings_title.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #333333; margin-bottom: 12px;"
        )
        right.addWidget(settings_title)

        settings_card = QWidget()
        settings_card.setStyleSheet(
            "background-color: white; border: 1px solid #E0E0E0; border-radius: 8px; padding: 16px;"
        )
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setSpacing(14)
        settings_layout.setContentsMargins(16, 16, 16, 16)

        q_row = QHBoxLayout()
        q_label = QLabel("Queries per server:")
        q_label.setStyleSheet("color: #666666; font-size: 13px;")
        q_row.addWidget(q_label)
        # use ModernSpinWidget (modern arrows, consistent across platforms)
        self.query_spin = ModernSpinWidget(
            minimum=3, maximum=20, value=5, is_double=False, step=1
        )
        q_row.addWidget(self.query_spin)
        q_row.addStretch()
        settings_layout.addLayout(q_row)

        t_row = QHBoxLayout()
        t_label = QLabel("Timeout (seconds):")
        t_label.setStyleSheet("color: #666666; font-size: 13px;")
        t_row.addWidget(t_label)
        # use ModernSpinWidget with floating values
        self.timeout_spin = ModernSpinWidget(
            minimum=1.0, maximum=5.0, value=2.0, is_double=True, step=0.1
        )
        t_row.addWidget(self.timeout_spin)
        t_row.addStretch()
        settings_layout.addLayout(t_row)

        p_row = QHBoxLayout()
        p_label = QLabel("Protocols:")
        p_label.setStyleSheet("color: #666666; font-size: 13px;")
        p_row.addWidget(p_label)
        self.udp_check = QCheckBox("UDP")
        self.udp_check.setChecked(True)
        self.tcp_check = QCheckBox("TCP")
        self.tcp_check.setChecked(True)
        p_row.addWidget(self.udp_check)
        p_row.addWidget(self.tcp_check)
        p_row.addStretch()
        settings_layout.addLayout(p_row)

        right.addWidget(settings_card)

        right.addSpacing(16)

        progress_title = QLabel("Progress")
        progress_title.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #333333; margin-bottom: 8px;"
        )
        right.addWidget(progress_title)

        progress_card = QWidget()
        progress_card.setStyleSheet(
            "background-color: white; border: 1px solid #E0E0E0; border-radius: 8px;"
        )
        pl = QVBoxLayout(progress_card)
        pl.setContentsMargins(16, 16, 16, 16)
        pl.setSpacing(10)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        pl.addWidget(self.progress)

        self.prog_label = QLabel("Ready")
        self.prog_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prog_label.setStyleSheet("color: #888888; font-size: 12px;")
        pl.addWidget(self.prog_label)

        right.addWidget(progress_card)

        right.addSpacing(20)

        self.start_btn = QPushButton("START BENCHMARK")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 15px;
                font-weight: 700;
                padding: 14px 32px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:disabled { background-color: #BDBDBD; color: #9E9E9E; }
        """)
        self.start_btn.clicked.connect(self.start_benchmark)
        right.addWidget(self.start_btn)

        legend = QLabel("Green = Cached  |  Red = Uncached  |  Blue = Average")
        legend.setStyleSheet("color: #888888; font-size: 12px; padding: 8px;")
        legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.addWidget(legend)

        right.addStretch()
        layout.addLayout(right, 1)

        self.tabs.addTab(tab, "Run Test")

    def create_results_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.summary_label = QLabel("Run a benchmark to see results")
        self.summary_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1565C0;
                padding: 12px 20px;
                background-color: #E3F2FD;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.summary_label)

        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(15)

        sort_container = QWidget()
        sort_layout = QHBoxLayout(sort_container)
        sort_layout.setContentsMargins(15, 8, 15, 8)
        sort_layout.setSpacing(10)
        sort_container.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
                border-radius: 8px;
            }
        """)

        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet(
            "font-size: 13px; color: #666666; background: transparent;"
        )
        sort_layout.addWidget(sort_label)

        # Use our SimpleCombo replacement so we control popup and arrow completely
        self.filter_combo = SimpleCombo(
            [
                "Fastest (Cached)",
                "Fastest (Uncached)",
                "Fastest (Overall)",
                "Slowest First",
                "Most Reliable",
            ],
            self,
        )
        # wire signals similar to QComboBox API
        self.filter_combo.currentIndexChanged.connect(lambda idx: self.apply_filter())
        # set initial index if needed
        self.filter_combo.setCurrentIndex(0)
        sort_layout.addWidget(self.filter_combo)
        controls_layout.addWidget(sort_container)

        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_csv)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #388E3C; }
        """)
        controls_layout.addWidget(export_btn)

        export_json_btn = QPushButton("Export to JSON")
        export_json_btn.clicked.connect(self.export_json)
        export_json_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        controls_layout.addWidget(export_json_btn)

        controls_layout.addStretch()
        layout.addWidget(controls)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
            }
        """)

        self.chart = ResultsChart()
        scroll.setWidget(self.chart)
        layout.addWidget(scroll, 1)

        self.tabs.addTab(tab, "Results")

    def create_security_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel("DNSSEC Security Analysis")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1565C0;")
        layout.addWidget(title)

        desc = QLabel("Check if your DNS servers support DNSSEC validation")
        desc.setStyleSheet("color: #616161; font-size: 13px;")
        layout.addWidget(desc)

        self.sec_btn = QPushButton("Run DNSSEC Check")
        self.sec_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6F00;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 40px;
                border-radius: 8px;
                max-width: 300px;
            }
            QPushButton:hover { background-color: #E65100; }
        """)
        self.sec_btn.clicked.connect(self.run_security)
        layout.addWidget(self.sec_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.sec_prog = QProgressBar()
        self.sec_prog.setValue(0)
        self.sec_prog.setMaximumWidth(600)
        layout.addWidget(self.sec_prog, alignment=Qt.AlignmentFlag.AlignCenter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #FAFAFA; }")

        self.sec_container = QWidget()
        self.sec_container.setStyleSheet("background-color: #FAFAFA;")
        self.sec_layout = QVBoxLayout(self.sec_container)
        self.sec_layout.setSpacing(8)
        self.sec_layout.setContentsMargins(10, 10, 10, 10)
        scroll.setWidget(self.sec_container)

        layout.addWidget(scroll, 1)
        self.tabs.addTab(tab, "Security")

    def start_benchmark(self):
        try:
            servers = {
                n: ip for n, ip in DNS_SERVERS.items() if self.checkboxes[n].isChecked()
            }
            if not servers:
                QMessageBox.warning(
                    self, "Warning", "Please select at least one server!"
                )
                return

            self.start_btn.setEnabled(False)
            self.start_btn.setText("Running...")
            self.results = []

            if self.bench_thread and self.bench_thread.isRunning():
                self.bench_thread.stop()
                self.bench_thread.wait(2000)

            self.bench_thread = BenchThread(servers, self.query_spin.value())
            self.bench_thread.progress.connect(self.update_progress)
            self.bench_thread.finished_signal.connect(self.benchmark_done)
            self.bench_thread.error_signal.connect(self.benchmark_error)
            self.bench_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start: {str(e)}")
            self.start_btn.setEnabled(True)
            self.start_btn.setText("START BENCHMARK")

    def update_progress(self, pct, msg):
        self.progress.setValue(pct)
        self.prog_label.setText(msg)
        self.statusBar().showMessage(msg)

    def benchmark_done(self, results):
        try:
            self.results = results
            self.filtered_results = results
            self.start_btn.setEnabled(True)
            self.start_btn.setText("START BENCHMARK")

            if results:
                valid_results = [r for r in results if r.overall_avg > 0]
                if valid_results:
                    best = min(valid_results, key=lambda x: x.overall_avg)
                    total_q = sum(r.total_queries for r in valid_results)
                    total_s = sum(r.successful for r in valid_results)
                    rate = (total_s / total_q * 100) if total_q else 0
                    self.summary_label.setText(
                        f"Winner: {best.name} ({best.overall_avg:.1f}ms)  |  "
                        f"Tested: {len(valid_results)} servers  |  "
                        f"Success: {rate:.1f}%"
                    )

            self.apply_filter()
            self.tabs.setCurrentIndex(1)
            self.statusBar().showMessage("Benchmark complete!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error displaying results: {str(e)}")
            self.start_btn.setEnabled(True)
            self.start_btn.setText("START BENCHMARK")

    def benchmark_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"Benchmark failed: {error_msg}")
        self.start_btn.setEnabled(True)
        self.start_btn.setText("START BENCHMARK")

    def apply_filter(self):
        try:
            if not self.results:
                return

            sort_mode = self.filter_combo.currentIndex()

            if sort_mode == 0:
                self.filtered_results = sorted(
                    self.results,
                    key=lambda x: x.cached_avg if x.cached_avg > 0 else float("inf"),
                )
            elif sort_mode == 1:
                self.filtered_results = sorted(
                    self.results,
                    key=lambda x: x.uncached_avg
                    if x.uncached_avg > 0
                    else float("inf"),
                )
            elif sort_mode == 2:
                self.filtered_results = sorted(
                    self.results,
                    key=lambda x: x.overall_avg if x.overall_avg > 0 else float("inf"),
                )
            elif sort_mode == 3:
                self.filtered_results = sorted(
                    self.results,
                    key=lambda x: x.overall_avg if x.overall_avg > 0 else 0,
                    reverse=True,
                )
            elif sort_mode == 4:
                self.filtered_results = sorted(
                    self.results, key=lambda x: x.reliability, reverse=True
                )

            self.chart.set_results(self.filtered_results)
        except Exception as e:
            print(f"Filter error: {e}")

    def run_security(self):
        try:
            servers = {
                n: ip for n, ip in DNS_SERVERS.items() if self.checkboxes[n].isChecked()
            }
            if not servers:
                QMessageBox.warning(
                    self, "Warning", "Please select at least one server!"
                )
                return

            self.sec_btn.setEnabled(False)
            self.sec_prog.setValue(0)

            while self.sec_layout.count():
                child = self.sec_layout.takeAt(0)
                if child and child.widget():
                    child.widget().setParent(None)
                    child.widget().deleteLater()

            QApplication.processEvents()

            if self.sec_thread and self.sec_thread.isRunning():
                self.sec_thread.stop()
                self.sec_thread.wait(2000)

            self.sec_thread = SecurityThread(servers)
            self.sec_thread.progress.connect(self.sec_prog.setValue)
            self.sec_thread.result.connect(self.add_security_result)
            self.sec_thread.finished_signal.connect(self.security_done)
            self.sec_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Security check failed: {str(e)}")
            self.sec_btn.setEnabled(True)

    def add_security_result(self, name, status):
        try:
            card = QFrame()
            card.setFrameShape(QFrame.Shape.StyledPanel)
            card.setMinimumHeight(50)
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 2px solid #E0E0E0;
                    border-radius: 8px;
                }
            """)

            hlayout = QHBoxLayout(card)
            hlayout.setContentsMargins(20, 12, 20, 12)

            name_label = QLabel(name)
            name_label.setStyleSheet(
                "font-size: 15px; font-weight: bold; color: #000000; background-color: transparent; border: none;"
            )
            hlayout.addWidget(name_label)
            hlayout.addStretch()

            ip_text = DNS_SERVERS.get(name, "")
            if ip_text:
                ip_label = QLabel(ip_text)
                ip_label.setStyleSheet(
                    "font-size: 12px; color: #757575; background-color: transparent; border: none; margin-right: 20px;"
                )
                hlayout.addWidget(ip_label)

            status_label = QLabel()
            status_label.setMinimumWidth(140)
            if status == "valid":
                status_label.setText("DNSSEC Valid")
                status_label.setStyleSheet(
                    "color: #2E7D32; font-weight: bold; font-size: 14px; background-color: transparent; border: none;"
                )
            elif status == "signed":
                status_label.setText("Signed")
                status_label.setStyleSheet(
                    "color: #F57C00; font-weight: bold; font-size: 14px; background-color: transparent; border: none;"
                )
            elif status == "unsigned":
                status_label.setText("No DNSSEC")
                status_label.setStyleSheet(
                    "color: #C62828; font-weight: bold; font-size: 14px; background-color: transparent; border: none;"
                )
            else:
                status_label.setText("Error")
                status_label.setStyleSheet(
                    "color: #757575; font-weight: bold; font-size: 14px; background-color: transparent; border: none;"
                )

            hlayout.addWidget(status_label)
            self.sec_layout.addWidget(card)
            card.show()
            self.sec_container.update()

        except Exception as e:
            print(f"Error adding security result: {e}")

    def security_done(self):
        self.sec_btn.setEnabled(True)

    def export_csv(self):
        try:
            if not self.results:
                QMessageBox.warning(self, "Warning", "No results to export!")
                return

            filename, _ = QFileDialog.getSaveFileName(
                self, "Export", "dns_results.csv", "CSV (*.csv)"
            )
            if filename:
                with open(filename, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            "Server",
                            "IP",
                            "Cached_ms",
                            "Uncached_ms",
                            "Avg_ms",
                            "Reliability_%",
                        ]
                    )
                    for r in self.results:
                        writer.writerow(
                            [
                                r.name,
                                r.ip,
                                r.cached_avg,
                                r.uncached_avg,
                                r.overall_avg,
                                r.reliability,
                            ]
                        )
                QMessageBox.information(self, "Done", f"Results saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    def export_json(self):
        try:
            import json

            if not self.results:
                QMessageBox.warning(self, "Warning", "No results to export!")
                return

            filename, _ = QFileDialog.getSaveFileName(
                self, "Export", "dns_results.json", "JSON (*.json)"
            )
            if filename:
                data = []
                for r in self.results:
                    data.append(
                        {
                            "server": r.name,
                            "ip": r.ip,
                            "cached_ms": round(r.cached_avg, 2),
                            "uncached_ms": round(r.uncached_avg, 2),
                            "average_ms": round(r.overall_avg, 2),
                            "reliability_percent": round(r.reliability, 1),
                        }
                    )
                with open(filename, "w") as f:
                    json.dump(data, f, indent=2)
                QMessageBox.information(self, "Done", f"Results saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    def closeEvent(self, a0):
        if self.bench_thread and self.bench_thread.isRunning():
            self.bench_thread.stop()
            self.bench_thread.wait(2000)
        if self.sec_thread and self.sec_thread.isRunning():
            self.sec_thread.stop()
            self.sec_thread.wait(2000)
        a0.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
