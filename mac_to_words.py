vendors = ["dc:a6:32:00:00:00"]   # only append to this list

adjectives = [x.strip() for x in open("adjectives.txt")]
nouns      = [x.strip() for x in open("nouns.txt")]
assert len(adjectives) == 4096
assert len(nouns) == 4096

def lcg_generator(state, multiplier=1140671485, addend=12820163, pmod=2**24):
    state = (multiplier*state + addend) % pmod
    return state

def address_to_addr(address):
    return int(address.replace(":", ""), 16)

def addr_to_address(addr):
    out = hex(addr).replace("0x", "")
    return ":".join(out[2*i:2*i + 2] for i in range(6))

vendor_mask    = 0xffffff000000
adjective_mask = 0x000000fff000
noun_mask      = 0x000000000fff

def address_to_word(address):
    addr = address_to_addr(address)
    state = (addr & ~vendor_mask)

    for vendor_id, vendor_address in enumerate(vendors):
        vendor_addr = address_to_addr(vendor_address)
        if (addr & vendor_mask) == (vendor_addr & vendor_mask):
            break
    else:
        raise ValueError(f"unrecognized vendor: {addr_to_address(addr & vendor_mask)}")

    for i in range(vendor_id + 1):
        state = lcg_generator(state)

    while True:
        adjective = adjectives[(state & adjective_mask) >> 12]
        noun = nouns[state & noun_mask]
        if adjective != "" and noun != "" and len(adjective) + len(noun) < 20:
            return adjective + " " + noun
        state = lcg_generator(state)

addresses = [
    "dc:a6:32:8f:67:58",
    "dc:a6:32:8f:67:46",
    "dc:a6:32:82:f6:a2",
    "dc:a6:32:83:73:79",
    "dc:a6:32:8f:55:64",
    "dc:a6:32:83:73:4f",
    "dc:a6:32:8f:67:8b",
    "dc:a6:32:87:49:e7",
    "dc:a6:32:8f:67:0e",
    "dc:a6:32:83:73:b5",
    "dc:a6:32:83:71:84",
    "dc:a6:32:80:73:99",
    "dc:a6:32:83:6f:fb",
    "dc:a6:32:87:4a:11",
    "dc:a6:32:83:73:3d",
    "dc:a6:32:87:4c:a2",
    "dc:a6:32:84:e4:2e",
    "dc:a6:32:83:71:45",
    "dc:a6:32:71:76:71",
    "dc:a6:32:82:99:ba"]

for address in addresses:
    print(address, "->", address_to_word(address))
