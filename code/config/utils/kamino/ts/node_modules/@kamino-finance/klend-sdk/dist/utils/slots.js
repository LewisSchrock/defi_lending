"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.toSeconds = toSeconds;
exports.toHours = toHours;
exports.toDays = toDays;
const constants_1 = require("./constants");
/**
 * Convert slots to seconds
 * @param slots
 * @return seconds
 */
function toSeconds(slots) {
    return Math.trunc(slots / constants_1.SLOTS_PER_SECOND);
}
/**
 * Convert slots to hours
 * @param slots
 * @return hours
 */
function toHours(slots) {
    return Math.trunc(slots / constants_1.SLOTS_PER_HOUR);
}
/**
 * Convert slots to days
 * @param slots
 * @return days
 */
function toDays(slots) {
    return Math.trunc(slots / constants_1.SLOTS_PER_DAY);
}
//# sourceMappingURL=slots.js.map