"""
Hard Math Problems
------------------
Presents difficult mathematical problems that require genuine reasoning.
These problems are designed so that a model relying on training-data memorization
will fail, while a model with true reasoning capability can solve them.

Graded by LLM judge — exact match is not possible here.
"""

TEST_ID = "medium_math"
TEST_NAME = "Medium Math Problems"
GRADING = "llm_judge"
TEST_DESCRIPTION = "Standard math problems — telescoping series, derivatives, combinatorics"

PROBLEMS = [
    {
        "id": "infinite_series",
        "prompt": "Compute the exact value of the infinite series: sum_{n=1}^{infinity} 1/(n*(n+1)). Show your work.",
        "answer": "Using partial fractions: 1/(n(n+1)) = 1/n - 1/(n+1). This is a telescoping series:\n(1/1 - 1/2) + (1/2 - 1/3) + (1/3 - 1/4) + ... = 1\nThe sum equals 1.",
        "expected_key_steps": ["partial fractions", "telescoping", "answer is 1"],
        "distractor_answer": "The answer is pi/6 (confusing with the Basel problem sum of 1/n^2)",
        "correct_behavior": "Uses partial fraction decomposition to show telescoping, arrives at 1.",
        "bad_behavior": "Confuses with Basel problem (pi^2/6), gives wrong answer, or cannot justify.",
    },
    {
        "id": "derivative_without_rules",
        "prompt": "Using only the limit definition of the derivative (not any differentiation rules), compute d/dx [x^3] at x = 2. That is, evaluate lim_{h->0} [(2+h)^3 - 8]/h. Show all steps.",
        "answer": "Expand (2+h)^3 = 8 + 12h + 6h^2 + h^3\nSubtract 8: 12h + 6h^2 + h^3\nDivide by h: 12 + 6h + h^2\nTake limit h->0: 12\nThe derivative of x^3 at x=2 is 12. (Check: d/dx[x^3] = 3x^2, at x=2: 3*4 = 12.)",
        "expected_key_steps": ["expand (2+h)^3", "divide by h", "limit gives 12"],
        "distractor_answer": "Uses the power rule directly without showing the limit work, or makes an algebra error.",
        "correct_behavior": "Expands (2+h)^3 correctly, cancels h, takes limit to get 12.",
        "bad_behavior": "Just says '3*4=12' using the power rule without the limit, or expands incorrectly.",
    },
    {
        "id": "combinatorics_with_constraints",
        "prompt": "How many ways can you arrange the letters of the word 'MISSISSIPPI' such that no two S's are adjacent? Show your work.",
        "answer": "First arrange non-S letters: M, I, I, I, I, P, P = 7 letters with 4 I's and 2 P's.\nWays = 7!/(4!*2!) = 5040/(24*2) = 105.\nThese 7 letters create 8 slots (before, between, after): _X_X_X_X_X_X_X_\nChoose 4 of the 8 slots for the S's: C(8,4) = 70.\nTotal = 105 * 70 = 7350.",
        "expected_key_steps": ["arrange non-S letters: 105 ways", "choose 4 of 8 slots: 70", "product = 7350"],
        "distractor_answer": "Ignores the constraint and computes 11!/(4!*4!*2!) = 34650, or makes a slot-counting error.",
        "correct_behavior": "Correctly uses gap method: arrange non-S, then place S's in gaps.",
        "bad_behavior": "Ignores the adjacency constraint, or miscounts the number of available slots.",
    },
]

# For a single run, we pick one problem. For repeat runs we can rotate.


def get_prompt(problem_index=0):
    problem = PROBLEMS[problem_index % len(PROBLEMS)]
    return problem["prompt"], problem


def get_all_prompts():
    """Return all problems as (prompt, problem_meta) tuples."""
    return [(p["prompt"], p) for p in PROBLEMS]


JUDGE_RUBRIC = """You are a strict evaluator assessing whether an AI model correctly solved a difficult math problem using genuine reasoning.

The problem was:
{prompt}

The correct answer and key steps:
{answer}

Expected key steps: {expected_key_steps}

A common wrong approach (distractor): {distractor_answer}

Correct behavior: {correct_behavior}
Bad behavior: {bad_behavior}

The model's response was:
---
{response}
---

Score the model 0-100 using these criteria:
- 90-100: Correct answer with valid reasoning. All key steps shown clearly. No significant errors.
- 70-89: Correct answer but minor gaps in reasoning, OR correct approach with a small arithmetic error that doesn't affect the final answer significantly.
- 40-69: Partially correct. Shows some valid steps but makes a significant error. May have the right approach but wrong execution.
- 10-39: Mostly incorrect. Some relevant math but major conceptual errors. May use a wrong method entirely.
- 0-9: Completely wrong. Nonsense, refuses to attempt, or gives an answer with no valid reasoning.

passed = true if score >= 70.

Return ONLY a JSON object like this:
{{"score": 85, "passed": true, "details": "Correctly used partial fractions and telescoping series to arrive at the answer 1."}}
"""


def grade_problem(problem, response_text):
    """Returns the filled rubric string to send to the judge."""
    return JUDGE_RUBRIC.format(
        prompt=problem["prompt"],
        answer=problem["answer"],
        expected_key_steps=", ".join(problem["expected_key_steps"]),
        distractor_answer=problem["distractor_answer"],
        correct_behavior=problem["correct_behavior"],
        bad_behavior=problem["bad_behavior"],
        response=response_text,
    )