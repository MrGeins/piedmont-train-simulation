import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QGraphicsScene, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QPen, QColor, QFont

from backend.data.topology_data import stations
from frontend.graphics_items import StationYardItem, TrainGraphicsItem
from frontend.ui_widgets import MapView, TrainCardWidget
from backend.data.stations_data import stations_registry
from frontend.ui_widgets import MapView, TrainCardWidget, LineHeaderWidget


class SignalBridge(QObject):
    tick_signal = pyqtSignal(str, list)


class DcoConsoleView(QWidget):
    def __init__(self, simulation_engine):
        super().__init__()
        self.simulation_engine = simulation_engine
        self.bridge = SignalBridge()
        self.bridge.tick_signal.connect(self.update_live_layer)

        self.train_markers = {}
        self.station_items = {}
        self.sidebar_items = {}
        self.header_items = {}
        self.line_train_items = {}
        self.collapsed_lines = set()
        self.speed_buttons = {}

        self.init_ui()
        self.draw_static_infrastructure()

    def init_ui(self):
        self.setWindowTitle("Console DCO - SFM Piemonte Simulator")
        self.resize(1420, 950)
        self.setStyleSheet("background-color: #181B20; color: white;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # --- TOP BAR ---
        top_bar = QHBoxLayout()
        title = QLabel("RAILWAY CONTROL CENTER")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #CFD8DC; letter-spacing: 1.5px;")

        top_bar.addWidget(title)
        top_bar.addStretch()

        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #21252B;
                border: 1px solid #333842;
                border-radius: 8px;
                padding: 2px;
            }
        """)
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(6, 4, 6, 4)
        controls_layout.setSpacing(6)

        btn_specs = [
            ("PAUSE", "⏸ Pausa"),
            ("1X", "▶ 1x"),
            ("2X", "⏩ 2x"),
            ("10X", "⚡ 10x"),
        ]

        for key, label in btn_specs:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            btn.clicked.connect(lambda checked, k=key: self.on_speed_control_clicked(k))
            self.speed_buttons[key] = btn
            controls_layout.addWidget(btn)

        self._update_speed_buttons_style("1X")
        top_bar.addWidget(controls_frame)
        top_bar.addStretch()

        self.clock_label = QLabel("SIM CLOCK: 04:30:00")
        self.clock_label.setFont(QFont("Consolas", 20, QFont.Weight.Bold))
        self.clock_label.setStyleSheet("""
            color: #00E676;
            background-color: #121417;
            border: 1px solid #2E3440;
            padding: 6px 16px;
            border-radius: 8px;
        """)

        top_bar.addWidget(self.clock_label)
        main_layout.addLayout(top_bar)

        # --- BODY: Mappa + Sidebar ---
        body_layout = QHBoxLayout()
        body_layout.setSpacing(12)

        self.scene = QGraphicsScene()
        self.view = MapView(self.scene)
        self.view.setStyleSheet("""
            border: 2px solid #2E3440;
            background-color: #242933;
            border-radius: 10px;
        """)
        body_layout.addWidget(self.view, stretch=7)

        sidebar_container = QFrame()
        sidebar_container.setMinimumWidth(370)
        sidebar_container.setStyleSheet("""
            QFrame {
                background-color: #1E222A;
                border: 1px solid #2E3440;
                border-radius: 10px;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(10, 12, 10, 10)
        sidebar_layout.setSpacing(8)

        sidebar_header_layout = QHBoxLayout()
        sidebar_title = QLabel("TRENI ATTIVI SULLA RETE")
        sidebar_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        sidebar_title.setStyleSheet("color: #90A4AE; border: none; letter-spacing: 1px;")

        self.active_count_badge = QLabel("0")
        self.active_count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_count_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.active_count_badge.setStyleSheet("""
            background-color: #37474F;
            color: #ECEFF1;
            border-radius: 10px;
            padding: 2px 10px;
            border: none;
        """)

        sidebar_header_layout.addWidget(sidebar_title)
        sidebar_header_layout.addStretch()
        sidebar_header_layout.addWidget(self.active_count_badge)
        sidebar_layout.addLayout(sidebar_header_layout)

        self.train_status_list = QListWidget()
        self.train_status_list.setSpacing(6)
        self.train_status_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.train_status_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                padding: 0px;
            }
            QListWidget::item:selected {
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #181B20;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #4B5366;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #61AFEF;
            }
        """)
        self.train_status_list.itemClicked.connect(self.on_train_clicked)
        sidebar_layout.addWidget(self.train_status_list)

        body_layout.addWidget(sidebar_container, stretch=3)
        main_layout.addLayout(body_layout)

        # --- BOTTOM BAR ---
        bottom_bar = QHBoxLayout()
        self.stress_btn = QPushButton("ACTIVATE RUSH HOUR STRESS")
        self.stress_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stress_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 28px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #F44336; }
        """)
        self.stress_btn.clicked.connect(self.on_stress_button_click)

        bottom_bar.addStretch()
        bottom_bar.addWidget(self.stress_btn)
        bottom_bar.addStretch()
        main_layout.addLayout(bottom_bar)

    def _update_speed_buttons_style(self, active_key: str):
        for key, btn in self.speed_buttons.items():
            if key == active_key:
                bg = "#EF5350" if key == "PAUSE" else "#1E88E5"
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {bg};
                        color: white;
                        border: none;
                        padding: 6px 14px;
                        border-radius: 6px;
                    }}
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2C313A;
                        color: #B0BEC5;
                        border: none;
                        padding: 6px 14px;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background-color: #383E4A;
                        color: white;
                    }
                """)

    def on_speed_control_clicked(self, mode: str):
        if mode == "PAUSE":
            self.simulation_engine.set_paused(True)
        elif mode == "1X":
            self.simulation_engine.set_speed(1)
        elif mode == "2X":
            self.simulation_engine.set_speed(2)
        elif mode == "10X":
            self.simulation_engine.set_speed(10)

        self._update_speed_buttons_style(mode)

    def on_stress_button_click(self):
        if self.simulation_engine.rush_hour_stress:
            self.simulation_engine.toggle_rush_hour_stress(False)
            self.stress_btn.setText("ACTIVATE RUSH HOUR STRESS")
            self.stress_btn.setStyleSheet(
                "QPushButton { background-color: #D32F2F; color: white; font-weight: bold; font-size: 13px; padding: 10px 28px; border-radius: 8px; } QPushButton:hover { background-color: #F44336; }"
            )
        else:
            self.simulation_engine.toggle_rush_hour_stress(True)
            self.stress_btn.setText("RUSH HOUR INDUCED (ACTIVE)")
            self.stress_btn.setStyleSheet(
                "QPushButton { background-color: #B71C1C; border: 2px solid #FF5252; color: white; font-weight: bold; font-size: 13px; padding: 10px 28px; border-radius: 8px; }"
            )

    @staticmethod
    def _latlon_to_xy(x, y):
        return x * 3.5, y * 3.5

    def _compute_station_angle(self, st_key: str, st_data: dict, neighbors: list[dict]) -> float:
        axis_overrides = {
            "STURA": 90.0,
            "SETTIMO": 0.0,
            "CHIVASSO": 0.0,
            "REBAUDENGO": 90.0,
            "DORA": 90.0,
            "PORTA_SUSA": 90.0,
            "PORTA_NUOVA": 90.0,
            "LINGOTTO": 90.0,
            "MONCALIERI": 90.0,
            "TROFARELLO": 90.0,
            "CARMAGNOLA": 90.0,
            "ZAPPATA": 0.0,
            "SAN_PAOLO": 0.0,
            "BUSSOLENO": 0.0,
        }
        if st_key in axis_overrides:
            return axis_overrides[st_key]

        if not neighbors:
            return 0.0

        sx, sy = st_data.get("x", 0), st_data.get("y", 0)
        if len(neighbors) == 1:
            dx = neighbors[0].get("x", 0) - sx
            dy = neighbors[0].get("y", 0) - sy
        else:
            dx = neighbors[1].get("x", 0) - neighbors[0].get("x", 0)
            dy = neighbors[1].get("y", 0) - neighbors[0].get("y", 0)

        raw_deg = math.degrees(math.atan2(dy, dx))
        # Normalizza nell'intervallo [-90, 90] e aggancia al multiplo di 45° più vicino
        while raw_deg > 90:
            raw_deg -= 180
        while raw_deg < -90:
            raw_deg += 180
        snapped = round(raw_deg / 45.0) * 45.0
        return 90.0 if snapped == -90.0 else float(snapped)

    def draw_static_infrastructure(self):
        from backend.network_graph import infrastructure_map

        neighbors = {k: [] for k in stations.keys()}
        station_has_double = {k: False for k in stations.keys()}
        node_incident_tracks = {k: [] for k in stations.keys()}
        track_color = QColor("#78909C")

        pen = QPen(track_color)
        pen.setWidthF(1.4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        for track in infrastructure_map:
            s1 = stations.get(track.node_from)
            s2 = stations.get(track.node_to)
            if s1 and s2:
                neighbors[track.node_from].append(s2)
                neighbors[track.node_to].append(s1)
                if track.double_track:
                    station_has_double[track.node_from] = True
                    station_has_double[track.node_to] = True

                x1, y1 = self._latlon_to_xy(s1.get("x", 0), s1.get("y", 0))
                x2, y2 = self._latlon_to_xy(s2.get("x", 0), s2.get("y", 0))
                dx, dy = x2 - x1, y2 - y1
                length = math.hypot(dx, dy)
                if length == 0:
                    continue

                ux, uy = dx / length, dy / length
                spacing = 2.5
                nx, ny = -uy * spacing, ux * spacing

                if track.double_track:
                    self.scene.addLine(x1 + nx, y1 + ny, x2 + nx, y2 + ny, pen)
                    self.scene.addLine(x1 - nx, y1 - ny, x2 - nx, y2 - ny, pen)
                    node_incident_tracks[track.node_from].append((ux, uy, nx, ny, True))
                    node_incident_tracks[track.node_to].append((-ux, -uy, nx, ny, True))
                else:
                    self.scene.addLine(x1, y1, x2, y2, pen)
                    node_incident_tracks[track.node_from].append((ux, uy, 0.0, 0.0, False))
                    node_incident_tracks[track.node_to].append((-ux, -uy, 0.0, 0.0, False))

        # Salda geometricamente i bivi e i posti di comunicazione (nodi senza stazione)
        for key, st in stations.items():
            if st.get("display_label", False):
                continue
            inc = node_incident_tracks.get(key, [])
            if len(inc) < 2:
                continue
            cx, cy = self._latlon_to_xy(st.get("x", 0), st.get("y", 0))

            # Copre le intersezioni interne sporche al centro del nodo e raccorda i profili esterni
            double_branches = [b for b in inc if b[4]]
            single_branches = [b for b in inc if not b[4]]

            if double_branches and single_branches:
                # Raccordo pulito da Doppio Binario a Binario Singolo (es. Bivio Valsusa -> Susa)
                for sb in single_branches:
                    s_ux, s_uy, _, _, _ = sb
                    px, py = cx + s_ux * 4.0, cy + s_uy * 4.0
                    for db in double_branches:
                        _, _, d_nx, d_ny, _ = db
                        self.scene.addLine(cx + d_nx, cy + d_ny, px, py, pen)
                        self.scene.addLine(cx - d_nx, cy - d_ny, px, py, pen)

            elif len(double_branches) >= 2:
                # Giunzione smussata tra rami a doppio binario (pieghe PC_* e bivi)
                for i in range(len(double_branches)):
                    for j in range(i + 1, len(double_branches)):
                        _, _, nx1, ny1, _ = double_branches[i]
                        _, _, nx2, ny2, _ = double_branches[j]
                        if nx1 * nx2 + ny1 * ny2 >= 0:
                            self.scene.addLine(cx + nx1, cy + ny1, cx + nx2, cy + ny2, pen)
                            self.scene.addLine(cx - nx1, cy - ny1, cx - nx2, cy - ny2, pen)
                        else:
                            self.scene.addLine(cx + nx1, cy + ny1, cx - nx2, cy - ny2, pen)
                            self.scene.addLine(cx - nx1, cy - ny1, cx + nx2, cy + ny2, pen)

        for key, st in stations.items():
            if not st.get("display_label", False):
                continue

            x, y = self._latlon_to_xy(st.get("x", 0), st.get("y", 0))
            nb_list = neighbors.get(key, [])
            angle_deg = self._compute_station_angle(key, st, nb_list)
            st_obj = stations_registry.get(key)

            yard_item = StationYardItem(
                key, st["nome"], x, y, angle_deg, st_obj,
                is_double_line=station_has_double.get(key, True)
            )
            self.scene.addItem(yard_item)
            self.station_items[key] = yard_item

            text = self.scene.addText(st["nome"])
            text.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            text.setDefaultTextColor(QColor("#CFD8DC"))
            text.setZValue(10)
            yard_item.external_label_item = text

            label_mode = st.get("label_dir", "AUTO")
            if label_mode == "AUTO" and nb_list:
                avg_dx = sum(abs(st.get("x", 0) - n.get("x", 0)) for n in nb_list)
                avg_dy = sum(abs(st.get("y", 0) - n.get("y", 0)) for n in nb_list)
                if avg_dy == 0 and avg_dx > 0:
                    label_mode = "ANGLED"
                elif avg_dx == 0 and avg_dy > 0:
                    label_mode = "RIGHT"
                else:
                    label_mode = "DIAG"

            if label_mode == "ANGLED":
                text.setRotation(-45)
                text.setPos(x - 4, y - 14)
            elif label_mode == "LEFT":
                rect = text.boundingRect()
                text.setPos(x - rect.width() - 8, y - 10)
            elif label_mode == "DIAG":
                text.setPos(x + 10, y - 16)
            else:
                text.setPos(x + 10, y - 10)

    def on_train_clicked(self, item: QListWidgetItem):
        item_data = item.data(Qt.ItemDataRole.UserRole)
        if not item_data:
            return

        if isinstance(item_data, str) and item_data.startswith("HEADER:"):
            line_id = item_data.split(":", 1)[1]
            if line_id in self.collapsed_lines:
                self.collapsed_lines.remove(line_id)
            else:
                self.collapsed_lines.add(line_id)

            is_collapsed = line_id in self.collapsed_lines
            train_items = self.line_train_items.get(line_id, [])
            for t_item in train_items:
                t_item.setHidden(is_collapsed)

            if line_id in self.header_items:
                _, hdr_widget = self.header_items[line_id]
                hdr_widget.update_header(len(train_items), is_collapsed)
            return

        if item_data in self.train_markers:
            marker = self.train_markers[item_data]
            self.view.centerOn(marker)

    def _compute_smooth_train_scene_pos(self, train, target_station_key: str, assigned_tr: int) -> tuple[float, float]:
        if train.status in ["DWELLING", "TURNAROUND"] and target_station_key in self.station_items:
            return self.station_items[target_station_key].get_track_scene_pos(assigned_tr)

        line_x, line_y = self._latlon_to_xy(train.current_x, train.current_y)

        if train.status == "RUNNING":
            from_key = train.route[train.current_station_index]
            prog = train.current_progress

            if prog < 0.14 and from_key in self.station_items:
                dep_tr = getattr(train, "departure_track", assigned_tr)
                sx, sy = self.station_items[from_key].get_track_scene_pos(dep_tr)
                alpha = prog / 0.14
                return sx + (line_x - sx) * alpha, sy + (line_y - sy) * alpha

            if prog > 0.86 and target_station_key in self.station_items:
                ex, ey = self.station_items[target_station_key].get_track_scene_pos(assigned_tr)
                alpha = (prog - 0.86) / 0.14
                return line_x + (ex - line_x) * alpha, line_y + (ey - line_y) * alpha

        return line_x, line_y

    def update_live_layer(self, current_time_str: str, active_trains: list):
        self.clock_label.setText(f"SIM CLOCK: {current_time_str}")

        for marker in self.train_markers.values():
            self.scene.removeItem(marker)
        self.train_markers.clear()

        station_occupied_map = {k: set() for k in self.station_items.keys()}
        running_trains = [
            t for t in active_trains
            if t.status in ["RUNNING", "DWELLING", "TURNAROUND"]
        ]

        line_order = ["S1", "S2", "S3a", "S3b", "S4", "S5", "S5e", "S6", "S7", "S8", "S8e"]
        running_trains.sort(
            key=lambda t: (
                line_order.index(t.service_id) if t.service_id in line_order else 99,
                t.train_number
            )
        )

        for train in running_trains:
            agent_key = id(train)
            is_delayed = train.accumulated_delay > 180
            assigned_tr = getattr(train, "assigned_track", 1)

            target_idx = (
                train.current_station_index + 1
                if train.current_station_index + 1 < len(train.route)
                else -1
            )
            target_station_key = train.route[target_idx]

            if train.status in ["DWELLING", "TURNAROUND"] and target_station_key in self.station_items:
                station_occupied_map[target_station_key].add(assigned_tr)

            x, y = self._compute_smooth_train_scene_pos(train, target_station_key, assigned_tr)

            marker = TrainGraphicsItem(
                x, y, train.service_id, train.train_number, is_delayed, assigned_tr
            )
            self.scene.addItem(marker)
            self.train_markers[agent_key] = marker

        grouped: dict[str, list] = {}
        for t in running_trains:
            grouped.setdefault(t.service_id, []).append(t)

        current_signature = tuple((t.service_id, id(t)) for t in running_trains)
        if getattr(self, "_last_sidebar_signature", None) != current_signature:
            scroll_pos = self.train_status_list.verticalScrollBar().value()
            self._last_sidebar_signature = current_signature
            self.train_status_list.clear()
            self.sidebar_items.clear()
            self.header_items.clear()
            self.line_train_items.clear()

            for line_id, trains_in_line in grouped.items():
                is_collapsed = line_id in self.collapsed_lines

                hdr_widget = LineHeaderWidget(line_id, len(trains_in_line), is_collapsed)
                hdr_item = QListWidgetItem(self.train_status_list)
                hdr_item.setSizeHint(hdr_widget.sizeHint())
                hdr_item.setData(Qt.ItemDataRole.UserRole, f"HEADER:{line_id}")
                self.train_status_list.addItem(hdr_item)
                self.train_status_list.setItemWidget(hdr_item, hdr_widget)
                self.header_items[line_id] = (hdr_item, hdr_widget)
                self.line_train_items[line_id] = []

                for train in trains_in_line:
                    agent_key = id(train)
                    target_idx = (
                        train.current_station_index + 1
                        if train.current_station_index + 1 < len(train.route)
                        else -1
                    )
                    target_station_key = train.route[target_idx]
                    dest_station_name = stations.get(target_station_key, {}).get("nome", "Capolinea")

                    card = TrainCardWidget(train, dest_station_name)
                    list_item = QListWidgetItem(self.train_status_list)
                    list_item.setSizeHint(card.sizeHint())
                    list_item.setData(Qt.ItemDataRole.UserRole, agent_key)
                    self.train_status_list.addItem(list_item)
                    self.train_status_list.setItemWidget(list_item, card)
                    list_item.setHidden(is_collapsed)

                    self.sidebar_items[agent_key] = (list_item, card)
                    self.line_train_items[line_id].append(list_item)

            self.train_status_list.verticalScrollBar().setValue(scroll_pos)
        else:
            for train in running_trains:
                agent_key = id(train)
                if agent_key in self.sidebar_items:
                    target_idx = (
                        train.current_station_index + 1
                        if train.current_station_index + 1 < len(train.route)
                        else -1
                    )
                    target_station_key = train.route[target_idx]
                    dest_station_name = stations.get(target_station_key, {}).get("nome", "Capolinea")
                    _, card = self.sidebar_items[agent_key]
                    card.update_card(train, dest_station_name)

        for st_key, yard_item in self.station_items.items():
            yard_item.set_occupied_tracks(station_occupied_map.get(st_key, set()))

        self.active_count_badge.setText(str(len(running_trains)))