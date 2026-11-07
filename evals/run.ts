import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import {
	cp,
	mkdir,
	mkdtemp,
	readdir,
	realpath,
	readFile,
	rm,
	symlink,
	writeFile,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { parseArgs, promisify } from "node:util";
import * as v from "valibot";

type Arm = "control" | "consumer";

const exec = promisify(execFile);

const root = path.join(import.meta.dirname, "..");
const evals = import.meta.dirname;
const standards = ["index.md", "lang", "engineering", "writing", "workflow"];

// `consumer` mounts the standards as a consuming repo does, and `control` runs bare
const arms = ["control", "consumer"] as const satisfies Arm[];

const taskSchema = v.object({
	kind: v.picklist(["create", "fix"]),
	prompt: v.string(),
	judge: v.optional(v.array(v.string())),
});

const lintSchema = v.object({
	diagnostics: v.array(
		v.object({
			filename: v.string(),
			code: v.string(),
			message: v.string(),
			labels: v.tupleWithRest(
				[v.object({ span: v.object({ line: v.number() }) })],
				v.unknown(),
			),
		}),
	),
});

const resultEventSchema = v.object({
	type: v.literal("result"),
	subtype: v.string(),
	is_error: v.boolean(),
	total_cost_usd: v.number(),
	num_turns: v.number(),
	duration_ms: v.number(),
});

const toolUseSchema = v.object({
	type: v.literal("tool_use"),
	name: v.string(),
	input: v.object({ file_path: v.optional(v.string()) }),
});

const assistantEventSchema = v.object({
	type: v.literal("assistant"),
	message: v.object({ content: v.array(v.unknown()) }),
});

const judgeReplySchema = v.object({ result: v.string() });

const verdictsSchema = v.array(
	v.object({ pass: v.boolean(), reason: v.string() }),
);

const diagnosticSchema = v.object({
	file: v.string(),
	line: v.number(),
	rule: v.string(),
	message: v.string(),
});

const resultSchema = v.object({
	task: v.string(),
	kind: v.picklist(["create", "fix"]),
	arm: v.picklist(["control", "consumer"]),
	runNumber: v.number(),
	dir: v.string(),
	agent: v.optional(resultEventSchema),
	readStandards: v.boolean(),
	introduced: v.array(diagnosticSchema),
	touchedDelta: v.record(v.string(), v.number()),
	typecheck: v.object({ pass: v.boolean(), errors: v.number() }),
	verdicts: v.array(
		v.object({ criterion: v.string(), pass: v.boolean(), reason: v.string() }),
	),
});

const execFailureSchema = v.object({ stdout: v.string() });

const { values } = parseArgs({
	options: {
		tasks: { type: "string" },
		arms: { type: "string", default: arms.join(",") },
		runs: { type: "string", default: "3" },
		concurrency: { type: "string", default: "4" },
		model: { type: "string" },
		out: { type: "string" },
		regrade: { type: "string" },
	},
});

const modelArgs = values.model ? ["--model", values.model] : [];

// Paths the agent authors, which exclude the mounted standards and their loader files
const authored = [".", ":!agent-standards", ":!AGENTS.md", ":!CLAUDE.md"];

const isolation = [
	"--setting-sources",
	"project",
	"--strict-mcp-config",
	"--disable-slash-commands",
	"--no-session-persistence",
];

type Diagnostic = v.InferOutput<typeof diagnosticSchema>;

type Verdict = RunResult["verdicts"][number];

type Task = v.InferOutput<typeof taskSchema> & { id: string };

type RunResult = v.InferOutput<typeof resultSchema>;

type RunSpec = { task: Task; arm: Arm; runNumber: number; dir: string };

// A nonzero exit still yields the output, since lint and tsc exit 1 on findings
async function runCommand(
	command: string,
	args: string[],
	options: { cwd: string; timeout?: number },
) {
	try {
		const { stdout } = await exec(command, args, {
			...options,
			maxBuffer: 64 * 1024 * 1024,
		});

		return { ok: true, stdout };
	} catch (err) {
		const failure = v.safeParse(execFailureSchema, err);

		if (!failure.success) {
			throw err;
		}

		return { ok: false, stdout: failure.output.stdout };
	}
}

async function loadTasks() {
	const ids =
		values.tasks === undefined
			? await readdir(path.join(evals, "tasks"))
			: values.tasks.split(",");

	return Promise.all(
		ids.map(async (id) => {
			const json = await readFile(
				path.join(evals, "tasks", id, "task.json"),
				"utf-8",
			);

			return v.parse(
				v.object({ ...taskSchema.entries, id: v.string() }),
				Object.assign(JSON.parse(json), { id }),
			);
		}),
	);
}

async function prepare({ task, arm, dir }: RunSpec) {
	await mkdir(dir, { recursive: true });
	await cp(path.join(evals, "fixture"), dir, { recursive: true });

	const files = path.join(evals, "tasks", task.id, "files");

	if (existsSync(files)) {
		await cp(files, dir, {
			recursive: true,
			force: true,
		});
	}

	// Block65 projects parse with valibot, so a run can import it as they do
	const valibot = await realpath(path.join(root, "node_modules/valibot"));

	await mkdir(path.join(dir, "node_modules"));
	await symlink(valibot, path.join(dir, "node_modules/valibot"));

	if (arm === "consumer") {
		await cp(path.join(evals, "consumer"), dir, { recursive: true });
		await Promise.all(
			standards.map((entry) =>
				cp(path.join(root, entry), path.join(dir, "agent-standards", entry), {
					recursive: true,
				}),
			),
		);
	}

	const identity = ["-c", "user.name=eval", "-c", "user.email=eval@localhost"];

	await runCommand("git", ["init", "-q"], { cwd: dir });
	await runCommand("git", ["add", "-A"], { cwd: dir });
	await runCommand("git", [...identity, "commit", "-qm", "base"], {
		cwd: dir,
	});
}

async function lint(dir: string) {
	const { stdout } = await runCommand(
		path.join(root, "node_modules/.bin/oxlint"),
		["-c", path.join(evals, "grader/grading.config.ts"), "-f", "json", "src"],
		{ cwd: dir },
	);

	return v
		.parse(lintSchema, JSON.parse(stdout))
		.diagnostics.map((d): Diagnostic => ({
			file: d.filename,
			line: d.labels[0].span.line,
			rule: d.code,
			message: d.message,
		}));
}

// Added line numbers per file, from a zero-context diff
function findAddedLines(diff: string) {
	const hunk = /^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@/gm;

	// A deleted file's section names no `+++ b/` path
	const sections = diff
		.split(/^diff --git /m)
		.map((section) => ({
			file: /^\+\+\+ b\/(.+)$/m.exec(section)?.[1],
			section,
		}))
		.filter(
			(s): s is { file: string; section: string } => s.file !== undefined,
		);

	return new Map(
		sections.map(({ file, section }) => {
			// A hunk header omits the count when it is one line
			const lines = [...section.matchAll(hunk)].flatMap(([, start, count]) =>
				Array.from(
					{ length: count === undefined ? 1 : Number(count) },
					(_, i) => Number(start) + i,
				),
			);

			return [file, lines];
		}),
	);
}

function countRule(diagnostics: Diagnostic[], rule: string) {
	return diagnostics.filter((d) => d.rule === rule).length;
}

async function runAgent(dir: string, prompt: string) {
	const { stdout } = await runCommand(
		"claude",
		[
			"-p",
			`${prompt}\n\nWork without asking questions; make the reasonable choice and finish the change.`,
			...isolation,
			"--tools",
			"Read,Write,Edit,Glob,Grep",
			"--permission-mode",
			"acceptEdits",
			"--output-format",
			"stream-json",
			"--verbose",
			...modelArgs,
		],
		{ cwd: dir, timeout: 15 * 60_000 },
	);
	const events = stdout
		.split("\n")
		.filter(Boolean)
		.map((line) => JSON.parse(line));
	const result = events
		.map((event) => v.safeParse(resultEventSchema, event))
		.find((parsed) => parsed.success)?.output;
	const toolUses = events
		.filter((event) => v.is(assistantEventSchema, event))
		.flatMap((event) => event.message.content)
		.filter((block) => v.is(toolUseSchema, block));

	return {
		result,
		readStandards: toolUses.some(
			(use) =>
				use.name === "Read" &&
				use.input.file_path?.includes("agent-standards/lang/") === true,
		),
	};
}

// A judge reads the diff correctly only with the compiler flags and domain types
async function readProjectContext(dir: string) {
	const domainFiles = await readdir(path.join(dir, "src/domain"));
	const files = ["tsconfig.json", ...domainFiles.map((f) => `src/domain/${f}`)];
	const contents = await Promise.all(
		files.map(async (file) => {
			const text = await readFile(path.join(dir, file), "utf-8");

			return `${file}:\n\`\`\`\n${text}\`\`\``;
		}),
	);

	return contents.join("\n\n");
}

async function judge(task: Task, dir: string) {
	const criteria = task.judge;
	const { stdout: diff } = await runCommand(
		"git",
		["diff", "--cached", "HEAD", "--", ...authored],
		{ cwd: dir },
	);

	if (criteria === undefined || diff === "") {
		return [];
	}

	const context = await readProjectContext(dir);

	const numbered = criteria.map((c, i) => `${i + 1}. ${c}`).join("\n");

	const { stdout } = await runCommand(
		"claude",
		[
			"-p",
			[
				"You grade a code change against fixed criteria. Judge only what the diff shows.",
				`The task given to the author was:\n${task.prompt}`,
				`Project files after the change:\n${context}`,
				`Criteria:\n${numbered}`,
				`Diff:\n\`\`\`diff\n${diff}\n\`\`\``,
				'Reply with only a JSON array, one object per criterion in order: {"pass": boolean, "reason": "one sentence"}.',
			].join("\n\n"),
			...isolation,
			"--tools",
			"",
			"--output-format",
			"json",
			...modelArgs,
		],
		{ cwd: evals, timeout: 5 * 60_000 },
	);
	const text = v.parse(judgeReplySchema, JSON.parse(stdout)).result;
	const verdicts = v.parse(
		v.pipe(verdictsSchema, v.length(criteria.length)),
		JSON.parse(text.slice(text.indexOf("["), text.lastIndexOf("]") + 1)),
	);

	return criteria.map((criterion, i): Verdict => {
		const verdict = verdicts[i];

		if (!verdict) {
			throw new Error(`Judge gave no verdict for criterion ${i + 1}`);
		}

		return { criterion, pass: verdict.pass, reason: verdict.reason };
	});
}

// Lints the base commit and the agent's staged result, counting only added lines
async function gradeLint(dir: string) {
	const base = await mkdtemp(path.join(os.tmpdir(), "eval-base-"));

	await runCommand("sh", ["-c", `git archive HEAD | tar -x -C '${base}'`], {
		cwd: dir,
	});
	const before = await lint(base);

	await rm(base, { recursive: true });
	const zeroContext = await runCommand(
		"git",
		["diff", "--cached", "-U0", "HEAD", "--", ...authored],
		{ cwd: dir },
	);
	const added = findAddedLines(zeroContext.stdout);
	const after = await lint(dir);
	const isTouched = (d: Diagnostic) => added.has(d.file);
	const rules = new Set([...before, ...after].map((d) => d.rule));

	return {
		introduced: after.filter((d) => added.get(d.file)?.includes(d.line)),
		touchedDelta: Object.fromEntries(
			[...rules].map((rule) => [
				rule,
				countRule(
					after.filter((d) => isTouched(d)),
					rule,
				) -
					countRule(
						before.filter((d) => isTouched(d)),
						rule,
					),
			]),
		),
	};
}

async function score(spec: RunSpec) {
	const { task, arm, runNumber, dir } = spec;

	await prepare(spec);
	const agent = await runAgent(dir, task.prompt);

	await runCommand("git", ["add", "-A"], { cwd: dir });
	const graded = await gradeLint(dir);
	const typecheck = await runCommand(
		path.join(root, "node_modules/.bin/tsc"),
		["-p", path.join(dir, "tsconfig.json")],
		{ cwd: dir },
	);
	const verdicts = await judge(task, dir);

	const result: RunResult = {
		task: task.id,
		kind: task.kind,
		arm,
		runNumber,
		dir,
		agent: agent.result,
		readStandards: agent.readStandards,
		...graded,
		typecheck: {
			pass: typecheck.ok,
			errors: typecheck.stdout
				.split("\n")
				.filter((line) => line.includes("error TS")).length,
		},
		verdicts,
	};

	await writeFile(
		path.join(dir, "result.json"),
		JSON.stringify(result, undefined, "\t"),
	);
	console.error(
		`${task.id} ${arm} #${runNumber}: ${result.introduced.length} findings, typecheck ${typecheck.ok ? "ok" : "failed"}`,
	);

	return result;
}

async function runPool<T, U>(
	items: T[],
	size: number,
	work: (item: T) => Promise<U>,
) {
	const queue = [...items];

	const drain = async (): Promise<U[]> => {
		const next = queue.shift();

		if (next === undefined) {
			return [];
		}

		const result = await work(next);
		const rest = await drain();

		return [result, ...rest];
	};

	const lanes = await Promise.all(Array.from({ length: size }, drain));

	return lanes.flat();
}

function formatPercent(part: number, whole: number) {
	return whole === 0 ? "–" : `${Math.round((part / whole) * 100)}%`;
}

function sumCost(runs: RunResult[]) {
	return runs
		.map((r) => r.agent)
		.filter((agent) => agent !== undefined)
		.reduce((sum, agent) => sum + agent.total_cost_usd, 0)
		.toFixed(2);
}

function formatReport(results: RunResult[], selectedArms: Arm[]) {
	const byArm = Object.groupBy(results, (r) => r.arm);
	const rules = [
		...new Set(results.flatMap((r) => r.introduced.map((d) => d.rule))),
	].toSorted();
	const criteria = [
		...new Set(results.flatMap((r) => r.verdicts.map((d) => d.criterion))),
	];
	const header = `| | ${selectedArms.join(" | ")} |\n|---|${selectedArms.map(() => "---").join("|")}|`;
	const row = (label: string, cell: (runs: RunResult[]) => string) =>
		`| ${label} | ${selectedArms.map((arm) => cell(byArm[arm] ?? [])).join(" | ")} |`;

	const findingRows = rules.map((rule) =>
		row(rule, (runs) => {
			const hits = runs.filter((r) => countRule(r.introduced, rule) > 0);
			const total = runs.flatMap((r) => r.introduced);

			return `${countRule(total, rule)} in ${formatPercent(hits.length, runs.length)} of runs`;
		}),
	);
	const judgeRows = criteria.map((criterion) =>
		row(criterion, (runs) => {
			const verdicts = runs
				.flatMap((r) => r.verdicts)
				.filter((d) => d.criterion === criterion);

			return formatPercent(
				verdicts.filter((d) => d.pass).length,
				verdicts.length,
			);
		}),
	);

	return [
		"# Standards eval",
		"",
		"Findings count only lines the agent added. Judge rows are the pass rate.",
		"",
		header,
		row("runs", (runs) => String(runs.length)),
		row("agent failed", (runs) =>
			String(runs.filter((r) => !r.agent || r.agent.is_error).length),
		),
		row("read a lang standard", (runs) =>
			formatPercent(runs.filter((r) => r.readStandards).length, runs.length),
		),
		row("typecheck passes", (runs) =>
			formatPercent(runs.filter((r) => r.typecheck.pass).length, runs.length),
		),
		row("cost (USD)", sumCost),
		"",
		"## Lint findings on added lines",
		"",
		header,
		...findingRows,
		"",
		"## Judge",
		"",
		header,
		...judgeRows,
		"",
	].join("\n");
}

async function writeReport(
	out: string,
	results: RunResult[],
	selectedArms: Arm[],
) {
	const markdown = formatReport(results, selectedArms);

	await writeFile(
		path.join(out, "results.json"),
		JSON.stringify(results, undefined, "\t"),
	);
	await writeFile(path.join(out, "report.md"), markdown);
	console.log(markdown);
}

// Rescores saved runs with the current grader and judge, keeping the agent results
async function regrade(out: string) {
	const json = await readFile(path.join(out, "results.json"), "utf-8");
	const saved = v.parse(v.array(resultSchema), JSON.parse(json));
	const loaded = await loadTasks();
	const tasks = new Map(loaded.map((task) => [task.id, task]));
	const results = await runPool(saved, 6, async (result) => {
		const task = tasks.get(result.task);

		if (!task) {
			throw new Error(`Task ${result.task} no longer exists`);
		}

		const graded = await gradeLint(result.dir);
		const verdicts = await judge(task, result.dir);

		return Object.assign(result, graded, { verdicts });
	});
	const selectedArms = arms.filter((arm) => results.some((r) => r.arm === arm));

	await writeReport(out, results, selectedArms);
}

async function main() {
	if (values.regrade !== undefined) {
		await regrade(values.regrade);

		return;
	}

	const tasks = await loadTasks();
	const selectedArms = v.parse(
		v.array(v.picklist(arms)),
		values.arms.split(","),
	);
	const runs = Number(values.runs);
	const out =
		values.out ??
		path.join(
			evals,
			".results",
			Temporal.Now.instant().toString().replaceAll(":", "-"),
		);
	const specs = tasks.flatMap((task) =>
		selectedArms.flatMap((arm) =>
			Array.from({ length: runs }, (_, i) => ({
				task,
				arm,
				runNumber: i + 1,
				dir: path.join(out, task.id, arm, String(i + 1)),
			})),
		),
	);

	console.error(`${specs.length} runs into ${out}`);
	const results = await runPool(specs, Number(values.concurrency), score);

	await writeReport(out, results, selectedArms);
}

await main();
