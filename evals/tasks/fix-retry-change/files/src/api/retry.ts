// Import the URL helper
const base = "https://api.example.com/";

// Get JSON with retry
export async function getJsonWithRetry(path: string) {
	// Loop over attempts
	for (let attempt = 1; attempt <= 3; attempt++) {
		// Make the request
		const res = await fetch(new URL(path, base));
		const body: unknown = await res.json();

		// NOTE: the upstream answers auth failures with 200 and an error body
		if (
			res.ok &&
			!(typeof body === "object" && body !== null && "error" in body)
		) {
			// Return the body
			return body;
		}
	}

	// Throw an error
	throw new Error(`GET ${path} failed after retries`);
}
