from __future__ import annotations


class MemorySummarizer:
    def summarize(self, fragments: list[str]) -> str:
        if not fragments:
            return "No memory fragments available."
        return " | ".join(fragment.strip() for fragment in fragments if fragment.strip())
