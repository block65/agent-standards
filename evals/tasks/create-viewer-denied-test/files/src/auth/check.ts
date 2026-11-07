export type Principal = { userId: string; permissions: string[] };

export function assertCan(principal: Principal, permission: string) {
	if (!principal.permissions.includes(permission)) {
		throw new Error(`Missing permission ${permission}`);
	}
}
