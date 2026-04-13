"""About PyPub — inline main panel (no dialog required)."""

from __future__ import annotations

import platform
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget

from pypub import __app_name__, __author__, __contact__, __version__


class AboutPanel(QWidget):
    def __init__(
        self,
        app_data_dir: Path,
        config_dir: Path,
        log_dir: Path | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._app_data = Path(app_data_dir)
        self._config = Path(config_dir)
        self._log = Path(log_dir) if log_dir else None
        self.setObjectName("PageSurface")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        intro = QWidget()
        intro_lay = QVBoxLayout(intro)
        intro_lay.setContentsMargins(0, 0, 0, 0)
        intro_lay.setSpacing(4)
        hero = QLabel("About PyPub")
        hero.setObjectName("PageHeroTitle")
        deck = QLabel("PyPub is a Windows desktop client for drafting, media handling, and Micropub publishing.")
        deck.setObjectName("PageHeroSubtitle")
        deck.setWordWrap(True)
        intro_lay.addWidget(hero)
        intro_lay.addWidget(deck)
        outer.addWidget(intro)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        host = QWidget()
        lay = QVBoxLayout(host)
        lay.setSpacing(12)

        lay.addWidget(self._heading(__app_name__, "app_title"))
        lay.addWidget(self._line(f"<b>Version</b> {__version__}", "section"))
        lay.addWidget(
            self._line(
                "A native Micropub desktop client for Windows.",
                "body",
            )
        )
        lay.addWidget(self._line(f"<b>Author</b> {__author__}", "section"))
        lay.addWidget(self._line(f"<b>Contact</b> <a href=\"mailto:{__contact__}\">{__contact__}</a>", "body"))
        lay.addWidget(self._heading("Stack", "section_title"))
        lay.addWidget(
            self._line(
                "Python · PySide6 · SQLite · httpx · keyring · markdown-it-py · nh3",
                "mono",
            )
        )
        lay.addWidget(self._heading("Paths", "section_title"))
        lay.addWidget(self._path_block("Data", self._app_data))
        lay.addWidget(self._path_block("Config", self._config))
        if self._log:
            lay.addWidget(self._path_block("Logs", self._log))
        lay.addWidget(self._heading("Runtime", "section_title"))
        lay.addWidget(
            self._line(
                f"<span class='mono'>{platform.python_version()} — {sys.executable}</span>",
                "mono",
            )
        )
        lay.addWidget(self._heading("Links", "section_title"))
        lay.addWidget(
            self._line(
                '<a href="https://micropub.net/">Micropub</a> · '
                '<a href="https://indieauth.spec.indieweb.org/">IndieAuth</a>',
                "body",
            )
        )
        lay.addStretch()

        scroll.setWidget(host)
        outer.addWidget(scroll, 1)

        btn_row = QVBoxLayout()
        btn_updates = QPushButton("Check for updates manually")
        btn_updates.clicked.connect(self._stub_updates)
        btn_row.addWidget(btn_updates)
        outer.addLayout(btn_row)

    def _heading(self, text: str, css_class: str) -> QLabel:
        lbl = QLabel(f"<h2 class='{css_class}'>{text}</h2>")
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setOpenExternalLinks(True)
        return lbl

    def _line(self, html: str, css_class: str) -> QLabel:
        lbl = QLabel(f"<p class='{css_class}'>{html}</p>")
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setWordWrap(True)
        lbl.setOpenExternalLinks(True)
        return lbl

    def _path_block(self, title: str, path: Path) -> QLabel:
        return self._line(f"<b>{title}</b><br/><span class='mono'>{path}</span>", "mono")

    def _stub_updates(self) -> None:
        QMessageBox.information(
            self,
            "Updates",
            f"You are running {__app_name__} {__version__}. "
            "There is no automatic update channel yet. Please check for newer builds manually.",
        )
