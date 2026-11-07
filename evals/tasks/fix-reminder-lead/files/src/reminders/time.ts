const dayMs = 24 * 60 * 60 * 1000;

export function reminderTime(dueIso: string) {
	return new Date(new Date(dueIso).getTime() - dayMs);
}
