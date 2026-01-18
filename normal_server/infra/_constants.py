import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)


if __name__ == "__main__":
    print(f"Current Directory: {CURRENT_DIR}")
    print(f"Project Root: {PROJECT_ROOT}")
