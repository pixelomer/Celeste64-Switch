#!/usr/bin/env python3
"""Allow 32 KiB copied uploads while preserving the original 8 KiB flush threshold."""
from pathlib import Path
import sys
root = Path(sys.argv[1])
p = root / 'src/mesa/main/glthread.h'
s = p.read_text()
a = '#define MARSHAL_MAX_CMD_SIZE (8 * 1024)'
assert s.count(a) == 1
p.write_text(s.replace(a, '#define MARSHAL_MAX_CMD_SIZE (32 * 1024)'))
p = root / 'src/mesa/main/glthread_marshal.h'
s = p.read_text()
a = 'next->used + size > MARSHAL_MAX_CMD_SIZE'
assert s.count(a) == 1
p.write_text(s.replace(a, 'next->used + size > (8 * 1024)'))
