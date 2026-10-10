def is_reparse_point(entry) -> bool:
    """
    Return True if a scandir DirEntry is a reparse point (symlink or NTFS
    junction). Cleanup code must NEVER recurse into these: a junction inside
    a temp/Downloads tree can point outside it, and deleting through it would
    destroy files the user never asked us to touch.

    Fail-closed: if we cannot determine the type, treat it as a reparse
    point (skip it).
    """
    is_junction = getattr(entry, "is_junction", None)
    if callable(is_junction):
        # Python 3.12+: explicit junction detection.
        try:
            if is_junction():
                return True
        except OSError:
            return True
    try:
        attrs = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
        FILE_ATTRIBUTE_REPARSE_POINT = 0x400
        if attrs & FILE_ATTRIBUTE_REPARSE_POINT:
            return True
    except OSError:
        return True
    # Plain symlinks: is_file()/is_dir() with follow_symlinks=False already
    # return False for these, but check explicitly for clarity.
    try:
        if entry.is_symlink():
            return True
    except OSError:
        return True
    return False
