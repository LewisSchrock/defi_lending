"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.sendAndConfirmTx = sendAndConfirmTx;
exports.fetchBlockhash = fetchBlockhash;
exports.sendAndConfirmTxImpl = sendAndConfirmTxImpl;
const kit_1 = require("@solana/kit");
async function sendAndConfirmTx(c, payer, ixs, luts = []) {
    const blockhash = await fetchBlockhash(c.rpc);
    const lutsByAddress = {};
    if (luts.length > 0) {
        for (const acc of luts) {
            lutsByAddress[acc.address] = acc.data.addresses;
        }
    }
    const tx = await (0, kit_1.pipe)((0, kit_1.createTransactionMessage)({ version: 0 }), (tx) => (0, kit_1.appendTransactionMessageInstructions)(ixs, tx), (tx) => (0, kit_1.setTransactionMessageFeePayerSigner)(payer, tx), (tx) => (0, kit_1.setTransactionMessageLifetimeUsingBlockhash)(blockhash, tx), (tx) => (0, kit_1.compressTransactionMessageUsingAddressLookupTables)(tx, lutsByAddress), (tx) => (0, kit_1.signTransactionMessageWithSigners)(tx));
    const sig = (0, kit_1.getSignatureFromTransaction)(tx);
    try {
        await sendRpc(c, tx, sig, blockhash);
    }
    catch (e) {
        console.error(`Transaction ${sig} failed:`, e);
        let tx;
        try {
            tx = await c.rpc
                .getTransaction(sig, {
                maxSupportedTransactionVersion: 0,
                commitment: 'confirmed',
                encoding: 'json',
            })
                .send();
        }
        catch (e2) {
            console.error('Error fetching transaction logs:', e2);
            throw e;
        }
        if (tx && tx.meta?.logMessages) {
            console.log('Transaction logs:', tx.meta.logMessages);
        }
        else {
            console.log('Transaction logs not found');
        }
        throw e;
    }
    return sig;
}
async function fetchBlockhash(rpc) {
    const res = await rpc.getLatestBlockhash({ commitment: 'finalized' }).send();
    return {
        blockhash: res.value.blockhash,
        lastValidBlockHeight: res.value.lastValidBlockHeight,
        slot: res.context.slot,
    };
}
async function sendRpc(c, tx, sig, blockhash) {
    if (c.shouldSpam) {
        let confirmed = false;
        let intervalId = undefined;
        const stopSendingTx = () => {
            if (intervalId) {
                clearInterval(intervalId);
            }
        };
        const send = () => {
            if (confirmed) {
                return;
            }
            console.log(`Spamming tx ${sig}`);
            sendTx(c.rpc, tx, blockhash).catch((e) => console.log(`Spamming tx failed`, e));
        };
        intervalId = setInterval(() => {
            send();
        }, 2000);
        await sendAndConfirmTxImpl(c, tx, blockhash.slot)
            .then(() => {
            confirmed = true;
            console.log(`Success ${sig}`);
            stopSendingTx();
            return sig;
        })
            .catch((e) => {
            stopSendingTx();
            throw e;
        })
            .finally(() => stopSendingTx());
        return sig;
    }
    else {
        await sendAndConfirmTxImpl(c, tx, blockhash.slot);
        console.log(`Success ${sig}`);
        return sig;
    }
}
async function sendAndConfirmTxImpl({ rpc, wsRpc, }, tx, slot) {
    await (0, kit_1.sendAndConfirmTransactionFactory)({ rpc, rpcSubscriptions: wsRpc })(tx, {
        commitment: 'confirmed',
        preflightCommitment: 'confirmed',
        maxRetries: 0n,
        skipPreflight: true,
        minContextSlot: slot,
    });
}
async function sendTx(rpc, tx, blockhash) {
    const serialized = (0, kit_1.getBase64EncodedWireTransaction)(tx);
    await rpc
        .sendTransaction(serialized, {
        encoding: 'base64',
        preflightCommitment: 'confirmed',
        maxRetries: 0n,
        skipPreflight: true,
        minContextSlot: blockhash.slot,
    })
        .send();
}
//# sourceMappingURL=tx.js.map