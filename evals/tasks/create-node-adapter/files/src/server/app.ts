export type Handler = (request: Request) => Promise<Response>;

export function createApp() {
	const routes = new Map<string, Handler>([
		["/health", async () => new Response("ok")],
	]);

	return {
		http(): Handler {
			return async (request) => {
				const route = routes.get(new URL(request.url).pathname);

				return route
					? route(request)
					: new Response("not found", { status: 404 });
			};
		},
	};
}
