"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.checkThat = checkThat;
exports.checkDefined = checkDefined;
exports.checkNotNull = checkNotNull;
exports.getSingleElement = getSingleElement;
function checkThat(evaluationResult, message = 'precondition failed') {
    if (!evaluationResult) {
        throw new Error(message);
    }
}
function checkDefined(value, message = 'value undefined') {
    checkThat(value !== undefined, message);
    return value;
}
function checkNotNull(value, message = 'value null') {
    checkThat(value !== null, message);
    return value;
}
function getSingleElement(iterable, nameWithinMessage = 'element') {
    const nothingReturnedMarker = {};
    let single = nothingReturnedMarker;
    for (const element of iterable) {
        if (single === nothingReturnedMarker) {
            single = element;
        }
        else {
            throw new Error(`exactly one ${nameWithinMessage} expected, but multiple found`);
        }
    }
    if (single === nothingReturnedMarker) {
        throw new Error(`exactly one ${nameWithinMessage} expected, but none found`);
    }
    return single;
}
//# sourceMappingURL=validations.js.map