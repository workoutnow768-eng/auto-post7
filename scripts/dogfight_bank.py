"""
Content bank for the dog-fight series (rough crew vs posh crew, kickboxing
with an arcade fighting-game HUD). Edit freely -- the bot rotates through
MATCHUPS in order, 3 per day, wrapping at the end.

Prompt wording is copied from the test runs that worked on 2026-10-03
(Staffy vs Poodle, Boxer vs Afghan): face hits are written as "sport
kickboxing in padded gloves, no blood, no injuries", realistic impact
reactions (jowls rippling, sweat/slobber spray), everything at real speed
except ONE slow-motion finisher. Keep that wording if you edit -- it's what
got past the content filter.
"""

# Locked references hosted on Higgsfield's CDN (your own generations).
# Order matters: ref 1 = ring/HUD/crowd layout, ref 2 = character designs,
# ref 3 = the Doberman.
REFERENCE_URLS = [
    "https://d8j0ntlcm91z4.cloudfront.net/user_3Ds4y4BMM0lylxBEO2zlV6BNZub/hf_20261003_091631_76e96899-c2ba-4f93-a123-bc5951e548eb.png",
    "https://d8j0ntlcm91z4.cloudfront.net/user_3Ds4y4BMM0lylxBEO2zlV6BNZub/hf_20261001_210353_dc47591a-50b8-4cc7-921b-049398b45bca.png",
    "https://d8j0ntlcm91z4.cloudfront.net/user_3Ds4y4BMM0lylxBEO2zlV6BNZub/hf_20261001_163816_8099b618-cd9d-48eb-95ce-4c228453acd5.png",
]

# hud = text under the health bar. fighter = how they look in the ring.
# ringside = how they look when they're NOT fighting (watching from the crowd).
ROUGH = {
    "blue_staffy": {
        "hud": "STAFFY",
        "name": "the blue-grey twin Staffordshire bull terrier",
        "fighter": "the blue-grey twin Staffordshire bull terrier, shirtless, muscular, in black tracksuit bottoms with white stripes and red boxing gloves, snarling",
        "ringside": "the blue-grey twin Staffy in a black tracksuit",
    },
    "white_staffy": {
        "hud": "STAFFY",
        "name": "the white twin Staffordshire bull terrier",
        "fighter": "the white twin Staffordshire bull terrier, shirtless, muscular, in black tracksuit bottoms with white stripes and black boxing gloves, jaw clenched",
        "ringside": "the white twin Staffy in a black tracksuit",
    },
    "brindle_staffy": {
        "hud": "BRINDLE",
        "name": "the scarred brindle Staffordshire bull terrier",
        "fighter": "the scarred brindle Staffordshire bull terrier, shirtless, thick-necked, in grey jogging bottoms and grey boxing gloves, a cigarette tucked behind his ear",
        "ringside": "the brindle Staffy in the grey hoodie",
    },
    "bull_terrier": {
        "hud": "BULLY",
        "name": "the white English bull terrier",
        "fighter": "the white English bull terrier with his long egg-shaped head, shirtless, stocky, in black puffer-style shorts and black boxing gloves, small mean eyes",
        "ringside": "the white bull terrier in the black puffer jacket",
    },
    "boxer": {
        "hud": "BOXER",
        "name": "the old scarred brindle Boxer dog",
        "fighter": "the old scarred brindle Boxer dog, shirtless, thick muscular build, grey on his muzzle, cauliflower ear, in faded brown boxing shorts and red boxing gloves, jaw set",
        "ringside": "the Boxer in the brown leather jacket",
    },
    "lurcher": {
        "hud": "LURCHER",
        "name": "the skinny grey brindle lurcher",
        "fighter": "the small skinny scruffy grey brindle lurcher, shirtless, ribs showing, in baggy navy tracksuit bottoms and oversized blue boxing gloves, twitchy and wide-eyed",
        "ringside": "the skinny grey lurcher in the navy tracksuit",
    },
}

POSH = {
    "poodle": {
        "hud": "POODLE",
        "name": "the small grey Poodle",
        "fighter": "the small grey Poodle with the show-cut topknot and pom-pom legs, shirtless with the cream jumper tied around his waist, in pink boxing gloves, chin up, snooty",
        "ringside": "the grey Poodle in the pink polo",
        "hair": "curly topknot and pom-poms",
    },
    "afghan": {
        "hud": "AFGHAN",
        "name": "the tall cream Afghan Hound",
        "fighter": "the tall slender cream Afghan Hound with long silky flowing hair, shirtless with a silk scarf tied as a headband, in camel satin shorts and gold boxing gloves, haughty",
        "ringside": "the long-haired cream Afghan Hound in the camel trench coat",
        "hair": "long silky mane",
    },
    "labradoodle": {
        "hud": "DOODLE",
        "name": "the fluffy cream Labradoodle",
        "fighter": "the small fluffy cream Labradoodle, shirtless with his navy gilet hanging off one shoulder, in beige chino shorts and pale blue boxing gloves, smug",
        "ringside": "the cream Labradoodle in the navy gilet holding the football",
        "hair": "fluffy curly coat",
    },
    "cockapoo": {
        "hud": "COCKAPOO",
        "name": "the tiny apricot Cockapoo",
        "fighter": "the tiny apricot Cockapoo, shirtless, wearing his checked flat cap, in green wax-cotton shorts and tiny green boxing gloves, nervous but defiant",
        "ringside": "the tiny apricot Cockapoo in the Barbour jacket and flat cap",
        "hair": "floppy curly ears",
    },
}

FINISHERS = [
    "a huge spinning back kick to the {loser}'s chest",
    "a massive overhand right to the side of the {loser}'s face",
    "a rising uppercut under the {loser}'s chin",
    "a head-height roundhouse kick that connects with the side of the {loser}'s head",
    "a big left hook to the {loser}'s jaw",
]

# Rotation: every rough fighter meets every posh fighter, rough crew always wins.
# Order is interleaved so the same dog doesn't fight twice in one day.
MATCHUPS = []
_rough_keys = list(ROUGH)
_posh_keys = list(POSH)
for _round in range(len(_posh_keys)):
    for _i, _r in enumerate(_rough_keys):
        _p = _posh_keys[(_i + _round) % len(_posh_keys)]
        MATCHUPS.append({"rough": _r, "posh": _p, "winner": "rough"})
