"""
Sudoku Test
-----------
Presents the model with a valid, solvable 9x9 sudoku puzzle.
Expects a fully solved grid back in a defined format.
Graded by exact solution match — no LLM judge needed.
"""

TEST_ID = "sudoku"
TEST_NAME = "Sudoku Solve"
GRADING = "exact"  # grader/llm_judge.py won't be called for this test

# A known hard (but solvable) sudoku puzzle.
# 0 = empty cell.
PUZZLE = [
    [8, 0, 0,  0, 0, 0,  0, 0, 0],
    [0, 0, 3,  6, 0, 0,  0, 0, 0],
    [0, 7, 0,  0, 9, 0,  2, 0, 0],

    [0, 5, 0,  0, 0, 7,  0, 0, 0],
    [0, 0, 0,  0, 4, 5,  7, 0, 0],
    [0, 0, 0,  1, 0, 0,  0, 3, 0],

    [0, 0, 1,  0, 0, 0,  0, 6, 8],
    [0, 0, 8,  5, 0, 0,  0, 1, 0],
    [0, 9, 0,  0, 0, 0,  4, 0, 0],
]

SOLUTION = [
    [8, 1, 2,  7, 5, 3,  6, 4, 9],
    [9, 4, 3,  6, 8, 2,  1, 7, 5],
    [6, 7, 5,  4, 9, 1,  2, 8, 3],

    [1, 5, 4,  2, 3, 7,  8, 9, 6],
    [3, 6, 9,  8, 4, 5,  7, 2, 1],
    [2, 8, 7,  1, 6, 9,  5, 3, 4],

    [5, 2, 1,  9, 7, 4,  3, 6, 8],
    [4, 3, 8,  5, 2, 6,  9, 1, 7],
    [7, 9, 6,  3, 1, 8,  4, 5, 2],
]


def _format_puzzle(grid):
    """Render puzzle as a clean string for the prompt."""
    lines = []
    for i, row in enumerate(grid):
        if i in (3, 6):
            lines.append("------+-------+------")
        cells = []
        for j, val in enumerate(row):
            if j in (3, 6):
                cells.append("|")
            cells.append(str(val) if val != 0 else ".")
        lines.append(" ".join(cells))
    return "\n".join(lines)


def get_prompt():
    puzzle_str = _format_puzzle(PUZZLE)
    return f"""Solve the following Sudoku puzzle. Replace every dot (.) with the correct digit (1-9).

{puzzle_str}

Respond with ONLY the completed grid in the exact same format — 9 rows, digits separated by spaces, using | and --- dividers as shown. No explanation, no extra text."""


def _parse_response(text):
    """Extract a 9x9 grid from model response. Returns list of lists or None."""
    digits = []
    for char in text:
        if char.isdigit() and char != "0":
            digits.append(int(char))
    if len(digits) == 81:
        return [digits[i*9:(i+1)*9] for i in range(9)]
    return None


def grade(response_text):
    """
    Returns a dict:
      score: 0-100
      passed: bool
      details: str
    """
    parsed = _parse_response(response_text)

    if parsed is None:
        return {
            "score": 0,
            "passed": False,
            "details": "Could not parse a 9x9 grid from response."
        }

    if parsed == SOLUTION:
        return {
            "score": 100,
            "passed": True,
            "details": "Perfect solution — all 81 cells correct."
        }

    # Partial credit: count correct cells
    correct = sum(
        1 for r in range(9) for c in range(9)
        if parsed[r][c] == SOLUTION[r][c]
    )
    score = int((correct / 81) * 100)
    return {
        "score": score,
        "passed": False,
        "details": f"{correct}/81 cells correct. Solution was wrong or incomplete."
    }
