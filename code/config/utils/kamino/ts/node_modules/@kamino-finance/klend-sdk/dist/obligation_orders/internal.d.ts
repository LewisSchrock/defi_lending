import { KaminoObligationOrder, OrderCondition } from '../classes/obligationOrder';
import { OrderContext, OrderSpecification, OrderType } from './common';
export declare function toOrderIndex(orderType: OrderType): number;
export declare function createConditionBasedOrder<C>(context: OrderContext, condition: OrderCondition, specification: OrderSpecification<C>): KaminoObligationOrder;
export declare function readTriggerBasedOrder<T>(kaminoOrder: KaminoObligationOrder, trigger: T): OrderSpecification<T>;
//# sourceMappingURL=internal.d.ts.map