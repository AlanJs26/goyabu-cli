import re
from .goyabucli.scraperManager import ScraperManager

manager = ScraperManager()

working_dict = manager.test(verbose=True)

readmefile = 'README.md'

# match pattern (<variable-*.?-tag>)(`*.?`)
# example: (<variable-VERSION-tag>)(`1.1`)
with open(readmefile,"r") as f:
  content = f.read()

# update readme variables
for key, value in working_dict.items():
  pattern = r"\<!--{}--\>:.+:".format(key)
  replacement = r"<!--{}-->:{}:".format(key, 'heavy_check_mark' if value else 'x')
  content = re.sub(pattern, replacement, content)

with open(readmefile,"w") as f:
  f.write(content)
