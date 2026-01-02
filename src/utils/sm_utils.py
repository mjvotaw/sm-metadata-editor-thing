import re
itl_brackets = re.compile(r"\[[\w\d]+?\]", re.IGNORECASE)

strip_regexes = [
    itl_brackets
]

strip_strings = [
    "(No CMOD)",
    "(Hard)",
    "(Medium)",
    "(Beginner)",
]
    
def strip_common_sm_words(some_string: str) -> str:
  if not some_string:
    return some_string

  result = some_string
  # remove literal strings (case-insensitive)
  for s in strip_strings:
    if not s:
      continue
    result = re.sub(re.escape(s), "", result, flags=re.IGNORECASE)

  # remove regex patterns
  for pattern in strip_regexes:
    result = pattern.sub("", result)

  # normalize whitespace and trim
  result = re.sub(r"\s+", " ", result).strip()
  return result