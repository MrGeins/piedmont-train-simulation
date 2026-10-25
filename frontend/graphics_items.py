import math
from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QFontMetricsF, QPainterPath

from frontend.theme import LINE_COLORS


class StationYardItem(QGraphicsItem):
    TRACK_SPACING = 5.0
    TRACK_WIDTH = 1.4
    YARD_HALF_LEN = 16.0

    def __init__(self, st_key: str, st_name: str, x: float, y: float, angle_deg: float, st_obj, is_double_line: bool = True):
        super().__init__()
        self.st_key = st_key
        self.st_name = st_name
        self.setPos(x, y)
        self.angle_deg = angle_deg
        self.st_obj = st_obj
        self.is_double_line = is_double_line

        self.num_tracks = st_obj.num_tracks if st_obj else 2
        self.available_tracks = set(st_obj.available_tracks) if st_obj else {1, 2}
        self.stub_tracks = st_obj.stub_tracks if (st_obj and hasattr(st_obj, "stub_tracks")) else {}

        self.visual_tracks = self._compute_visual_tracks()
        self.occupied_tracks = set()
        self.external_label_item = None

        self.setZValue(5)

    def _compute_visual_tracks(self) -> list[int]:
        if self.num_tracks <= 6:
            return list(range(1, self.num_tracks + 1))
        extra = {1, self.num_tracks}
        return sorted(set(self.available_tracks) | extra)

    def set_occupied_tracks(self, occupied: set[int]):
        if self.occupied_tracks != occupied:
            self.occupied_tracks = set(occupied)
            self.update()

    def get_track_local_offset_y(self, track_num: int) -> float:
        if track_num in self.visual_tracks:
            idx = self.visual_tracks.index(track_num)
        else:
            idx = 0
        n_vis = len(self.visual_tracks)
        return (idx - (n_vis - 1) / 2.0) * self.TRACK_SPACING

    def get_track_scene_pos(self, track_num: int) -> tuple[float, float]:
        offset_y = self.get_track_local_offset_y(track_num)
        rad = math.radians(self.angle_deg)
        nx = -math.sin(rad)
        ny = math.cos(rad)
        return self.pos().x() + nx * offset_y, self.pos().y() + ny * offset_y

    def boundingRect(self) -> QRectF:
        return QRectF(-90.0, -70.0, 180.0, 140.0)

    def _is_blocked_end(self, track_num: int) -> tuple[bool, bool]:
        if track_num not in self.stub_tracks:
            return False, False

        access_dir = self.stub_tracks[track_num].upper()
        rad = math.radians(self.angle_deg)
        dx, dy = math.cos(rad), math.sin(rad)

        dir_vectors = {
            "SOUTH": (0.0, 1.0),
            "NORTH": (0.0, -1.0),
            "EAST":  (1.0, 0.0),
            "WEST":  (-1.0, 0.0),
        }
        vx, vy = dir_vectors.get(access_dir, (0.0, 1.0))
        dot = dx * vx + dy * vy
        return (True, False) if dot >= 0 else (False, True)

    def paint(self, painter, option: QStyleOptionGraphicsItem, widget=None):
        painter.setRenderHint(painter.renderHints().Antialiasing)
        lod = option.levelOfDetailFromTransform(painter.worldTransform())

        if self.external_label_item is not None:
            should_be_visible = (lod < 1.85)
            if self.external_label_item.isVisible() != should_be_visible:
                self.external_label_item.setVisible(should_be_visible)

        if lod < 1.85:
            if self.occupied_tracks:
                halo_pen = QPen(QColor("#00E676"), 1.4)
                painter.setPen(halo_pen)
                painter.setBrush(QBrush(QColor(0, 230, 118, 45)))
                painter.drawEllipse(QPointF(0, 0), 6.0, 6.0)

            painter.setPen(QPen(QColor("#ECEFF1"), 1.0))
            painter.setBrush(QBrush(QColor("#242933")))
            painter.drawEllipse(QPointF(0, 0), 3.2, 3.2)
            return

        painter.save()
        painter.rotate(self.angle_deg)

        n_vis = len(self.visual_tracks)
        total_h = max(4.0, (n_vis - 1) * self.TRACK_SPACING)
        main_top_y = -2.5 if self.is_double_line and n_vis >= 2 else 0.0
        main_bot_y = 2.5 if self.is_double_line and n_vis >= 2 else 0.0

        max_dy = max((abs(self.get_track_local_offset_y(t) - (main_top_y if self.get_track_local_offset_y(t) <= 0 else main_bot_y)) for t in self.visual_tracks), default=0.0)
        lead_len = max_dy + 3.0
        full_half_x = self.YARD_HALF_LEN + lead_len

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#242933")))
        painter.drawRect(QRectF(-full_half_x, -total_h / 2.0 - 3.0, full_half_x * 2, total_h + 6.0))

        base_rail_pen = QPen(
            QColor("#78909C"), self.TRACK_WIDTH,
            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin
        )

        all_blocked_left = all(self._is_blocked_end(t)[0] for t in self.visual_tracks)
        all_blocked_right = all(self._is_blocked_end(t)[1] for t in self.visual_tracks)

        painter.setPen(base_rail_pen)
        if not all_blocked_left:
            painter.drawLine(QPointF(-full_half_x - 0.5, main_top_y), QPointF(-self.YARD_HALF_LEN, main_top_y))
            if self.is_double_line and n_vis >= 2:
                painter.drawLine(QPointF(-full_half_x - 0.5, main_bot_y), QPointF(-self.YARD_HALF_LEN, main_bot_y))
        if not all_blocked_right:
            painter.drawLine(QPointF(self.YARD_HALF_LEN, main_top_y), QPointF(full_half_x + 0.5, main_top_y))
            if self.is_double_line and n_vis >= 2:
                painter.drawLine(QPointF(self.YARD_HALF_LEN, main_bot_y), QPointF(full_half_x + 0.5, main_bot_y))

        for t_num in self.visual_tracks:
            ty = self.get_track_local_offset_y(t_num)
            is_avail = t_num in self.available_tracks
            is_occ = t_num in self.occupied_tracks
            blocked_left, blocked_right = self._is_blocked_end(t_num)

            if is_avail:
                plat_rect = QRectF(-self.YARD_HALF_LEN + 3.0, ty - 2.3, (self.YARD_HALF_LEN - 3.0) * 2, 1.0)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor("#37474F")))
                painter.drawRoundedRect(plat_rect, 0.4, 0.4)

            anchor_y = main_top_y if ty <= 0 else main_bot_y
            dy_dist = abs(ty - anchor_y)

            sw_color = QColor("#78909C") if is_avail else QColor("#455A64")
            sw_pen = QPen(sw_color, self.TRACK_WIDTH, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)

            if not blocked_left and dy_dist > 0.1:
                painter.setPen(sw_pen)
                painter.drawLine(QPointF(-self.YARD_HALF_LEN - dy_dist, anchor_y), QPointF(-self.YARD_HALF_LEN, ty))

            if not blocked_right and dy_dist > 0.1:
                painter.setPen(sw_pen)
                painter.drawLine(QPointF(self.YARD_HALF_LEN, ty), QPointF(self.YARD_HALF_LEN + dy_dist, anchor_y))

            if is_occ:
                t_pen = QPen(QColor("#FF5252"), self.TRACK_WIDTH + 0.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            elif is_avail:
                t_pen = QPen(QColor("#ECEFF1"), self.TRACK_WIDTH, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            else:
                t_pen = QPen(QColor("#455A64"), 0.9, Qt.PenStyle.DashLine, Qt.PenCapStyle.FlatCap)

            painter.setPen(t_pen)
            painter.drawLine(QPointF(-self.YARD_HALF_LEN, ty), QPointF(self.YARD_HALF_LEN, ty))

            bumper_pen = QPen(QColor("#EF5350"), 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap)
            if blocked_left:
                painter.setPen(bumper_pen)
                painter.drawLine(QPointF(-self.YARD_HALF_LEN, ty - 1.3), QPointF(-self.YARD_HALF_LEN, ty + 1.3))
            if blocked_right:
                painter.setPen(bumper_pen)
                painter.drawLine(QPointF(self.YARD_HALF_LEN, ty - 1.3), QPointF(self.YARD_HALF_LEN, ty + 1.3))

            painter.save()
            painter.translate(-self.YARD_HALF_LEN + 4.2, ty)
            painter.rotate(-self.angle_deg)

            pill_rect = QRectF(-2.2, -1.7, 4.4, 3.4)
            painter.setPen(QPen(QColor("#455A64"), 0.35))
            painter.setBrush(QBrush(QColor("#181B20")))
            painter.drawRoundedRect(pill_rect, 0.8, 0.8)

            font_num = QFont("Segoe UI")
            font_num.setPointSizeF(2.1)
            font_num.setBold(True)
            painter.setFont(font_num)
            num_color = QColor("#FF8A80") if is_occ else (QColor("#ECEFF1") if is_avail else QColor("#607D8B"))
            painter.setPen(num_color)
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, str(t_num))
            painter.restore()

        painter.restore()

        rad = math.radians(self.angle_deg)
        badge_dist = (total_h / 2.0) + 5.8
        bx = abs(math.sin(rad)) * (badge_dist + 10.0) if abs(math.sin(rad)) > 0.7 else 0.0
        by = -badge_dist if abs(math.sin(rad)) <= 0.7 else 0.0

        font_title = QFont("Segoe UI")
        font_title.setPointSizeF(2.5)
        font_title.setBold(True)
        painter.setFont(font_title)

        label_str = self.st_name.upper()
        fm = QFontMetricsF(font_title)
        text_w = fm.horizontalAdvance(label_str) + 4.5
        text_h = fm.height() + 1.4
        badge_rect = QRectF(bx - text_w / 2.0, by - text_h / 2.0, text_w, text_h)

        painter.setPen(QPen(QColor("#3B82F6"), 0.45))
        painter.setBrush(QBrush(QColor("#0F294A")))
        painter.drawRoundedRect(badge_rect, 1.2, 1.2)

        painter.setPen(QColor("#ECEFF1"))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, label_str)


