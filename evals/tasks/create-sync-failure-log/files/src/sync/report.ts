import type { Order } from "../domain/order.ts";

export function countPaid(orders: Order[]) {
	return orders.filter((order) => order.status === "paid").length;
}
