

"""
based on https://github.com/Sepero/SearchBin


search_hex(file_path: str, pattern, max_matches: int = 999, start: int = 0, end: int = 0, bsize: int = 0) => list[int]
search_text(file_path: str, pattern, max_matches: int = 999, start: int = 0, end: int = 0, bsize: int = 0) => list[int]
search_one_hex(file_path: str, pattern, start: int = 0, end: int = 0, bsize: int = 0) => int
search_one_text(file_path: str, pattern, start: int = 0, end: int = 0, bsize: int = 0) => int

examples:
results = search_hex(file_path, "deadbeef0000")
results = search_text(file_path, "aaaaaaa")
if len(result) > 0:
    pass

result = search_one_hex(file_path, "aaaaaaa")
if result > 0:
    pass


license: BSD 2-Clause License, 2012, Sepero
license: http://www.opensource.org/licenses/BSD-2-Clause
"""

# from __future__ import unicode_literals
import re
import sys

# Global variables.
VERSION="0.0.1"
DEBUG = False
STDOUT = sys.stdout


def _exit_error(code, option="", err=None):
    """
	Error information is kept here for the purposes of easier management and possibly language tranlation.
	Returns nothing. All calls exit the program, error status 128.
	"""
    error_codes = {
     "Xpatterns":
      "Cannot search for multiple patterns. '-t -p -f'",
     "0patterns":
      "No pattern to search for was supplied. '-t -p -f'",
     "decode":
      "The pattern string is invalid.\n" + str(option),
     "bsize":
      "The buffer size must be at least %s bytes." % str(option),
     "sizes":
      "Size parameters (-b -s -e -m) must be in decimal format.",
     "fpattern":
      "No pattern file found named: %s" % option,
     "openfile":
      "Failed opening file: %s" % option,
     "read":
      "Failed reading from file: %s" % option,

    }

    import traceback
    sys.stderr.write(traceback.format_exc() + "\n")
    if not DEBUG:
        sys.stderr.write("version: %s\n" % VERSION)
        if err: sys.stderr.write("%s\n" % str(err))
    sys.stderr.write("Error <%s>: %s\n\n" % (code, error_codes[code]))
    if __name__ == "__main__":
        sys.exit(128) # Exit under normal operation.
    raise # Raise error on unittest or other execution.


"""
=Patterns=
A pattern is a list. It represents the division between known and unknown
bytes to search for. All hex/text/file input is converted to a pattern.
Examples of conversions:
hex "31??33" becomes ['A', 'C']  # Everything is converted internally to strings, even though they may not be printable characters.
text "A?C"   becomes ['A', 'C']
text "A??C"  becomes ['A', '', 'C']
"""
def hex_to_pattern(hex):
    """ Converts a hex string into a pattern. """
    ret = []
    pattern = hex
    if hex[:2] == "0x": # Remove "0x" from start if it exists.
        pattern = hex[2:]
    try:
        ret = [ p for p in pattern.split("??") ]
        return [ bytes.fromhex(p) for p in ret ]
    except(TypeError, ValueError):
        e = sys.exc_info()[1]
        _exit_error("decode", hex, e)


def text_to_pattern(text):
    """ Converts a text string into a pattern. """
    return [ t.encode('utf-8') for t in text.split("?") ]



def file_to_pattern(fname):
    """ Converts a file into a pattern. """
    try: # If file specified, read it into memory.
        with open(fname, "rb") as f:
            return [f.read()]
    except IOError:
        e = sys.exc_info()[1]
        _exit_error("fpattern", fname, e)


# We will be keeping the parsed args object and editing its attributes!
def verify_args(ar):
    """
	Verify that all the parsed args are correct and work well together.
	Returns the modified args object.
	"""
    # Make sure that exactly 1 pattern argument was given.
    all_patterns = list(filter(None, [ar.fpattern, ar.ppattern, ar.tpattern]))
    if len(all_patterns) > 1:
        _exit_error("Xpatterns")
    if len(all_patterns) == 0:
        _exit_error("0patterns")

    # Create a new variable ar.pattern, and fill it with
    # whichever pattern we have -t -f -p. ar.pattern will be a list.
    if ar.fpattern:
        ar.pattern = file_to_pattern(ar.fpattern)
    elif ar.tpattern:
        ar.pattern = text_to_pattern(ar.tpattern)
    else:
        ar.pattern = hex_to_pattern(ar.ppattern)

    # Convert all number args from strings into long integers.
    try:
        for attr in [ "bsize", "max_matches", "start", "end" ]:
            if getattr(ar, attr):
                setattr(ar, attr, int(getattr(ar, attr)))
    except ValueError:
        e = sys.exc_info()[1]
        _exit_error("sizes", err=e)

    # Buffer size must be at least double maximum pattern size.
    if ar.bsize:
        if ar.bsize < len("?".join(ar.pattern)) * 2:
            ar.bsize = 2**23
    else:
        ar.bsize = len(b"".join(ar.pattern)) * 2
        ar.bsize = max(ar.bsize, 2**23) # If bsize is < default, set to default.

    # Set start and end values to 0 if not set.
    ar.start = ar.start or 0
    ar.end = ar.end or 0
    # End must be after start.  :)
    if ar.end and ar.start >= ar.end:
        ar.end = 0

    return ar


