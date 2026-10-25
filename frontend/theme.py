from PyQt6.QtGui import QColor

LINE_COLORS = {
    "S1":  "#FF9800",  # Arancione
    "S2":  "#29B6F6",  # Azzurra
    "S3a": "#66BB6A",  # Verde chiaro
    "S3b": "#1B5E20",  # Verde scuro
    "S4":  "#E53935",  # Rosso
    "S5":  "#8E24AA",  # Viola
    "S5e": "#CE93D8",  # Lilla
    "S6":  "#880E4F",  # Bordeaux
    "S7":  "#FDD835",  # Giallo
    "S8":  "#1E88E5",  # Blu
    "S8e": "#0D47A1",  # Blu scuro
}

def get_text_color_for_bg(hex_color: str) -> str:
    c = QColor(hex_color)
    luminance = (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255
    return "#121417" if luminance > 0.65 else "#FFFFFF"