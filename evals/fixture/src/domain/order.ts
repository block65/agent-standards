export type OrderStatus = "open" | "paid" | "cancelled";

export type Order = {
	id: string;
	userId: string;
	status: OrderStatus;
	totalCents: number;
};
