import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db  # noqa: E402

db.DB_PATH = os.path.join(tempfile.mkdtemp(), "ci.db")  # isolated database for tests