class TrainGraphicsItem(QGraphicsItem):
    def __init__(self, x: float, y: float, service_id: str, train_number: int, is_delayed: bool, assigned_track: int):
        super().__init__()
        self.setPos(x, y)
        self.service_id = service_id
        self.train_number = train_number
        self.is_delayed = is_delayed
        self.assigned_track = assigned_track
        self.base_hex = LINE_COLORS.get(service_id, "#00E676")
        self.color = QColor(self.base_hex)
        self.setZValue(20)
        self.setToolTip(f"Linea {service_id} - Treno #{train_number} (Bin. {assigned_track})")

    def boundingRect(self) -> QRectF:
        return QRectF(-16, -16, 32, 32)

    def paint(self, painter, option: QStyleOptionGraphicsItem, widget=None):
        painter.setRenderHint(painter.renderHints().Antialiasing)
        lod = option.levelOfDetailFromTransform(painter.worldTransform())

        scale_factor = 0.28 if lod >= 1.85 else 0.80
        painter.save()
        painter.scale(scale_factor, scale_factor)

        if self.is_delayed:
            glow_pen = QPen(QColor("#FF1744"), 2.2)
            painter.setPen(glow_pen)
            painter.setBrush(QBrush(QColor(255, 23, 68, 45)))
            painter.drawRoundedRect(QRectF(-11, -11, 22, 22), 6, 6)

        pantograph_pen = QPen(QColor("#ECEFF1"), 1.5)
        painter.setPen(pantograph_pen)
        painter.drawLine(QPointF(-3, -8), QPointF(0, -11))
        painter.drawLine(QPointF(3, -8), QPointF(0, -11))
        painter.drawLine(QPointF(-4, -11), QPointF(4, -11))

        body_rect = QRectF(-8.5, -8, 17, 15)
        painter.setPen(QPen(QColor("#FFFFFF"), 1.3))
        painter.setBrush(QBrush(self.color))
        painter.drawRoundedRect(body_rect, 4, 4)

        windshield_rect = QRectF(-6, -5.5, 12, 5)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#1A2027")))
        painter.drawRoundedRect(windshield_rect, 1.5, 1.5)

        painter.setBrush(QBrush(QColor("#FFFDE7")))
        painter.drawEllipse(QPointF(-4.5, 3.2), 1.6, 1.6)
        painter.drawEllipse(QPointF(4.5, 3.2), 1.6, 1.6)

        painter.setPen(QPen(QColor("#B0BEC5"), 1.8))
        painter.drawLine(QPointF(-5.5, 8.5), QPointF(-2, 8.5))
        painter.drawLine(QPointF(2, 8.5), QPointF(5.5, 8.5))

        painter.restore()