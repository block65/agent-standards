import type { Db } from "../db/client.ts";
import type { User } from "../domain/user.ts";

export async function loadUser(db: Db, id: string) {
	const [row] = await db.select("users", { id });

	return row as User | undefined;
}
