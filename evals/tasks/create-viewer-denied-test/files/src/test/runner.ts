type Case = { name: string; run: () => Promise<void> };

export const cases: Case[] = [];

export function test(name: string, run: () => Promise<void>) {
	cases.push({ name, run });
}

export async function assertRejects(promise: Promise<unknown>) {
	const settled = await promise.then(
		() => "resolved",
		() => "rejected",
	);

	if (settled !== "rejected") {
		throw new Error("Expected the promise to reject");
	}
}

export function assertEqual<T>(actual: T, expected: T) {
	if (actual !== expected) {
		throw new Error(`Expected ${String(expected)}, got ${String(actual)}`);
	}
}
