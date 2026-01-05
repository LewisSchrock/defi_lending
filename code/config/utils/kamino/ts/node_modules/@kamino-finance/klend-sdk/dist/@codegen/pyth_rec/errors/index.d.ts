import { Address } from "@solana/kit";
import * as anchor from "./anchor";
import * as custom from "./custom";
export declare function fromCode(code: number, logs?: string[]): custom.CustomError | anchor.AnchorError | null;
export declare function fromTxError(err: unknown, programId?: Address): custom.CustomError | anchor.AnchorError | null;
//# sourceMappingURL=index.d.ts.map