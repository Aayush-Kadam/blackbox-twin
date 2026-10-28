"""Admission limits for repeated local demos, not a filesystem or OS quota."""

import stat


def storage_size(root, max_files=10000):
    try:
        root.lstat()
    except FileNotFoundError:
        return 0
    total, seen, pending = 0, 0, [root]
    while pending:
        path = pending.pop()
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
        ):
            raise ValueError("Linked paths are not accepted in live output storage")
        seen += 1
        if seen > max_files:
            raise ValueError("Live output storage has too many entries")
        if stat.S_ISDIR(info.st_mode):
            pending.extend(path.iterdir())
        elif stat.S_ISREG(info.st_mode):
            total += info.st_size
    return total
