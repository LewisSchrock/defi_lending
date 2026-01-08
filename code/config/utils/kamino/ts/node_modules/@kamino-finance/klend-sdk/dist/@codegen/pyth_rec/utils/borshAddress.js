"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.borshAddress = borshAddress;
const kit_1 = require("@solana/kit");
const buffer_layout_1 = require("buffer-layout");
const addressCodec = (0, kit_1.getAddressCodec)();
function borshAddress(property) {
    return new WrappedLayout((0, buffer_layout_1.blob)(32), (b) => addressCodec.decode(b), (addr) => Buffer.from(addressCodec.encode(addr)), property);
}
class WrappedLayout extends buffer_layout_1.Layout {
    layout;
    decoder;
    encoder;
    constructor(layout, decoder, encoder, property) {
        super(layout.span, property);
        this.layout = layout;
        this.decoder = decoder;
        this.encoder = encoder;
    }
    decode(b, offset) {
        return this.decoder(this.layout.decode(b, offset));
    }
    encode(src, b, offset) {
        return this.layout.encode(this.encoder(src), b, offset);
    }
    getSpan(b, offset) {
        return this.layout.getSpan(b, offset);
    }
}
//# sourceMappingURL=borshAddress.js.map