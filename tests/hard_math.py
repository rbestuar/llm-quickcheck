"""
Hard Math Problems
------------------
Brutally difficult problems designed to expose pattern-matching vs genuine reasoning.
Each problem has a highly plausible wrong answer that most LLMs will produce.
"""

TEST_ID = "hard_math"
TEST_NAME = "Hard Math Problems"
GRADING = "llm_judge"
TEST_DESCRIPTION = "Multi-step math where the obvious approach gives the wrong answer — designed to fail pattern-matching"

PROBLEMS = [
    {
        "id": "monty_hall_variant",
        "prompt": "You are on a game show with 4 doors. Behind one door is a car, behind the other three are goats. You pick door 1. The host (who always knows what is behind every door and always opens a door with a goat) opens door 3, revealing a goat. He then offers you a choice: stick with door 1, switch to door 2, or switch to door 4.\n\nWhat is the probability of winning if you:\na) Stay with door 1\nb) Switch to door 2\nc) Switch to door 4\n\nShow your full reasoning. Does it matter which door you switch to?",
        "correct_answer": "Stay: 1/4. Switch to either door 2 or door 4: 3/8 each. Total switching probability = 3/4, split equally between the two remaining doors since the host gave no information distinguishing door 2 from door 4. Key insight: staying gives 1/4, switching to a specific door gives 3/8, not 1/3. Most people wrongly say 1/3 for switching because they apply the 3-door Monty Hall logic incorrectly. In the 4-door version, host opening one door concentrates the 3/4 probability across TWO remaining doors equally, 3/8 each, not one.",
        "expected_key_steps": [
            "stay probability is 1/4",
            "switching probability is 3/4 total split between two doors",
            "each switch door is 3/8 not 1/3",
            "recognizes naive 1/3 answer is wrong"
        ],
        "distractor_answer": "Stay: 1/4, Switch: 1/3 for each remaining door — applies 3-door logic to 4-door problem incorrectly.",
        "correct_behavior": "Correctly computes stay=1/4, each switch=3/8, explains why 1/3 is wrong, notes host reveals no info distinguishing door 2 from door 4.",
        "bad_behavior": "Says switching gives 1/3 per door, or says all three remaining doors are equal at 1/3, or fails to account for host knowledge.",
    },
    {
        "id": "expected_value_trap",
        "prompt": "A biased coin has probability p=0.6 of heads. You start with $100. On each flip, heads multiplies your money by 1.5, tails multiplies by 0.5. You play 1000 flips.\n\nA friend says: the expected value per flip is 0.6*1.5 + 0.4*0.5 = 1.1, so after 1000 flips your expected value is 100 * 1.1^1000, which is astronomical. You should definitely play!\n\nIs your friend correct? What will most likely happen to your $100 after 1000 flips? Show your full mathematical reasoning.",
        "correct_answer": "The friend is wrong about what matters. The arithmetic expected value is 100 * 1.1^1000 but misleading. The geometric mean per flip is 1.5^0.6 * 0.5^0.4 which is approximately 0.815. Since 0.815 < 1, after 1000 flips the median outcome is 100 * 0.815^1000 which is essentially $0. The expected value is dominated by astronomically rare lucky streaks. In practice with probability approaching 1 you go broke. This is the volatility decay trap: the correct metric for repeated multiplicative bets is the geometric mean, not arithmetic mean.",
        "expected_key_steps": [
            "geometric mean per flip is 1.5^0.6 * 0.5^0.4 approximately 0.815",
            "geometric mean less than 1 means ruin in the long run",
            "arithmetic expected value is misleading for multiplicative processes",
            "median outcome approaches 0 despite high arithmetic expectation"
        ],
        "distractor_answer": "Agrees with the friend that expected value of 1.1^1000 means you should play, missing the geometric mean analysis entirely.",
        "correct_behavior": "Identifies geometric mean approximately 0.815 < 1, explains arithmetic vs geometric mean distinction, concludes you almost certainly go broke.",
        "bad_behavior": "Agrees with the friend, only computes arithmetic expected value, fails to compute geometric mean, or says the game is favorable.",
    },
    {
        "id": "calculus_trap",
        "prompt": "Evaluate this limit and show all work:\n\nlim_{x->0} [x - sin(x)] / x^3\n\nA student applies L Hopital three times and gets 1/6. Are they correct? Is their method valid? Also solve it using the Taylor series method and confirm whether both methods agree.",
        "correct_answer": "Answer is 1/6. L Hopital is valid here since each step produces 0/0: first application gives [1-cos(x)]/3x^2 which is 0/0 at x=0, second gives sin(x)/6x which is 0/0 at x=0, third gives cos(x)/6 = 1/6. Taylor series confirmation: sin(x) = x - x^3/6 + x^5/120 - ..., so x - sin(x) = x^3/6 - x^5/120 + ..., dividing by x^3 gives 1/6 - x^2/120 + ..., limit is 1/6. Both methods agree. A strong response verifies 0/0 form at each L Hopital step AND independently confirms with Taylor series.",
        "expected_key_steps": [
            "verifies 0/0 indeterminate form at each L Hopital step",
            "correctly applies L Hopital three times to get 1/6",
            "Taylor expansion sin(x) = x - x^3/6 + higher order terms",
            "x - sin(x) = x^3/6 + higher order terms",
            "both methods confirm 1/6"
        ],
        "distractor_answer": "Gets 1/6 via L Hopital only without verifying indeterminate form at each step, or makes sign error in Taylor expansion getting -1/6.",
        "correct_behavior": "Confirms 1/6, verifies 0/0 at each L Hopital step, derives independently via Taylor series, notes where sign errors commonly occur.",
        "bad_behavior": "Gets wrong answer, skips verification of indeterminate form, makes sign error in Taylor expansion, or only uses one method.",
    },
]


def get_prompt(problem_index=0):
    problem = PROBLEMS[problem_index % len(PROBLEMS)]
    return problem["prompt"], problem


def get_all_prompts():
    return [(p["prompt"], p) for p in PROBLEMS]


JUDGE_RUBRIC = """You are evaluating whether an AI model correctly solved a brutally difficult math problem.

The problem:
{prompt}

Correct answer and key reasoning:
{correct_answer}

Key steps the model MUST hit:
{expected_key_steps}

Common wrong answer (what a pattern-matching model produces):
{distractor_answer}

Correct behavior: {correct_behavior}
Bad behavior: {bad_behavior}

Model response:
---
{response}
---

Score 0-100. Be brutal:
- 90-100: Hits ALL key steps, correct answer, correct reasoning, no errors, concise.
- 75-89: Correct answer but misses one key step or has a minor reasoning gap.
- 50-74: Gets the right answer via incomplete or partially wrong reasoning.
- 20-49: Produces the distractor answer or has major conceptual errors.
- 0-19: Wrong answer, refuses to engage, or complete conceptual failure.

passed = true if score >= 70.
Return ONLY JSON: {{"score": 72, "passed": true, "details": "Got 1/6 via L Hopital but skipped Taylor verification."}}"""


def grade_problem(problem, response_text):
    return JUDGE_RUBRIC.format(
        prompt=problem["prompt"],
        correct_answer=problem["correct_answer"],
        expected_key_steps="\n".join(f"- {s}" for s in problem["expected_key_steps"]),
        distractor_answer=problem["distractor_answer"],
        correct_behavior=problem["correct_behavior"],
        bad_behavior=problem["bad_behavior"],
        response=response_text,
    )
