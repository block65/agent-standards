import { setup } from "../test/fixtures.ts";
import { assertEqual, test } from "../test/runner.ts";
import { archiveOrder } from "./archive.ts";

test("the owner can archive their order", async () => {
	const { db, owner, order } = await setup();

	await archiveOrder(db, owner, order.id);

	const rows = await db.select("orders", { id: order.id, status: "cancelled" });
	assertEqual(rows.length, 1);
});
