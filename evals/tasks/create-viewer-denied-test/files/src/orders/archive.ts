import { assertCan, type Principal } from "../auth/check.ts";
import type { Db } from "../db/client.ts";

export async function archiveOrder(
	db: Db,
	principal: Principal,
	orderId: string,
) {
	const [order] = await db.select("orders", { id: orderId });

	if (!order) {
		throw new Error(`Order ${orderId} not found`);
	}

	if (order.userId !== principal.userId) {
		assertCan(principal, "orders:archive");
	}

	await db.insert("orders", { ...order, status: "cancelled" });
}
