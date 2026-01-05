import Decimal from 'decimal.js';
import { KaminoMarket, KaminoObligation, KaminoReserve } from '../classes';
import { Address, Option, Slot } from '@solana/kit';
export declare function calcRepayAmountWithSlippage(kaminoMarket: KaminoMarket, debtReserve: KaminoReserve, currentSlot: Slot, obligation: KaminoObligation, amount: Decimal, referrer: Option<Address>): {
    repayAmount: Decimal;
    repayAmountLamports: Decimal;
    flashRepayAmountLamports: Decimal;
};
export declare const calcFlashRepayAmount: (props: {
    reserve: KaminoReserve;
    referralFeeBps: number;
    hasReferral: boolean;
    flashBorrowAmountLamports: Decimal;
}) => {
    flashRepayAmountLamports: Decimal;
};
export declare function calcMaxWithdrawCollateral(market: KaminoMarket, obligation: KaminoObligation, collReserveAddr: Address, debtReserveAddr: Address, repayAmountLamports: Decimal): {
    maxWithdrawableCollLamports: Decimal;
    canWithdrawAllColl: boolean;
    repayingAllDebt: boolean;
};
export declare function estimateDebtRepaymentWithColl(props: {
    collAmount: Decimal;
    priceDebtToColl: Decimal;
    slippagePct: Decimal;
    flashLoanFeePct: Decimal;
    kaminoMarket: KaminoMarket;
    debtTokenMint: Address;
    obligation: KaminoObligation;
    currentSlot: Slot;
}): Decimal;
export declare function estimateCollNeededForDebtRepayment(props: {
    debtAmount: Decimal;
    priceDebtToColl: Decimal;
    slippagePct: Decimal;
    flashLoanFeePct: Decimal;
}): Decimal;
//# sourceMappingURL=repay_with_collateral_calcs.d.ts.map