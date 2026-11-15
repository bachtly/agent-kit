# {{APP_NAME}}

{{ONE_LINE_DESCRIPTION}}

## Check command

Run before every commit. Every command here must also be in `.claude/settings.json`
`permissions.allow`, or the agent can't run it.

```sh
{{CHECK_COMMAND}}
```

Individual steps: install `{{INSTALL_COMMAND}}` · build `{{BUILD_COMMAND}}` · test `{{TEST_COMMAND}}` · lint `{{LINT_COMMAND}}`

## Architecture

{{ARCHITECTURE: 3-8 bullets. Main folders and what lives in each, how a request or data flows,
where tests live.}}

## Do not

- Edit `.github/workflows/` (the agent can't push workflow changes).
- {{APP_SPECIFIC_DO_NOT, e.g. "hand-edit generated files in src/gen/", "change the DB schema without a migration"}}
