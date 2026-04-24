LOG_FILE = "searched.txt"

def load_searched():
    """Load all previously searched websites into a set."""
    try:
        with open(LOG_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def log_searched(url):
    """Add a website to the log file."""
    with open(LOG_FILE, "a") as f:
        f.write(url + "\n")