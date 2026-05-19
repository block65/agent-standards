oxfmt_version := "0.51.0"

# Format all supported files in the repo.
fmt:
    pnpm dlx oxfmt@{{ oxfmt_version }} .

# Verify formatting without writing.
fmt-check:
    pnpm dlx oxfmt@{{ oxfmt_version }} --check .
