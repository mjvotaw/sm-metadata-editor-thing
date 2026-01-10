import argparse
import sys
from PyQt6.QtWidgets import QApplication
from src.utils.logger import get_logger
from src.utils.app_paths import AppPaths
from src.ui.main_window import MainWindow

logger = get_logger(__name__)


def get_args():
    parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--app-data-dir", 
        help="Specify directory for the application to save app data (config files, caches). By default, the application will use whatever is standard for your OS",
        type=str)
    args = parser.parse_args()
    return args

def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    args = get_args()
    if args.app_data_dir:
        AppPaths.set_base_dir(args.app_data_dir)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()