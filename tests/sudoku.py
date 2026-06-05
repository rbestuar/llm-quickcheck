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

SOLUTION = [
    [1, 2, 3, 4],
    [2, 1, 4, 3],
    [3, 4, 1, 2],
    [4, 3, 2, 1],
]


def get_prompt():
    return """You are given a 4x4 grid. Place the numbers 1-4 in each row and each column exactly once (like a mini Sudoku). The following cells are pre-filled:
Row 1, Col 3 = 3
Row 2, Col 4 = 3
Row 3, Col 1 = 3
Row 4, Col 2 = 3

Output only the completed 4x4 grid, one row per line, numbers separated by spaces. No explanation."""


def _parse_response(text):
    """Extract a 4x4 grid from model response. Returns list of lists or None."""
    import re
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    digits_found = []
    current = []
    for char in text:
        if char.isdigit() and char != '0':
            current.append(int(char))
            if len(current) == 16:
                digits_found.append(current[:])
                current = []
        elif char not in ' \t\n|.-+':
            current = []
    if digits_found:
        grid = digits_found[-1]
        return [grid[i*4:(i+1)*4] for i in range(4)]
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
            "details": "Could not parse a 4x4 grid from response."
        }

    if parsed == SOLUTION:
        return {
            "score": 100,
            "passed": True,
            "details": "Perfect solution — all 16 cells correct."
        }

    # Partial credit: count correct cells
    correct = sum(
        1 for r in range(4) for c in range(4)
        if parsed[r][c] == SOLUTION[r][c]
    )
    score = int((correct / 16) * 100)
    return {
        "score": score,
        "passed": False,
        "details": f"{correct}/16 cells correct. Solution was wrong or incomplete."
    }