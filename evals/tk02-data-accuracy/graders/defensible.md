---
type: llm
criteria: Is every figure in the content JSON traceable to a value in the fixture pack, and is the posted range quoted verbatim?
target: {source: file, path: out/TK_02.content.json}
---
Read the content JSON. Every dollar figure, percentage, and pool count must appear in the
fixture pack (the prompt's pack.json). The posted range must be exactly "$115,000-$155,000
base salary + equity". Any figure not in the pack is a fail.
