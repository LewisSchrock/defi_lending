"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.downloadUserMetadatasWithFilter = downloadUserMetadatasWithFilter;
const utils_1 = require("../../utils");
const fs_1 = __importDefault(require("fs"));
async function downloadUserMetadatasWithFilter(c, filter, output, programId) {
    const userMetadatas = await (0, utils_1.getAllUserMetadatasWithFilter)(c.rpc, filter, programId);
    // help mapping
    const userPubkeys = userMetadatas.map((userMetadatas) => userMetadatas.address.toString());
    if (output) {
        fs_1.default.writeFileSync(output, JSON.stringify(userPubkeys, null, 2));
    }
    else {
        for (const userPubkey of userPubkeys) {
            console.log(userPubkey);
        }
    }
    console.log('Total of ' + userPubkeys.length + ' userMetadatas filtered');
}
//# sourceMappingURL=userMetadata.js.map