def search(ar, fh):
    """
	This function is simply a wrapper to forward needed variables in a way
	to make them all local variables. Accessing local variables is faster than
	accessing object.attribute variables.
	Returns nothing.
	"""
    return _search_loop(ar.start, ar.end, ar.bsize, ar.pattern,
          ar.max_matches, fh.name,
          fh.read, fh.seek)

def _search_loop(start:int, end:int, bsize:int, pattern, max_matches:int,
  fh_name, fh_read, fh_seek):
    """
	Primary search function.
	Returns nothing.
	"""
    result = []
    len_pattern = len(b"?".join(pattern)) # Byte length of pattern.
    read_size = bsize - len_pattern # Amount to read each loop.

    # Convert pattern into a regular expression for insane fast searching.
    pattern = [ re.escape(p) for p in pattern ]
    pattern = b".".join(pattern)
    # Grab regex search function directly to speed up function calls.
    regex_search = re.compile(pattern, re.DOTALL+re.MULTILINE).search

    offset = start or 0
    # Set start reading position in file.
    try:
        if offset:
            fh_seek(offset)
    except IOError:
        e = sys.exc_info()[1]
        _exit_error("read", fh_name, err=e)

    try:
        buffer = fh_read(len_pattern + read_size) # Get initial buffer amount.
        match = regex_search(buffer) # Search for a match in the buffer.
        # Set match to -1 if no match, else set it to the match position.
        match = -1 if match == None else match.start()

        while True: # Begin main loop for searching through a file.
            if match == -1: # No match.
                offset += read_size
                # If end exists and we are beyond end, finish search.
                if end and offset > end:
                    return result
                buffer = buffer[read_size:] # Erase front portion of buffer.
                buffer += fh_read(read_size) # Read more into the buffer.
                match = regex_search(buffer) # Search for next match in the buffer.
                # If there is no match set match to -1, else the matching position.
                match = -1 if match == None else match.start()
            else: # Else- there was a match.
                # If end exists and we are beyond end, finish search.
                if match == -1 and offset + match > end:
                    return result

                # Print matched offset.
                find_offset = offset + match
                # STDOUT.write("%d\n" % (find_offset))
                result.append(find_offset)

                if max_matches:
                    max_matches -= 1
                    if max_matches == 0: # If maximum matches are found, then end.
                        return result

                # Search for next match in the buffer.
                match = regex_search(buffer, match+1)
                match = -1 if match == None else match.start()

            if len(buffer) <= len_pattern: # If finished reading input then end.
                return result

        # Main loop closes here.
    except IOError:
        e = sys.exc_info()[1]
        _exit_error("read", fh_name, e)
    return result

class pysearchbin_arg(object):
    def __init__(self):
        self.fpattern = None
        self.tpattern = None
        self.ppattern = None
        self.pattern = None
        self.max_matches = 0
        self.start = 0
        self.end = 0
        self.bsize = 0

def search_one_hex(file_path: str, pattern, start: int = 0, end: int = 0, bsize: int = 0):
    result =search_hex(file_path, pattern, 1, start, end, bsize)
    if len(result) > 0:
        return result[0]
    return -1

def search_one_text(file_path: str, pattern, start: int = 0, end: int = 0, bsize: int = 0):
    result = search_text(file_path, pattern, 1, start, end, bsize)
    if len(result) > 0:
        return result[0]
    return -1

def search_hex(file_path: str, pattern, max_matches: int = 999, start: int = 0, end: int = 0, bsize: int = 0):
    args = pysearchbin_arg()
    args.ppattern = pattern
    args.max_matches = max_matches
    args.start = start
    args.end = end
    args.bsize = bsize
    args = verify_args(args) # Check arguments for sanity, and edit them a bit.
    result = []
    try:  # Open a filehandler for the filename.
        filehandler = open(file_path, "rb")
        result = search(args, filehandler)
        filehandler.close()
    except IOError:
        e = sys.exc_info()[1]
        _exit_error("openfile", file_path, e)
    return result

def search_text(file_path: str, pattern, max_matches: int = 999, start: int = 0, end: int = 0, bsize: int = 0):
    args = pysearchbin_arg()
    args.tpattern = pattern
    args.max_matches = max_matches
    args.start = start
    args.end = end
    args.bsize = bsize
    args = verify_args(args) # Check arguments for sanity, and edit them a bit.
    result = []
    try: # Open a filehandler for the filename.
        filehandler = open(file_path, "rb")
        result = search(args, filehandler)
        filehandler.close()
    except IOError:
        e = sys.exc_info()[1]
        _exit_error("openfile", file_path, e)
    return result

if __name__ == "__main__":
    pass
