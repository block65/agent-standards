import type { Order } from "../domain/order.ts";

export function formatOrderTotal(order: Order) {
	return "$" + order.totalCents / 100;
}

export function describeOrders(orders: Order[]) {
	var lines = [];
	for (var i = 0; i < orders.length; i++) {
		lines.push(orders[i]!.id + ": " + formatOrderTotal(orders[i]!));
	}
	return lines.join("\n");
}
