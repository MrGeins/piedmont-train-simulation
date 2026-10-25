from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QGraphicsView, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from frontend.theme import LINE_COLORS, get_text_color_for_bg


class MapView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(self.renderHints().Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scale(1.18, 1.18)
        else:
            self.scale(0.85, 0.85)

class TrainCardWidget(QFrame):
    def __init__(self, train, dest_station_name: str):
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        line_hex = LINE_COLORS.get(train.service_id, "#607D8B")
        text_hex = get_text_color_for_bg(line_hex)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: #252932;
                border: 1px solid #353B48;
                border-left: 4px solid {line_hex};
                border-radius: 8px;
            }}
            QFrame:hover {{
                background-color: #2E3440;
                border: 1px solid #61AFEF;
                border-left: 4px solid {line_hex};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        self.line_badge = QLabel(train.service_id)
        self.line_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.line_badge.setFixedWidth(38)
        self.line_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.line_badge.setStyleSheet(f"""
            background-color: {line_hex};
            color: {text_hex};
            border-radius: 4px;
            padding: 2px 4px;
            border: none;
        """)
        self.line_badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.train_id_lbl = QLabel()
        self.train_id_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.train_id_lbl.setStyleSheet("color: #ECEFF1; border: none; background: transparent;")
        self.train_id_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.track_chip = QLabel()
        self.track_chip.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.track_chip.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.status_chip = QLabel()
        self.status_chip.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        self.status_chip.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        top_row.addWidget(self.line_badge)
        top_row.addWidget(self.train_id_lbl)
        top_row.addStretch()
        top_row.addWidget(self.track_chip)
        top_row.addWidget(self.status_chip)
        layout.addLayout(top_row)

        self.desc_lbl = QLabel()
        self.desc_lbl.setFont(QFont("Segoe UI", 9))
        self.desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.desc_lbl)

        self.update_card(train, dest_station_name)

    def update_card(self, train, dest_station_name: str):
        self.train_number = train.train_number
        delay_min = train.accumulated_delay // 60
        assigned_tr = getattr(train, "assigned_track", 1)
        track_changed = getattr(train, "track_changed", False)

        self.train_id_lbl.setText(f"#{train.train_number}")

        track_text = f"⚠ Bin. {assigned_tr}" if track_changed else f"Bin. {assigned_tr}"
        track_bg = "rgba(255, 152, 0, 0.22)" if track_changed else "#323846"
        track_fg = "#FFB74D" if track_changed else "#CFD8DC"
        self.track_chip.setText(track_text)
        self.track_chip.setStyleSheet(f"""
            background-color: {track_bg};
            color: {track_fg};
            border-radius: 4px;
            padding: 2px 6px;
            border: none;
        """)

        if delay_min > 0:
            self.status_chip.setText(f"+{delay_min}'")
            chip_bg = "#D32F2F" if train.accumulated_delay > 180 else "#F57C00"
            self.status_chip.setStyleSheet(f"""
                background-color: {chip_bg};
                color: white;
                border-radius: 4px;
                padding: 2px 6px;
                border: none;
            """)
        else:
            self.status_chip.setText("IN ORARIO")
            self.status_chip.setStyleSheet("""
                background-color: rgba(0, 230, 118, 0.15);
                color: #00E676;
                border-radius: 4px;
                padding: 2px 6px;
                border: none;
            """)

        final_dest = train.route[-1] if train.route else ""
        dep_time = train.get_last_dep_str() if hasattr(train, "get_last_dep_str") else "--:--"
        arr_time = train.get_next_arr_str() if hasattr(train, "get_next_arr_str") else "--:--"
        plan_dep = train.get_planned_dep_str() if hasattr(train, "get_planned_dep_str") else "--:--"

        if train.status == "RUNNING":
            prev_st_key = train.route[train.current_station_index]
            status_text = f"Da {prev_st_key} ({dep_time}) ➔ {dest_station_name} ({arr_time})"
            status_color = "#B0BEC5"
        elif train.status == "TURNAROUND":
            status_text = f"Capolinea {dest_station_name} • Riparte {plan_dep} (Dir. {final_dest})"
            status_color = "#81D4FA"
        else:
            status_text = f"Fermo a {dest_station_name} • Riparte {plan_dep}"
            status_color = "#FFE082"

        self.desc_lbl.setText(status_text)
        self.desc_lbl.setStyleSheet(f"color: {status_color}; border: none; background: transparent;")

class LineHeaderWidget(QFrame):
    def __init__(self, line_id: str, count: int, is_collapsed: bool = False):
        super().__init__()
        self.line_id = line_id
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(32)
        self.line_hex = LINE_COLORS.get(line_id, "#607D8B")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        self.arrow_lbl = QLabel()
        self.arrow_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.arrow_lbl.setFixedWidth(14)
        self.arrow_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.title_lbl = QLabel(f"LINEA {line_id}")
        self.title_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet(f"color: {self.line_hex}; border: none; background: transparent; letter-spacing: 0.8px;")
        self.title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.count_badge = QLabel()
        self.count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_badge.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.count_badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout.addWidget(self.arrow_lbl)
        layout.addWidget(self.title_lbl)
        layout.addStretch()
        layout.addWidget(self.count_badge)

        self.update_header(count, is_collapsed)

    def update_header(self, count: int, is_collapsed: bool):
        arrow = "▶" if is_collapsed else "▼"
        self.arrow_lbl.setText(arrow)
        self.arrow_lbl.setStyleSheet(f"color: {self.line_hex}; border: none; background: transparent;")

        label_treni = "treno" if count == 1 else "treni"
        self.count_badge.setText(f"{count} {label_treni}")
        self.count_badge.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, 0.07);
            color: #CFD8DC;
            border-radius: 6px;
            padding: 1px 8px;
            border: none;
        """)

        bg_color = "#161920" if is_collapsed else "#1B2028"
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid #2E3440;
                border-left: 4px solid {self.line_hex};
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: #262C36;
                border: 1px solid {self.line_hex};
                border-left: 4px solid {self.line_hex};
            }}
        """)