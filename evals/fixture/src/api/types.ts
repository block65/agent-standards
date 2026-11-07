// Shapes the REST API returns, as documented by its OpenAPI spec

export type ApiUser = {
	id: string;
	display_name: string | null;
	email: string;
	tags?: string[] | null;
	created_at: string;
};

export type ApiOrder = {
	id: string;
	user_id: string;
	status: "open" | "paid" | "cancelled";
	total_cents: number;
};
