import uuid


def create_short_uuid():
    return str(uuid.uuid4())[:8]
