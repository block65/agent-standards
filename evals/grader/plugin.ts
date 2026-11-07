type Node = { type: string; parent?: Node | null; [key: string]: unknown };

type Context = {
	report: (descriptor: { node: Node; message: string }) => void;
};

const upperSnake = /^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$|^[A-Z]{2,}[0-9]*$/;

const loops = new Set([
	"ForStatement",
	"ForOfStatement",
	"ForInStatement",
	"WhileStatement",
	"DoWhileStatement",
]);

const functions = new Set([
	"FunctionDeclaration",
	"FunctionExpression",
	"ArrowFunctionExpression",
]);

const mutators = new Set(["push", "unshift", "splice", "set", "add"]);

// A loop body holding one of these needs the loop
const sequenceOrExit = new Set([
	"AwaitExpression",
	"BreakStatement",
	"ReturnStatement",
	"YieldExpression",
]);

function isNode(value: unknown): value is Node {
	return (
		typeof value === "object" &&
		value !== null &&
		"type" in value &&
		typeof value.type === "string"
	);
}

function child(node: Node | undefined, key: string) {
	const value = node?.[key];

	return isNode(value) ? value : undefined;
}

function readName(node: Node | undefined) {
	return typeof node?.name === "string" ? node.name : undefined;
}

function readParams(node: Node) {
	return Array.isArray(node.params) ? node.params.filter(isNode) : [];
}

function isAsConst(node: Node) {
	return (
		node.type === "TSAsExpression" &&
		readName(child(child(node, "typeAnnotation"), "typeName")) === "const"
	);
}

// Each evaluates to a scalar, which the binding holds by value
const scalarInits = new Set([
	"TemplateLiteral",
	"UnaryExpression",
	"BinaryExpression",
]);

function isFreezeCall(init: Node) {
	const callee = child(init, "callee");
	const called =
		callee?.type === "MemberExpression"
			? readName(child(callee, "property"))
			: readName(callee);

	return called !== undefined && /freeze/i.test(called);
}

// `satisfies` and parentheses check or group a value without changing it
const transparent = new Set([
	"TSSatisfiesExpression",
	"ParenthesizedExpression",
]);

function unwrap(node: Node): Node {
	const inner = child(node, "expression");

	return transparent.has(node.type) && inner ? unwrap(inner) : node;
}

function isImmutableInit(wrapped: Node) {
	const init = unwrap(wrapped);

	// A regex literal holds mutable `lastIndex` state, so only the other literals qualify
	if (init.type === "Literal") {
		return !("regex" in init && init.regex);
	}

	return (
		isAsConst(init) ||
		scalarInits.has(init.type) ||
		(init.type === "CallExpression" && isFreezeCall(init))
	);
}

function isForEachCallback(fn: Node) {
	const call = fn.parent;

	return (
		call?.type === "CallExpression" &&
		readName(child(child(call, "callee"), "property")) === "forEach"
	);
}

// Iteration stops at a function boundary unless that function is a `.forEach()` callback
function enclosingIteration(node: Node): Node | undefined {
	const at = node.parent;

	if (!at) {
		return;
	}

	if (loops.has(at.type)) {
		return at;
	}

	if (functions.has(at.type)) {
		return isForEachCallback(at) ? at : undefined;
	}

	return enclosingIteration(at);
}

function hasDescendant(node: Node, types: Set<string>): boolean {
	if (types.has(node.type)) {
		return true;
	}

	return Object.entries(node)
		.filter(([key]) => key !== "parent")
		.flatMap(([, value]) => (Array.isArray(value) ? value : [value]))
		.filter((value) => isNode(value))
		.some((item) => !functions.has(item.type) && hasDescendant(item, types));
}

function isExported(node: Node) {
	const parent = node.parent;

	return (
		parent?.type === "ExportNamedDeclaration" ||
		(parent?.type === "VariableDeclarator" &&
			parent.parent?.parent?.type === "ExportNamedDeclaration")
	);
}

function inlineObjectParam(node: Node) {
	const params = readParams(node);
	const [first] = params;

	if (params.length !== 1 || !first) {
		return;
	}

	const pattern =
		first.type === "AssignmentPattern" ? child(first, "left") : first;
	const annotation = child(child(pattern, "typeAnnotation"), "typeAnnotation");

	return annotation?.type === "TSTypeLiteral" ? pattern : undefined;
}

function findAnnotatedIdentifier(node: Node) {
	let at = node.parent;

	while (at && at.type !== "Identifier" && !functions.has(at.type)) {
		at = at.parent;
	}

	return at?.type === "Identifier" ? at : undefined;
}

function findOwningParam(node: Node) {
	const identifier = findAnnotatedIdentifier(node);
	const owner = identifier?.parent;

	return identifier && owner && readParams(owner).includes(identifier)
		? identifier
		: undefined;
}

function checkFunction(context: Context, node: Node) {
	const pattern = isExported(node) ? inlineObjectParam(node) : undefined;

	if (pattern) {
		context.report({
			node: pattern,
			message: "Exported function types its object parameter inline",
		});
	}
}

export default {
	meta: { name: "eval" },
	rules: {
		"upper-snake-mutable": {
			create: (context: Context) => ({
				VariableDeclarator(node: Node) {
					const id = child(node, "id");
					const init = child(node, "init");
					const name = readName(id);

					if (
						!id ||
						!init ||
						!name ||
						!upperSnake.test(name) ||
						isImmutableInit(init)
					) {
						return;
					}

					context.report({
						node: id,
						message: `UPPER_SNAKE name on a mutable ${init.type}`,
					});
				},
			}),
		},

		"loop-mutation": {
			create: (context: Context) => {
				const report = (node: Node) => {
					if (enclosingIteration(node)) {
						context.report({
							node,
							message: "Mutates a collection inside a loop or forEach",
						});
					}
				};

				return {
					CallExpression(node: Node) {
						const callee = child(node, "callee");
						const method = readName(child(callee, "property"));

						if (
							callee?.type === "MemberExpression" &&
							method &&
							mutators.has(method)
						) {
							report(node);
						}
					},
					AssignmentExpression(node: Node) {
						if (child(node, "left")?.type === "MemberExpression") {
							report(node);
						}
					},
				};
			},
		},

		"side-effect-for-loop": {
			create: (context: Context) => {
				const check = (node: Node) => {
					const body = child(node, "body");

					if (body && !hasDescendant(body, sequenceOrExit)) {
						context.report({
							node,
							message:
								"Loop without await or early exit; use a transformation or forEach",
						});
					}
				};

				return {
					ForStatement: check,
					ForOfStatement: check,
					ForInStatement: check,
					WhileStatement: check,
				};
			},
		},

		"inline-object-param": {
			create: (context: Context) => ({
				FunctionDeclaration: (node: Node) => checkFunction(context, node),
				ArrowFunctionExpression: (node: Node) => checkFunction(context, node),
				FunctionExpression: (node: Node) => checkFunction(context, node),
			}),
		},

		// Every `??` is reported for a reviewer to weigh, so it scores as a warning
		"nullish-default": {
			create: (context: Context) => ({
				LogicalExpression(node: Node) {
					if (node.operator === "??") {
						context.report({ node, message: "`??` default" });
					}
				},
			}),
		},

		"nullable-param": {
			create: (context: Context) => ({
				TSNullKeyword(node: Node) {
					const param = findOwningParam(node);

					if (param) {
						context.report({ node: param, message: "Parameter admits null" });
					}
				},
			}),
		},
	},
};
