## What this changes

<!-- One or two sentences. Link the issue it closes, if any: "Closes #123" -->

## Safety checklist

NitroCore modifies real Windows system settings. Check all that apply, or
explain why an item doesn't apply:

- [ ] No registry / service / power-plan behavior changed
- [ ] New or changed mutation is covered by Preview Mode (`--dry-run` records it)
- [ ] Restore-point prompt added where `step_requires_restore_prompt` says so
- [ ] Registry writes snapshot the old value for one-click undo
- [ ] Tested the dry-run path on a non-Windows runner (`pytest NitroCore/tests`)

## Test report

<!-- How did you verify this? Paste pytest output, or describe manual testing
on Windows (version, profile used, what you clicked). -->
