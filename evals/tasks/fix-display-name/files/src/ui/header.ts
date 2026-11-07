import type { User } from "../domain/user.ts";

export function greeting(user: User) {
	return `Hello, ${user.displayName}`;
}

export function renderHeader(user: User) {
	return `<header><span>${greeting(user)}</span></header>`;
}
