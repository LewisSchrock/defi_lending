import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
export interface ShortUrlFields {
    referrer: Address;
    shortUrl: string;
}
export interface ShortUrlJSON {
    referrer: string;
    shortUrl: string;
}
export declare class ShortUrl {
    readonly referrer: Address;
    readonly shortUrl: string;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<ShortUrl>;
    constructor(fields: ShortUrlFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<ShortUrl | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<ShortUrl | null>>;
    static decode(data: Buffer): ShortUrl;
    toJSON(): ShortUrlJSON;
    static fromJSON(obj: ShortUrlJSON): ShortUrl;
}
//# sourceMappingURL=ShortUrl.d.ts.map