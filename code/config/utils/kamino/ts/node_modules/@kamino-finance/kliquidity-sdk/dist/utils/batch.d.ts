export declare function batchFetch<A, T>(addresses: Array<A>, fetchBatch: (chunk: Array<A>) => Promise<Array<T>>, chunkSize?: number): Promise<Array<T>>;
export declare function chunks<T>(array: T[], size: number): T[][];
//# sourceMappingURL=batch.d.ts.map