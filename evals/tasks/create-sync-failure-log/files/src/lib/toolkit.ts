export function errorMessage(err: unknown) {
	return err instanceof Error ? err.message : String(err);
}

export function isDefined<T>(value: T | undefined): value is T {
	return value !== undefined;
}
