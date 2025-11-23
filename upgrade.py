import asyncio, math
MAX_STARS = 250
GIFT_OFFSETS = [17*3, 17*3+1]
GIFT_NFT_SLUGS = [
    [
        [*range(0, 1)],
        "CloverPin-"
    ],
    [
        [1],
        "FreshSocks-"
    ]
]

gifts = {
    "gifts": [
    ]
}
can_upgrade = False
for off in GIFT_OFFSETS:
    while not can_upgrade: # одинаково для каждого подарка, так что достаточно одного подтверждения от одного типа
        async for gift in self.client.get_saved_gifts("me", offset=f'{off}', limit=1, exclude_nft=True, exclude_unlimited=True):
            can_upgrade = gift.gift.upgrade_stars <= MAX_STARS
            if not can_upgrade: await asyncio.sleep(60)  
    gifts["gifts"].append({
        "gift": [*(await self.client.get_saved_gifts("me", offset=f'{off}', limit=1, exclude_nft=True, exclude_unlimited=True))][0],
        }
    )

for filler in GIFT_NFT_SLUGS:
    for i in filler[0]:
        gifts["gifts"][i]["slug"] = filler[1]
    
self.selected = {}
async def get_min(gift):
    key = gift["slug"]
    selected_for_gift = self.selected.setdefault(key, [])

    availability = (await self.client(GetUniqueStarGiftRequest(f"{key}1"))).gift.availability_issued

    next_thousand = math.ceil(availability / 1000) * 1000
    nextnext_tho = next_thousand + 1000

    s = str(availability)
    len_s = len(s)

    rep_candidates = []
    for L in range(len_s, len_s + 5):
        for d in range(1, 10):
            rep = int(str(d) * L)
            if rep >= availability:
                rep_candidates.append(rep)

    next_repdigit = min(rep_candidates) if rep_candidates else next_thousand

    if "9" not in str(next_repdigit):
        nextnext_rep = next_repdigit + int("1" * len_s)
    else:
        nextnext_rep = int("1" * (len(str(next_repdigit)) + 1))

    number = min((next_thousand, next_repdigit), key=lambda x: x - availability)

    if number in selected_for_gift:
        alt_candidates = [nextnext_tho, nextnext_rep, next_thousand, next_repdigit]
        for cand in sorted(set(alt_candidates), key=lambda x: x - availability):
            if cand not in selected_for_gift:
                number = cand
                break
        else:
            cand = number
            while cand in selected_for_gift:
                cand += 1000
            number = cand

    selected_for_gift.append(number)

    await m.respond(f"{key} — {number}")
    return number
    
async def upgrade(gift, need_to):
    sleep = 20
    issued = 0
    while True:
        try:
            issued = (await self.client(GetUniqueStarGiftRequest(f"{gift['slug']}1"))).gift.availability_issued if sleep != 1 else 5000 # JollyChimp-1 или MoonPendant-1 уже существуют и ошибки в первой строке не будет
            await self.client(GetUniqueStarGiftRequest(f"{gift['slug']}{need_to-2}"))
            break
        except Exception as e:
            if "SLUG" not in str(e):
                await m.respond(str(e))
            if issued > need_to-200:
                sleep = 1
            await asyncio.sleep(sleep)
    try:
        await gift["gift"].upgrade()
    except:
        await asyncio.sleep(0.3)
        await gift["gift"].upgrade()
        
await m.respond("К автоулучшению с определённым номером готов!")
needs = [await get_min(g) for g in gifts["gifts"]] 
await asyncio.gather(*(upgrade(gift, need) for gift, need in zip(gifts["gifts"], needs)))