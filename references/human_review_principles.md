# Human Review Principles

How to phrase the feedback once you've found it. The
[`review_criteria.md`](./review_criteria.md) file covers *what* to look for;
this one covers *how* to communicate it without making the author wish they
hadn't asked.

This is the "human" half of the skill. The mechanical bits (fetching the diff,
generating files, posting comments) can be automated. The judgement and tone
can't. If a person is named on the review, the words should sound like that
person.

> Distilled from the
> [`code-review-excellence`](https://github.com/wshobson/agents/blob/main/plugins/developer-essentials/skills/code-review-excellence/SKILL.md)
> skill, and refined through opinion.

## What review is for

- Catch bugs and edge cases.
- Make the code easier to maintain than what was there before.
- Share knowledge across the team.
- Build culture - people remember how reviews felt.

## What review is NOT for

- Showing off knowledge.
- Nitpicking formatting (let linters do that).
- Blocking progress when the issue is taste, not substance.
- Rewriting the PR to your personal preference.

If most of your comments fall in those four buckets, you're not reviewing - you
are obstructing.

## Severity vocabulary

Always tag the severity. The author should be able to tell at a glance which
comments require a fix and which are FYI.

| Tag             | Use it when                                                  |
|-----------------|--------------------------------------------------------------|
| 🔴 `[blocking]` | Must be fixed before merge. Bug, security issue, broken test |
| 🟡 `[important]`| Should be fixed; willing to discuss if the author disagrees  |
| 🟢 `[nit]`      | Personal preference or trivial polish. Author can ignore     |
| 💡 `[suggestion]`| Future idea, separate PR. Not blocking this one             |
| 📚 `[learning]` | Educational FYI. No action requested                         |
| ❓ `[question]` | You don't know enough to say if it's right. Ask              |
| 🎉 `[praise]`   | This was nice. Say so out loud                              |

If you can't decide between `[important]` and `[nit]`, it's probably `[nit]`.

## The Question Approach

Asking is friendlier than asserting, and it leaves room for you to be wrong:

```diff
- "This will fail if the list is empty."
+ "What happens if `items` is empty here? I might be misreading."

- "You need error handling here."
+ "How should this behave if the API call fails?"

- "This is inefficient."
+ "I see this loops through all users. Have we tested this with the kind of
+  list size we'd see in production?"
```

If you genuinely don't know, asking is honest. If you do know, asking still
works - it gives the author space to spot the issue themselves, which lands
better than being told.

## Suggest, don't command

Collaborative phrasing. End with "what do you think?" if you're not sure:

```diff
- "Change this to async/await."
+ "Suggestion: async/await might read more cleanly here. What do you think?"

- "Extract this into a function."
+ "This logic appears in three places now - would it make sense to pull it
+  into a shared helper?"
```

Direct commands are appropriate for `[blocking]` security issues. For
everything else, suggest.

## Modified sandwich method

The classic "praise / criticism / praise" sandwich feels fake because the
praise is invented. Replace it with **Context → Specific Issue → Helpful
Solution**:

> The payment processing logic is currently inline in the controller, which
> makes it hard to unit test.
>
> `calculateTotal()` mixes tax, discounts, and DB queries in one function,
> so I can't test the tax logic without standing up a test database.
>
> Could we extract this into a `PaymentService`? Happy to pair on it if
> useful.

Three sentences. Says the thing without making it personal.

## Handling disagreements

When the author pushes back:

1. **Seek to understand first.** "Help me understand your approach - what led
   you to choose this pattern?"
2. **Acknowledge valid points.** "You're right about X, I hadn't considered
   that."
3. **Provide data.** If you're concerned about performance or security, ask
   for a benchmark or a reference rather than asserting.
4. **Escalate when needed.** "Let's get [architect] to weigh in on this."
5. **Know when to let it go.** If it's working, not buggy, and the
   disagreement is about taste, approve it. Perfection is the enemy of
   shipping.

Two reasonable engineers can have different opinions on the same code. That
doesn't mean one is wrong.

## What to leave to tooling, not humans

Don't waste review cycles on:

- Code formatting → linter / Prettier / Black / gofmt
- Import organisation → linter
- Trivial typos → can mention once, but don't make a thing of it
- Lint rule violations → CI

If you find yourself writing the same nit on every PR, that's a signal to
configure tooling, not to keep writing the nit.

## Best practices for the reviewer

- **Reply within 24 hours** if you can. PRs rotting in the queue cost the team
  more than an imperfect review.
- **Cap PR size**. If it's >400 lines and not a mechanical refactor, ask the
  author to split it. Reviews get worse linearly with size.
- **Time-box the review session**. After ~60 minutes, review quality drops.
  Take a break, come back.
- **Be available for follow-up**. Don't request changes and disappear.
- **Approve when you can**. "Approve with comments" beats "request changes"
  for nits the author can choose to address.

## Common pitfalls

- **Perfectionism**: blocking PRs for personal style preferences.
- **Scope creep**: "while you're at it, can you also...".
- **Inconsistent standards**: stricter reviews for some authors than others.
- **Bike-shedding**: extended debate over trivial details.
- **Rubber stamping**: approving without actually reading.
- **Ghost reviews**: requesting changes then never coming back to re-review.

## A short template for the human.md file

```markdown
## Summary

[One paragraph: what this PR does and your overall take.]

## [blocking] Issues

[Only if there are real blockers. Be specific.]

## [important] Notes

[Should be addressed; willing to discuss.]

## [nit] / [suggestion]

[Optional polish. Author can take or leave.]

## [praise]

[At least one thing, when there's something worth calling out.]

## Recommendation

Approve / Request changes / Comment.
```

If the review fits this skeleton in your own voice, the human touch is
preserved. If it reads like a checklist robot, edit it before posting.
