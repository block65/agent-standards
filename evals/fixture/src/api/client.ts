import type { ApiOrder, ApiUser } from "./types.ts";

async function getJson(path: string): Promise<unknown> {
	const res = await fetch(new URL(path, "https://api.example.com/"));

	if (!res.ok) {
		throw new Error(`GET ${path} failed with ${res.status}`);
	}

	return res.json();
}

export async function listUsers() {
	return (await getJson("v1/users")) as ApiUser[];
}

export async function listOrders(userId: string) {
	return (await getJson(
		`v1/users/${encodeURIComponent(userId)}/orders`,
	)) as ApiOrder[];
}
