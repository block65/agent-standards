import type { OrderStatus } from "../domain/order.ts";

export type OrderFilter = { userId: string; status?: OrderStatus };

export function buildFilter(
	userId: string,
	status: OrderStatus | undefined,
): OrderFilter {
	return { userId, status };
}
