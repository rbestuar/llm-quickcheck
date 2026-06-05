"""
Hard Code Challenges
--------------------
Tests genuine code reasoning using subtle bugs that require actual understanding.
NOT textbook implementations — these are bugs that pattern-matching will miss.
"""

TEST_ID = "medium_code"
TEST_NAME = "Medium Code Challenges"
GRADING = "llm_judge"
TEST_DESCRIPTION = "Classic Python gotchas — shallow copy, off-by-one, mutable defaults"

CHALLENGES = [
    {
        "id": "silent_data_corruption",
        "prompt": """Find the bug in this Python function. It is supposed to return a deep copy of a list of dicts, but it has a subtle data corruption bug. Explain exactly what the bug is, why it causes corruption, and provide the corrected code.

````````python
def deep_copy_records(records):
    result = []
    empty = {}
    for record in records:
        new_record = empty.copy()
        new_record.update(record)
        result.append(new_record)
    return result

data = [{"id": 1, "tags": ["a", "b"]}, {"id": 2, "tags": ["c"]}]
copied = deep_copy_records(data)
copied[0]["tags"].append("z")
print(data[0]["tags"])  # What does this print and why?
```````""",
        "correct_answer": "dict.copy() is a shallow copy. The nested tags list is not copied — both copied[0][tags] and data[0][tags] point to the same list object. Appending z to the copy also mutates the original. Output is [a, b, z]. Fix: use copy.deepcopy().",
        "expected_key_steps": [
            "identifies shallow copy as root cause",
            "explains nested lists are shared references",
            "correctly predicts output as [a, b, z]",
            "fix uses deepcopy or equivalent"
        ],
        "distractor_answer": "Says the bug is empty={} defined outside the loop, missing that shallow copy of nested objects is the real issue.",
        "correct_behavior": "Identifies shallow copy, explains shared reference, predicts [a, b, z], fixes with deepcopy.",
        "bad_behavior": "Misidentifies bug as empty dict reuse, fails to predict output correctly, or fix still has shallow copy problem.",
    },
    {
        "id": "off_by_one_generator",
        "prompt": """This function is supposed to return all sliding windows of size n over a list. It has a subtle off-by-one bug. Find it, explain when it triggers, and fix it.

``````python
def sliding_windows(lst, n):
    windows = []
    for i in range(len(lst) - n):
        windows.append(lst[i:i+n])
    return windows

print(sliding_windows([1,2,3,4,5], 3))  # Expected: [[1,2,3],[2,3,4],[3,4,5]]
print(sliding_windows([1,2,3], 3))       # Expected: [[1,2,3]]
print(sliding_windows([1,2], 3))         # Expected: []
`````""",
        "correct_answer": "range(len(lst) - n) should be range(len(lst) - n + 1). With [1,2,3,4,5] and n=3, range(2) gives i=0,1 producing only [[1,2,3],[2,3,4]] — the last window [3,4,5] is always dropped. With [1,2,3] and n=3, range(0) gives [] instead of [[1,2,3]].",
        "expected_key_steps": [
            "identifies range(len(lst) - n) as wrong",
            "correct fix is range(len(lst) - n + 1)",
            "explains last window is always missing",
            "identifies both test case 1 and 2 are broken"
        ],
        "distractor_answer": "Says the slicing lst[i:i+n] is wrong, or only notices one of the two broken test cases.",
        "correct_behavior": "Identifies range end should be len(lst)-n+1, explains last window is dropped, notes both cases 1 and 2 fail.",
        "bad_behavior": "Only catches one broken case, gives wrong fix, or misidentifies which line has the bug.",
    },
    {
        "id": "mutable_default_arg",
        "prompt": """This Python class has a classic but dangerous bug. Identify it, explain why Python causes it, predict the exact output, and give the correct implementation.

````python
class TaskQueue:
    def __init__(self, tasks=[]):
        self.tasks = tasks

    def add_task(self, task):
        self.tasks.append(task)
        return self

    def get_tasks(self):
        return self.tasks

q1 = TaskQueue()
q1.add_task("write tests")
q1.add_task("deploy")

q2 = TaskQueue()
q2.add_task("fix bug")

print(q1.get_tasks())
print(q2.get_tasks())
```""",
        "correct_answer": "Mutable default argument. Default values are evaluated once at function definition time. All TaskQueue() instances share the same list object. Output: both q1 and q2 print [write tests, deploy, fix bug]. Fix: use tasks=None and set self.tasks = tasks if tasks is not None else [].",
        "expected_key_steps": [
            "identifies mutable default argument antipattern",
            "explains default evaluated once at definition time",
            "correctly predicts both queues print all 3 tasks",
            "fix uses None as default sentinel"
        ],
        "distractor_answer": "Says bug is that add_task returns self, or tasks should be copied, missing the shared default object entirely.",
        "correct_behavior": "Names mutable default argument antipattern, predicts both queues show all 3 tasks, gives None sentinel fix.",
        "bad_behavior": "Misidentifies bug, predicts wrong output, or fix still uses mutable default.",
    },
]


def get_prompt(challenge_index=0):
    challenge = CHALLENGES[challenge_index % len(CHALLENGES)]
    return challenge["prompt"], challenge


def get_all_prompts():
    return [(c["prompt"], c) for c in CHALLENGES]


JUDGE_RUBRIC = """You are evaluating whether an AI correctly identified and fixed a subtle Python bug.

The challenge:
{prompt}

Correct answer:
{correct_answer}

Key steps the model must hit:
{expected_key_steps}

Common wrong answer:
{distractor_answer}

Correct behavior: {correct_behavior}
Bad behavior: {bad_behavior}

Model response:
---
{response}
---

Score 0-100:
- 90-100: All key steps hit. Correct bug, correct why, correct output prediction, correct fix. Concise.
- 75-89: Bug and fix correct but misses one key step or has minor explanation gap.
- 50-74: Right area but wrong root cause, OR correct cause but wrong fix.
- 20-49: Partially on track but significant conceptual errors.
- 0-19: Wrong bug, wrong output, wrong fix, or correct answer with no explanation.

passed = true if score >= 70.
Return ONLY JSON: {{"score": 85, "passed": true, "details": "Correctly identified shallow copy bug, predicted output, fixed with deepcopy."}}"""


def grade_challenge(challenge, response_text):
    return JUDGE_RUBRIC.format(
        prompt=challenge["prompt"],
        correct_answer=challenge["correct_answer"],
        expected_key_steps="\n".join(f"- {s}" for s in challenge["expected_key_steps"]),
        distractor_answer=challenge["distractor_answer"],
        correct_behavior=challenge["correct_behavior"],
        bad_behavior=challenge["bad_behavior"],
        response=response_text,
    )
