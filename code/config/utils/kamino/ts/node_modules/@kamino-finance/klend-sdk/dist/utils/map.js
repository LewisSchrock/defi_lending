"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.setOrAppend = setOrAppend;
function setOrAppend(map, key, value) {
    const existing = map.get(key);
    if (existing) {
        existing.push(value);
    }
    else {
        map.set(key, [value]);
    }
}
//# sourceMappingURL=map.js.map