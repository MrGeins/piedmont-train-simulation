import sys
from PyQt6.QtWidgets import QApplication
from backend.sim_engine import SimEngine
from frontend.dco_canvas import DcoConsoleView


def main():
    app = QApplication(sys.argv)

    simulation_engine = SimEngine(start_time_str="04:30:00", end_time_str="23:40:00")
    simulation_engine.initialize_timetable()

    console_view = DcoConsoleView(simulation_engine)

    def sync_backend_to_frontend_view(current_time_str, active_trains):
        console_view.bridge.tick_signal.emit(current_time_str, active_trains)

    simulation_engine.register_callback(sync_backend_to_frontend_view)

    console_view.show()
    simulation_engine.start_sim()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()