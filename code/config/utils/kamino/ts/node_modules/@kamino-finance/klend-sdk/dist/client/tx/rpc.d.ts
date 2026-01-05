import { Rpc, RpcTransport, SolanaRpcApi, SolanaRpcApiDevnet, SolanaRpcApiMainnet, SolanaRpcApiTestnet } from '@solana/kit';
import { createHttpTransport } from '@solana/rpc-transport-http';
import { Mutable } from '../utils/modifiers';
import { Cluster } from './CliEnv';
export type RpcMethodTypes = SolanaRpcApi | SolanaRpcApiDevnet | SolanaRpcApiMainnet | SolanaRpcApiTestnet;
type RpcHeadersConfigParam = Parameters<typeof createHttpTransport>[0]['headers'];
export type AllowedHttpHeaders = Mutable<RpcHeadersConfigParam>;
export type RpcUrl = {
    url: string;
    name: string;
    headers?: AllowedHttpHeaders;
};
export type Chain = {
    name: Cluster;
    endpoint: RpcUrl;
    wsEndpoint: RpcUrl;
    multicastEndpoints: RpcUrl[];
};
export declare function createCliRpc<TExtraMethods>(rpcChain: Chain): Rpc<RpcMethodTypes & TExtraMethods>;
/**
 * A "true" interface wrapping the function interface {@link RpcTransport} (so that a class can implement it).
 */
export interface RpcCaller {
    /**
     * See {@link RpcTransport}.
     */
    call(...args: Parameters<RpcTransport>): ReturnType<RpcTransport>;
}
export {};
//# sourceMappingURL=rpc.d.ts.map