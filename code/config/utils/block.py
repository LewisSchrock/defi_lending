def block_for_ts(w3, ts):
    lo, hi = 1, w3.eth.block_number
    ans = hi
    while lo <= hi:
        mid = (lo + hi) // 2
        t = w3.eth.get_block(mid)["timestamp"]
        if t >= ts:
            ans = mid
            hi = mid - 1
        else:
            lo = mid + 1
    return ans