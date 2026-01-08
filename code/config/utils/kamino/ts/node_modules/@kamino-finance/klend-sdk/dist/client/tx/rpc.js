"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createCliRpc = createCliRpc;
const kit_1 = require("@solana/kit");
/**
 * Names of Solana RPC methods that should be multicasted to all configured multicast RPCs.
 */
const MULTICASTED_METHOD_NAMES = ['sendTransaction'];
function createCliRpc(rpcChain) {
    return asRpc(createResilientRpcCaller(rpcChain));
}
function createUrlRpcCaller({ url, name, headers }) {
    return new LabelledRpcCaller((0, kit_1.createDefaultRpcTransport)({ url, headers }), name);
}
function createResilientRpcCaller(rpcChain) {
    let resilientRpcCaller = createUrlRpcCaller(rpcChain.endpoint);
    if (rpcChain.multicastEndpoints.length > 0) {
        resilientRpcCaller = new MethodRoutingRpcTransport(resilientRpcCaller, MULTICASTED_METHOD_NAMES, new MulticastingRpcTransport(rpcChain.multicastEndpoints.map((url) => createUrlRpcCaller(url)), resilientRpcCaller));
    }
    return resilientRpcCaller;
}
function asRpc(rpcCaller) {
    const api = (0, kit_1.createSolanaRpcApi)({
        ...kit_1.DEFAULT_RPC_CONFIG,
        defaultCommitment: 'processed',
    });
    const transport = asRpcTransport(rpcCaller);
    return (0, kit_1.createRpc)({ api, transport });
}
function asRpcTransport(rpcCaller) {
    // Despite `ReturnType<RpcTransport>` working fine in all other contexts, it loses its type-inferring powers when
    // `RpcCaller.call()` is referenced directly (due to not seeing the actual type parameter), forcing this ugly cast:
    return rpcCaller.call.bind(rpcCaller);
}
class LabelledRpcCaller {
    transport;
    label;
    constructor(transport, label) {
        this.transport = transport;
        this.label = label;
    }
    call(...args) {
        return this.transport(...args);
    }
    toString() {
        return this.label;
    }
}
class MethodRoutingRpcTransport {
    defaultRpcCaller;
    routedMethodNames;
    routedRpcCaller;
    constructor(defaultRpcCaller, routedMethodNames, routedRpcCaller) {
        this.defaultRpcCaller = defaultRpcCaller;
        this.routedMethodNames = new Set(routedMethodNames);
        this.routedRpcCaller = routedRpcCaller;
    }
    call(...args) {
        const methodName = MethodRoutingRpcTransport.resolveMethodName(...args);
        if (this.routedMethodNames.has(methodName)) {
            return this.routedRpcCaller.call(...args);
        }
        return this.defaultRpcCaller.call(...args);
    }
    static resolveMethodName(...args) {
        // Please excuse the ugly introspection, needed only because of the RpcTransport using a private type:
        return args[0].payload.method;
    }
}
class MulticastingRpcTransport {
    multicastRpcCallers;
    finalRpcCaller;
    constructor(multicastRpcCallers, finalRpcCaller) {
        this.multicastRpcCallers = new Set(multicastRpcCallers);
        this.finalRpcCaller = finalRpcCaller;
    }
    call(...args) {
        for (const multicastRpcCaller of this.multicastRpcCallers) {
            // Please note the lack of `await` below. This is intended, since we want to fire and forget to all multicast
            // RPCs. This works in JavaScript (in contrast to e.g. Rust), because `Promise`s here start work when constructed,
            // not when "polled".
            multicastRpcCaller
                .call(...args)
                .catch((e) => console.log(`Calling multicast RPC ${multicastRpcCaller} failed; ignoring it`, e));
        }
        return this.finalRpcCaller.call(...args);
    }
}
//# sourceMappingURL=rpc.js.map