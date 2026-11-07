export type Notification = { to: string; subject: string; body: string };

export async function sendNotification(notification: Notification) {
	await fetch(new URL("v1/email", "https://mail.example.com/"), {
		method: "POST",
		headers: { "content-type": "application/json" },
		body: JSON.stringify(notification),
	});
}
