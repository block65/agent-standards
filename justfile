default: typecheck lint fmt-check test dead-code

# The engine lays the types tsconfig.json extends when it first loads the
# plugin from this folder (claude --plugin-dir .)
typecheck:
    pnpm exec tsc -p .

lint *ARGS:
    pnpm exec oxlint {{ ARGS }}

fmt:
    pnpm exec oxfmt

fmt-check:
    pnpm exec oxfmt --check

test:
    claude plugin test .
    claude plugin validate .
    node --test evals/grader/plugin.spec.ts

dead-code:
    pnpm exec fallow

# Scores whether agents follow the standards; costs model usage, so not in default
eval *ARGS:
    node evals/run.ts {{ ARGS }}
