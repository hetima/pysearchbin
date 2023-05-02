# pysearchbin

based on https://github.com/Sepero/SearchBin

## Install

```
pip install git+https://github.com/hetima/pysearchbin.git
```

## Usage
```
search_hex(file_path, pattern, max_matches = 999, start = 0, end = 0, bsize = 0) => list[int]

search_text(file_path, pattern, max_matches = 999, start = 0, end = 0, bsize = 0) => list[int]

search_one_hex(file_path, pattern, start = 0, end = 0, bsize = 0) => int

search_one_text(file_path, pattern, start = 0, end = 0, bsize = 0) => int
```

examples:

```
import pysearchbin

results = pysearchbin.search_hex(file_path, "01020304????07")
results = pysearchbin.search_text(file_path, "aaaaaaa")
if len(results) > 0:
    pass

result = pysearchbin.search_one_hex(file_path, "aaaaaaa")
if result >= 0:
    pass

```

`??` is wild card.


