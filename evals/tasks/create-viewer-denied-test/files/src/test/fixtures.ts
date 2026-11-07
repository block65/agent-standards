import { createPrincipal } from "../auth/principals.ts";
import { createMemoryDb } from "../db/client.ts";

// Every suite starts from the principals and data a fresh install would have
export async function setup() {
	const db = createMemoryDb();
	const owner = await createPrincipal(db, `${crypto.randomUUID()}@example.com`);
	const colleague = await createPrincipal(
		db,
		`${crypto.randomUUID()}@example.com`,
	);
	const order = {
		id: crypto.randomUUID(),
		userId: owner.userId,
		status: "open",
		totalCents: 1200,
	};

	await db.insert("orders", order);

	return { db, owner, colleague, order };
}
