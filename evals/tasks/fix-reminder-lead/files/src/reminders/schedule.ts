import { reminderTime } from "./time.ts";

export type Reminder = { orderId: string; sendAt: Date };

export function scheduleReminder(orderId: string, due: Date): Reminder {
	return { orderId, sendAt: reminderTime(due.toISOString()) };
}
