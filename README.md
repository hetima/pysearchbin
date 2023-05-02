# pysearchbin

based on https://github.com/Sepero/SearchBin

## Install

```
pip install git+https://github.com/hetima/pysearchbin.git
```

## Usage
```
search_hex(file_path: str, pattern, max_matches: int = 999, start: int = 0, end: int = 0, bsize: int = 0) => list[int]

search_text(file_path: str, pattern, max_matches: int = 999, start: int = 0, end: int = 0, bsize: int = 0) => list[int]

search_one_hex(file_path: str, pattern, start: int = 0, end: int = 0, bsize: int = 0) => int

search_one_text(file_path: str, pattern, start: int = 0, end: int = 0, bsize: int = 0) => int
```
examples:
```
results = search_hex(file_path, "01020304????07")
results = search_text(file_path, "aaaaaaa")
if len(result) > 0:
    pass

result = search_one_hex(file_path, "aaaaaaa")
if result > 0:
    pass

```

