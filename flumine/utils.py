import uuid


def create_short_uuid():
    return str(uuid.uuid4())[:8]


def file_line_count(file_path):
    with open(file_path) as f:
        for i, l in enumerate(f):
            pass
    return i + 1
