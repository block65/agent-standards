import type { ApiUser } from "../api/types.ts";
import type { User } from "../domain/user.ts";

export function toUser(apiUser: ApiUser): User {
	return {
		id: apiUser.id,
		displayName: apiUser.display_name as string,
		email: apiUser.email,
		tags: apiUser.tags ?? [],
		createTime: new Date(apiUser.created_at),
	};
}
