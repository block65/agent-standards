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

dead-code:
    pnpm exec fallow
