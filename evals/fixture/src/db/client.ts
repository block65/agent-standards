export type Row = Record<string, unknown>;

export type Db = {
	insert: (table: string, row: Row) => Promise<void>;
	select: (table: string, where?: Row) => Promise<Row[]>;
	truncate: (table: string) => Promise<void>;
};

export function createMemoryDb(): Db {
	const tables = new Map<string, Row[]>();

	return {
		insert: async (table, row) => {
			tables.set(table, [...(tables.get(table) ?? []), row]);
		},
		select: async (table, where = {}) =>
			(tables.get(table) ?? []).filter((row) =>
				Object.entries(where).every(([key, value]) => row[key] === value),
			),
		truncate: async (table) => {
			tables.delete(table);
		},
	};
}
