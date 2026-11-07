import type { Order } from "../domain/order.ts";

export function totalsByUser(orders: Order[]) {
	const totals: Record<string, number> = {};

	for (let i = 0; i < orders.length; i++) {
		const order = orders[i]!;
		totals[order.userId] = (totals[order.userId] ?? 0) + order.totalCents;
	}

	return totals;
}
