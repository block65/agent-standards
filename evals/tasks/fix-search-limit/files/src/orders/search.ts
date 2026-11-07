import type { Order, OrderStatus } from "../domain/order.ts";

export function searchOrders({
	orders,
	userId,
	status,
}: {
	orders: Order[];
	userId: string;
	status?: OrderStatus;
}) {
	return orders.filter(
		(order) =>
			order.userId === userId &&
			(status === undefined || order.status === status),
	);
}
