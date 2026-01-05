"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getUserLutAddressAndSetupIxs = void 0;
exports.getAllUserMetadatasWithFilter = getAllUserMetadatasWithFilter;
const kit_1 = require("@solana/kit");
const lib_1 = require("../lib");
const buffer_1 = require("buffer");
const system_1 = require("@solana-program/system");
const sysvars_1 = require("@solana/sysvars");
const address_lookup_table_1 = require("@solana-program/address-lookup-table");
const getUserLutAddressAndSetupIxs = async (kaminoMarket, user, referrer = (0, kit_1.none)(), withExtendLut = true, multiplyMints = [], leverageMints = [], repayWithCollObligation = undefined, payer = user) => {
    const [userMetadataAddress, userMetadataState] = await kaminoMarket.getUserMetadata(user.address);
    const initUserMetadataIxs = [];
    let userLookupTableAddress;
    if (userMetadataState === null) {
        const referrerUserMetadata = (0, kit_1.isSome)(referrer)
            ? (0, kit_1.some)((await kaminoMarket.getUserMetadata(referrer.value))[0])
            : (0, kit_1.none)();
        const [createLutIx, lookupTableAddress] = await (0, lib_1.createLookupTableIx)(kaminoMarket.getRpc(), user);
        userLookupTableAddress = lookupTableAddress;
        initUserMetadataIxs.push(createLutIx);
        initUserMetadataIxs.push((0, lib_1.initUserMetadata)({
            userLookupTable: lookupTableAddress,
        }, {
            owner: user,
            feePayer: payer,
            userMetadata: userMetadataAddress,
            referrerUserMetadata,
            rent: sysvars_1.SYSVAR_RENT_ADDRESS,
            systemProgram: system_1.SYSTEM_PROGRAM_ADDRESS,
        }, undefined, kaminoMarket.programId));
    }
    else {
        userLookupTableAddress = userMetadataState.userLookupTable;
        referrer = userMetadataState.referrer === lib_1.DEFAULT_PUBLIC_KEY ? (0, kit_1.none)() : (0, kit_1.some)(userMetadataState.referrer);
    }
    const setupUserMetadataIxs = [initUserMetadataIxs];
    if (withExtendLut) {
        const dedupUserLutAddresses = await getDedupUserLookupTableAddresses(kaminoMarket, userLookupTableAddress, user.address, referrer, multiplyMints, leverageMints, userMetadataState !== null, repayWithCollObligation);
        const extendLookupTableChunkIxs = (0, lib_1.extendLookupTableIxs)(user, userLookupTableAddress, dedupUserLutAddresses, payer);
        for (const extendLutIx of extendLookupTableChunkIxs) {
            setupUserMetadataIxs.push([extendLutIx]);
        }
    }
    return [userLookupTableAddress, setupUserMetadataIxs];
};
exports.getUserLutAddressAndSetupIxs = getUserLutAddressAndSetupIxs;
const getDedupUserLookupTableAddresses = async (kaminoMarket, tableAddress, user, referrer, multiplyMints = [], leverageMints = [], tableExists, repayWithCollObligation = undefined) => {
    const requiredAddresses = await getUserLookupTableAddresses(kaminoMarket, user, referrer, multiplyMints, leverageMints, repayWithCollObligation);
    if (tableExists) {
        const userLookupTable = (await (0, address_lookup_table_1.fetchAddressLookupTable)(kaminoMarket.getRpc(), tableAddress)).data;
        const addressesAndLogsNotInLut = requiredAddresses.filter((addressAndLogs) => userLookupTable.addresses.filter((a) => a === addressAndLogs.address).length === 0);
        console.log('Addresses to be added in LUT:');
        const addressNotInLut = addressesAndLogsNotInLut.map((addressAndLogs) => {
            console.log(addressAndLogs.log);
            return addressAndLogs.address;
        });
        return [...new Set(addressNotInLut)];
    }
    else {
        const addressNotInLut = requiredAddresses.map((addressAndLogs) => {
            console.log(addressAndLogs.log);
            return addressAndLogs.address;
        });
        return [...new Set(addressNotInLut)];
    }
};
const getUserLookupTableAddresses = async (kaminoMarket, user, referrer, multiplyMints = [], leverageMints = [], repayWithCollObligation = undefined) => {
    const addresses = [];
    addresses.push({ address: user, log: 'user address' });
    const [userMetadataAddress] = await (0, lib_1.userMetadataPda)(user, kaminoMarket.programId);
    addresses.push({ address: userMetadataAddress, log: 'userMetadata address' });
    const allMints = [];
    multiplyMints.forEach(({ coll: collMint, debt: debtMint }) => {
        allMints.push(collMint);
        allMints.push(debtMint);
    });
    leverageMints.forEach(({ coll: collMint, debt: debtMint }) => {
        allMints.push(collMint);
        allMints.push(debtMint);
    });
    if (repayWithCollObligation) {
        repayWithCollObligation.borrows.forEach((borrow) => {
            allMints.push(borrow.mintAddress);
        });
        repayWithCollObligation.deposits.forEach((deposit) => {
            allMints.push(deposit.mintAddress);
        });
    }
    const dedupMints = [...new Set(allMints)];
    const reserves = [];
    dedupMints.forEach((mint) => {
        const kaminoReserve = kaminoMarket.getReserveByMint(mint);
        if (kaminoReserve) {
            reserves.push(kaminoReserve);
        }
    });
    // reserve mint ATAs
    const mintsAtas = await Promise.all(dedupMints.map(async (mint) => {
        return { address: await (0, lib_1.getAssociatedTokenAddress)(mint, user), log: 'ata for mint ' + mint.toString() };
    }));
    addresses.push(...mintsAtas);
    // ctoken ATAs
    const ctokenMintsAtas = await Promise.all(reserves.map(async (reserve) => {
        const ctokenMint = reserve.getCTokenMint();
        return {
            address: await (0, lib_1.getAssociatedTokenAddress)(ctokenMint, user),
            log: 'ctoken ata for reserve ' + reserve.address.toString(),
        };
    }));
    addresses.push(...ctokenMintsAtas);
    // farm states
    const farmCollateralStates = reserves.map((reserve) => reserve.state.farmCollateral);
    const farmDebtStates = reserves.map((reserve) => reserve.state.farmDebt);
    const farmStates = new Set(farmCollateralStates.concat(farmDebtStates).filter((address) => (0, lib_1.isNotNullPubkey)(address)));
    const farmStatesAdressesAndLogs = [...farmStates].map((address) => {
        return { address: address, log: 'farm state' };
    });
    addresses.push(...farmStatesAdressesAndLogs);
    if ((0, kit_1.isSome)(referrer)) {
        // referrer token states
        const referrerTokenStates = await Promise.all(reserves.map(async (reserve) => {
            return {
                address: await (0, lib_1.referrerTokenStatePda)(referrer.value, reserve.address, kaminoMarket.programId),
                log: `referrer token state for reserve ${reserve.address}`,
            };
        }));
        addresses.push(...referrerTokenStates);
    }
    const [multiplyObligations, multiplyObligationsFarmUserStates] = await getMultiplyObligationAndObligationFarmStateAddresses(kaminoMarket, user, multiplyMints);
    addresses.push(...multiplyObligations);
    addresses.push(...multiplyObligationsFarmUserStates);
    const [leverageObligations, leverageObligationsFarmUserStates] = await getLeverageObligationAndObligationFarmStateAddresses(kaminoMarket, user, leverageMints);
    addresses.push(...leverageObligations);
    addresses.push(...leverageObligationsFarmUserStates);
    if (repayWithCollObligation) {
        const repayWithCollFarmUserStates = await getRepayWithCollObligationFarmStateAddresses(kaminoMarket, repayWithCollObligation);
        addresses.push(...repayWithCollFarmUserStates);
        addresses.push({ address: repayWithCollObligation.obligationAddress, log: 'repay with coll obligation' });
    }
    return addresses;
};
async function getMultiplyObligationAndObligationFarmStateAddresses(kaminoMarket, user, mints) {
    const obligationPdas = [];
    const farmUserStates = [];
    for (const { coll: collMint, debt: debtMint } of mints) {
        const collReserve = kaminoMarket.getReserveByMint(collMint);
        const debtReserve = kaminoMarket.getReserveByMint(debtMint);
        const collMintString = collMint.toString();
        const debtMintString = debtMint.toString();
        if (collReserve && debtReserve) {
            const multiplyObligation = new lib_1.MultiplyObligation(collMint, debtMint, kaminoMarket.programId);
            obligationPdas.push({
                address: await multiplyObligation.toPda(kaminoMarket.getAddress(), user),
                log: 'multiply obligation coll: ' + collMintString + ' debt: ' + debtMintString,
            });
            if (collReserve.state.farmCollateral !== lib_1.DEFAULT_PUBLIC_KEY) {
                farmUserStates.push({
                    address: await (0, lib_1.obligationFarmStatePda)(collReserve.state.farmCollateral, await multiplyObligation.toPda(kaminoMarket.getAddress(), user)),
                    log: 'collReserve farmState for multiply obligation coll: ' + collMintString + ' debt: ' + debtMintString,
                });
            }
            if (debtReserve.state.farmDebt !== lib_1.DEFAULT_PUBLIC_KEY) {
                farmUserStates.push({
                    address: await (0, lib_1.obligationFarmStatePda)(debtReserve.state.farmDebt, await multiplyObligation.toPda(kaminoMarket.getAddress(), user)),
                    log: 'debtReserve farmState for multiply obligation coll: ' + collMintString + ' debt: ' + debtMintString,
                });
            }
        }
    }
    return [obligationPdas, farmUserStates];
}
async function getLeverageObligationAndObligationFarmStateAddresses(kaminoMarket, user, mints) {
    const obligationPdas = [];
    const farmUserStates = [];
    for (const { coll: collMint, debt: debtMint } of mints) {
        const collReserve = kaminoMarket.getReserveByMint(collMint);
        const debtReserve = kaminoMarket.getReserveByMint(debtMint);
        const collMintString = collMint.toString();
        const debtMintString = debtMint.toString();
        if (collReserve && debtReserve) {
            const leverageObligation = new lib_1.LeverageObligation(collMint, debtMint, kaminoMarket.programId);
            obligationPdas.push({
                address: await leverageObligation.toPda(kaminoMarket.getAddress(), user),
                log: 'leverage obligation coll: ' + collMintString + ' debt: ' + debtMintString,
            });
            if (collReserve.state.farmCollateral !== lib_1.DEFAULT_PUBLIC_KEY) {
                farmUserStates.push({
                    address: await (0, lib_1.obligationFarmStatePda)(collReserve.state.farmCollateral, await leverageObligation.toPda(kaminoMarket.getAddress(), user)),
                    log: 'collReserve farmState for leverage obligation coll: ' + collMintString + ' debt: ' + debtMintString,
                });
            }
            if (debtReserve.state.farmDebt !== lib_1.DEFAULT_PUBLIC_KEY) {
                farmUserStates.push({
                    address: await (0, lib_1.obligationFarmStatePda)(debtReserve.state.farmDebt, await leverageObligation.toPda(kaminoMarket.getAddress(), user)),
                    log: 'debtReserve farmState for leverage obligation coll: ' + collMintString + ' debt: ' + debtMintString,
                });
            }
        }
    }
    return [obligationPdas, farmUserStates];
}
async function getRepayWithCollObligationFarmStateAddresses(kaminoMarket, obligation) {
    const farmUserStates = [];
    const obligationString = obligation.obligationAddress.toString();
    for (const borrow of obligation.getBorrows()) {
        const borrowReserve = kaminoMarket.getReserveByMint(borrow.mintAddress);
        if (borrowReserve.state.farmDebt !== lib_1.DEFAULT_PUBLIC_KEY) {
            farmUserStates.push({
                address: await (0, lib_1.obligationFarmStatePda)(borrowReserve.state.farmDebt, obligation.obligationAddress),
                log: 'debtReserve farmState for vanilla obligation: ' + obligationString,
            });
        }
    }
    for (const deposit of obligation.getDeposits()) {
        const depositReserve = kaminoMarket.getReserveByMint(deposit.mintAddress);
        if (depositReserve.state.farmCollateral !== lib_1.DEFAULT_PUBLIC_KEY) {
            farmUserStates.push({
                address: await (0, lib_1.obligationFarmStatePda)(depositReserve.state.farmCollateral, obligation.obligationAddress),
                log: 'collReserve farmState for vanilla obligation' + obligationString,
            });
        }
    }
    return farmUserStates;
}
async function getAllUserMetadatasWithFilter(rpc, filter, programId) {
    const filters = [
        {
            dataSize: BigInt(lib_1.UserMetadata.layout.span + 8),
        },
        ...filter,
    ];
    const userMetadatas = await rpc
        .getProgramAccounts(programId, {
        filters,
        encoding: 'base64',
    })
        .send();
    return userMetadatas.map((userMetadata) => {
        if (userMetadata.account.owner !== programId) {
            throw new Error("account doesn't belong to this program");
        }
        const userMetadataAccount = lib_1.UserMetadata.decode(buffer_1.Buffer.from(userMetadata.account.data[0], 'base64'));
        if (!userMetadataAccount) {
            throw Error('Could not parse user metadata.');
        }
        return { address: userMetadata.pubkey, state: userMetadataAccount };
    });
}
//# sourceMappingURL=userMetadata.js.map