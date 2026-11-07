import type { Db } from "../db/client.ts";
import type { Principal } from "./check.ts";

const rolePermissions = {
	viewer: ["orders:read"],
	admin: ["orders:read", "orders:archive"],
} as const;

export type Role = keyof typeof rolePermissions;

export async function createPrincipal(
	db: Db,
	email: string,
): Promise<Principal> {
	const userId = crypto.randomUUID();

	await db.insert("users", { id: userId, email });

	return { userId, permissions: [] };
}

export async function grantRole(
	db: Db,
	principal: Principal,
	role: Role,
): Promise<Principal> {
	await db.insert("user_roles", { userId: principal.userId, role });

	return {
		...principal,
		permissions: [
			...new Set([...principal.permissions, ...rolePermissions[role]]),
		],
	};
}
