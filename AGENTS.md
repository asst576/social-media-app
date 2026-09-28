# Project Working Instructions

## Workflow

Use this workflow in order, but never advance to the next phase automatically. The user must explicitly invoke each phase:

`study` -> `plan` -> `execute plan` -> `rendezvous` -> `sync docs`

Stop at the end of each phase and wait for the user's instruction to continue.

### STUDY

When the user says `study`:

- First run `date +%s` to get the current Unix timestamp.
- Analyze the requested problem, feature, or goal.
- Write findings to `doc/study/{unix_timestamp}_{topic}.md`.
- Discuss feasibility, tradeoffs, assumptions, risks, constraints, dependencies, and possible approaches.
- Do not implement code during a study.
- Only modify the study document unless its directory must be created.
- Commit the study with an appropriate Conventional Commit, such as `docs: study <topic>`.
- Stop after completing the study. Do not automatically continue to planning.

### PLAN

When the user says `plan`:

- First run `date +%s`.
- Base the plan on the relevant study and the current repository state.
- Write the plan to `doc/plan/{unix_timestamp}_{topic}.md`.
- Write it as an editable checklist that another coding session can execute.
- Include implementation steps, files likely to change, testing, validation, and documentation updates.
- If human input is required, include an `OPEN QUESTIONS` section near the top.
- Do not implement the plan while writing it.
- Commit the plan with an appropriate Conventional Commit, such as `docs: plan <topic>`.
- Stop after completing the plan. Do not automatically begin implementation.

### EXECUTE PLAN

When the user says `execute plan`:

- Read the specified plan document.
- Check the Git status first using `git status`.
- Review the current repository state before making changes.
- Create a separate Git branch unless instructed otherwise.
- Execute the checklist in the plan.
- Update the plan document as tasks are completed by changing completed items from `[ ]` to `[x]`.
- Run relevant tests.
- Continue until the plan is complete or there is a genuine external roadblock.
- Clearly identify any external or human-required inputs if blocked.
- Use Conventional Commits for meaningful changes.
- Do not merge the branch into `main` during this phase.
- Stop when execution is complete and wait for the user to say `rendezvous`.

### RENDEZVOUS

When the user says `rendezvous`:

- Verify the completed implementation.
- Review the relevant plan and confirm the implementation matches it.
- Run relevant tests.
- Check `git status`.
- Confirm the application is in a workable state.
- Resolve integration problems, merge conflicts, broken imports, failing tests, missing dependencies, and configuration issues caused by the implementation.
- Merge the feature branch back into `main`.
- After merging, report the branch that was merged, final Git status, tests executed, test results, and any remaining known issues.
- Do not begin unrelated work during rendezvous.
- Stop after rendezvous and wait for the user to say `sync docs`.

### SYNC DOCS

When the user says `sync docs`:

- Update the living documentation so it matches the actual state of the codebase.
- Use `doc/wiki/` for living documentation.
- Record unintuitive behavior, warnings, or common mistakes in `doc/wiki/footguns/`.
- Only document features that actually exist. Do not describe planned features as implemented.
- Correct or remove documentation that no longer matches the codebase.
- Commit documentation updates with an appropriate Conventional Commit, such as `docs: sync project documentation`.
- Stop after syncing the documentation.

## Repository Rules

- Use Git for version control.
- Check `git status` before significant repository changes.
- Scope meaningful changes into focused Conventional Commits, such as `feat:`, `fix:`, `docs:`, `chore:`, `build:`, `test:`, and `refactor:`.
- Keep commits focused; do not combine unrelated work into one commit.
- Use `TODO.md` as the editable repository todo list.
- Use `doc/memory/` for project memory instead of harness-specific memory.
- Treat `doc/canonical/` as human-approved authoritative project information. Do not modify it unless explicitly instructed.
- Use `doc/roadmap/` for future roadmap items.
- Use `doc/roadmap/plan_queue/` for queued plans.
- Do not place secrets, passwords, tokens, API keys, or credentials directly in Git-tracked files.
- Clearly identify any external or human-required inputs.
- The application should eventually run in CodeRange on port `5001` unless the user specifies otherwise.
- Do not use the original Digital Cafe walkthrough as step-by-step implementation instructions. It may only be used to understand expected functionality and user experience.
- Use clear, direct technical writing in responses and documentation.
- Read existing code before modifying it.
- Avoid unnecessary dependencies and avoid rewriting working code without a reason.
- Follow the existing architecture where reasonable.
- Run relevant tests after meaningful changes.
- Do not silently change requirements.
- Do not ask the user to manually write code that you can implement yourself.
