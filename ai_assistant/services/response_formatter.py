import re
from typing import List, Dict, Any

class ResponseFormatter:
    """
    Utility class to format raw text outputs from AI models into structural shapes
    like lists, tables, markdown components, and code blocks.
    """

    @staticmethod
    def to_plain_text(raw_text: str) -> str:
        """
        Clean raw text and return plain text.
        """
        if not raw_text:
            return ""
        # Remove markdown bold markers and clean newlines
        text = re.sub(r'\*\*(.*?)\*\*|__(.*?)__', r'\1\2', raw_text)
        return text.strip()

    @staticmethod
    def to_markdown(raw_text: str) -> str:
        """
        Retain markdown formatting (e.g. bold, code blocks, lists, tables).
        Ensure extra consecutive blank lines are consolidated.
        """
        if not raw_text:
            return ""
        return re.sub(r'\n{3,}', '\n\n', raw_text).strip()

    @staticmethod
    def to_bullets(raw_text: str) -> List[str]:
        """
        Split a block of text into individual bullet items.
        """
        if not raw_text:
            return []
        lines = re.split(r'\n+|- |\* ', raw_text)
        return [line.strip() for line in lines if line.strip()]

    @staticmethod
    def to_numbered_list(raw_text: str) -> List[str]:
        """
        Split a block of text into ordered numbered list items.
        """
        if not raw_text:
            return []
        # Match lines starting with numbers followed by periods (e.g. "1. Item")
        lines = re.split(r'\n+|\d+\.\s+', raw_text)
        return [line.strip() for line in lines if line.strip()]

    @staticmethod
    def parse_code_blocks(raw_text: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from markdown (e.g. ```python ... ```).
        Returns list of dicts: [{"language": "python", "code": "..."}]
        """
        if not raw_text:
            return []
        blocks = []
        pattern = r'```(\w*)\n(.*?)\n```'
        matches = re.findall(pattern, raw_text, re.DOTALL)
        for lang, code in matches:
            blocks.append({
                "language": lang or "txt",
                "code": code.strip()
            })
        return blocks

    @staticmethod
    def parse_tables(raw_text: str) -> List[List[List[str]]]:
        """
        Parse markdown tables into matrix grid rows.
        Format: | Header 1 | Header 2 | -> [["Header 1", "Header 2"], ...]
        """
        if not raw_text:
            return []
        tables = []
        # Find lines starting/ending with pipes
        table_matches = re.findall(r'((?:\|[^\n]+\|\r?\n?)+)', raw_text)
        for tbl in table_matches:
            grid = []
            lines = tbl.strip().split('\n')
            for line in lines:
                # Skip divider rows like |---|---|
                if re.match(r'^\|[\s:-|]+$', line):
                    continue
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if cells:
                    grid.append(cells)
            if grid:
                tables.append(grid)
        return tables
