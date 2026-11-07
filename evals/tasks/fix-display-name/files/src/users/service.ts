import { listUsers } from "../api/client.ts";
import type { User } from "../domain/user.ts";
import { toUser } from "./map.ts";

export async function findUser(id: string): Promise<User | undefined> {
	const users = await listUsers();

	return users.map(toUser).find((user) => user.id === id);
}
