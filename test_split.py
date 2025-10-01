import typing
import herokutl

import grapheme
from herokutl.tl.types import (
    MessageEntityBankCard,
    MessageEntityBlockquote,
    MessageEntityBold,
    MessageEntityBotCommand,
    MessageEntityCashtag,
    MessageEntityCode,
    MessageEntityEmail,
    MessageEntityHashtag,
    MessageEntityItalic,
    MessageEntityMention,
    MessageEntityMentionName,
    MessageEntityPhone,
    MessageEntityPre,
    MessageEntitySpoiler,
    MessageEntityStrike,
    MessageEntityTextUrl,
    MessageEntityUnderline,
    MessageEntityUnknown,
    MessageEntityUrl,
)

ListLike = typing.Union[list, set, tuple]

FormattingEntity = typing.Union[
    MessageEntityUnknown,
    MessageEntityMention,
    MessageEntityHashtag,
    MessageEntityBotCommand,
    MessageEntityUrl,
    MessageEntityEmail,
    MessageEntityBold,
    MessageEntityItalic,
    MessageEntityCode,
    MessageEntityPre,
    MessageEntityTextUrl,
    MessageEntityMentionName,
    MessageEntityPhone,
    MessageEntityCashtag,
    MessageEntityUnderline,
    MessageEntityStrike,
    MessageEntityBlockquote,
    MessageEntityBankCard,
    MessageEntitySpoiler,
]

parser = herokutl.utils.sanitize_parse_mode("html")
def _copy_tl(o, **kwargs):
    d = o.to_dict()
    del d["_"]
    d.update(kwargs)
    return o.__class__(**d)

def smart_split(
    text: str,
    entities: typing.List[FormattingEntity],
    length: int = 4096,
    split_on: ListLike = ("\n", " "),
    min_length: int = 1,
) -> typing.Iterator[str]:
    """
    Split the message into smaller messages.
    A grapheme will never be broken. Entities will be displaced to match the right location. No inputs will be mutated.
    The end of each message except the last one is stripped of characters from [split_on]
    :param text: the plain text input
    :param entities: the entities
    :param length: the maximum length of a single message
    :param split_on: characters (or strings) which are preferred for a message break
    :param min_length: ignore any matches on [split_on] strings before this number of characters into each message
    :return: iterator, which returns strings

    :example:
        >>> utils.smart_split(
            *herokutl.extensions.html.parse(
                "<b>Hello, world!</b>"
            )
        )
        <<< ["<b>Hello, world!</b>"]
    """

    # Authored by @bsolute
    # https://t.me/LonamiWebs/27777

    encoded = text.encode("utf-16le")
    pending_entities = entities
    text_offset = 0
    bytes_offset = 0
    text_length = len(text)
    bytes_length = len(encoded)

    while text_offset < text_length:
        if bytes_offset + length * 2 >= bytes_length:
            yield parser.unparse(
                text[text_offset:],
                list(sorted(pending_entities, key=lambda x: (x.offset, -x.length))),
            )
            break

        codepoint_count = len(
            encoded[bytes_offset : bytes_offset + length * 2].decode(
                "utf-16le",
                errors="ignore",
            )
        )

        for search in split_on:
            search_index = text.rfind(
                search,
                text_offset + min_length,
                text_offset + codepoint_count,
            )
            if search_index != -1:
                break
        else:
            search_index = text_offset + codepoint_count

        split_index = grapheme.safe_split_index(text, search_index)

        split_offset_utf16 = (
            len(text[text_offset:split_index].encode("utf-16le"))
        ) // 2
        exclude = 0

        while (
            split_index + exclude < text_length
            and text[split_index + exclude] in split_on
        ):
            exclude += 1

        current_entities = []
        entities = pending_entities.copy()
        pending_entities = []

        for entity in entities:
            if (
                entity.offset < split_offset_utf16
                and entity.offset + entity.length > split_offset_utf16 + exclude
            ):
                # spans boundary
                current_entities.append(
                    _copy_tl(
                        entity,
                        length=split_offset_utf16 - entity.offset,
                    )
                )
                pending_entities.append(
                    _copy_tl(
                        entity,
                        offset=0,
                        length=entity.offset
                        + entity.length
                        - split_offset_utf16
                        - exclude,
                    )
                )
            elif entity.offset < split_offset_utf16 < entity.offset + entity.length:
                # overlaps boundary
                current_entities.append(
                    _copy_tl(
                        entity,
                        length=split_offset_utf16 - entity.offset,
                    )
                )
            elif entity.offset < split_offset_utf16:
                # wholly left
                current_entities.append(entity)
            elif (
                entity.offset + entity.length
                > split_offset_utf16 + exclude
                > entity.offset
            ):
                # overlaps right boundary
                pending_entities.append(
                    _copy_tl(
                        entity,
                        offset=0,
                        length=entity.offset
                        + entity.length
                        - split_offset_utf16
                        - exclude,
                    )
                )
            elif entity.offset + entity.length > split_offset_utf16 + exclude:
                # wholly right
                pending_entities.append(
                    _copy_tl(
                        entity,
                        offset=entity.offset - split_offset_utf16 - exclude,
                    )
                )

        current_text = text[text_offset:split_index]
        yield parser.unparse(
            current_text,
            list(sorted(current_entities, key=lambda x: (x.offset, -x.length))),
        )

        text_offset = split_index + exclude
        bytes_offset += len(current_text.encode("utf-16le"))

textm = """<emoji document_id=5875180111744995604>🎁</emoji> <b>Подарки (100/137 показано) у ‏󠆜⁧⁧⁧⁧ стик⁧Пуши</b>
<emoji document_id=5807868868886009920>👑</emoji> <b>NFTs (28):</b>
<blockquote expandable>
<emoji document_id=5402510413835302585>🖤</emoji> <a href='https://t.me/nft/TrappedHeart-19095'>Trapped Heart #19095</a>
  <emoji document_id=5796440171364749940>📌</emoji> <b>Закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>26407</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>14:50 18.02.2025</code>
  <b>Подробнее о подарке:</b> <code>gift TrappedHeart-19095</code>

<emoji document_id=5237992786778679797>🔔</emoji> <a href='https://t.me/nft/JingleBells-21381'>Jingle Bells #21381</a>
  <emoji document_id=5796440171364749940>📌</emoji> <b>Закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>124593</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>04:51 26.02.2025</code>
  <b>Подробнее о подарке:</b> <code>gift JingleBells-21381</code>

<emoji document_id=5195125946557952379>🥚</emoji> <a href='https://t.me/nft/EasterEgg-31266'>Easter Egg #31266</a>
  <emoji document_id=5796440171364749940>📌</emoji> <b>Закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>173176</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>06:20 12.05.2025</code>
  <b>Подробнее о подарке:</b> <code>gift EasterEgg-31266</code>

<emoji document_id=5411168522443186264>💀</emoji> <a href='https://t.me/nft/SkullFlower-15254'>Skull Flower #15254</a>
  <emoji document_id=5796440171364749940>📌</emoji> <b>Закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>24126</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>14:50 18.02.2025</code>
  <b>Подробнее о подарке:</b> <code>gift SkullFlower-15254</code>

<emoji document_id=5425029528663646777>🌹</emoji> <a href='https://t.me/nft/EternalRose-2438'>Eternal Rose #2438</a>
  <emoji document_id=5796440171364749940>📌</emoji> <b>Закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>37640</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>15:13 23.01.2025</code>
  <b>Подробнее о подарке:</b> <code>gift EternalRose-2438</code>

<emoji document_id=5440793772331915488>🧹</emoji> <a href='https://t.me/nft/FlyingBroom-12009'>Flying Broom #12009</a>
  <emoji document_id=5796440171364749940>📌</emoji> <b>Закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>25916</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>11:20 23.02.2025</code>
  <b>Подробнее о подарке:</b> <code>gift FlyingBroom-12009</code>

<emoji document_id=5228941881936732761>🔔</emoji> <a href='https://t.me/nft/JingleBells-27229'>Jingle Bells #27229</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>124593</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>08:52 07.03.2025</code>
  <b>Подробнее о подарке:</b> <code>gift JingleBells-27229</code>

<emoji document_id=5237930745976087093>🔔</emoji> <a href='https://t.me/nft/JingleBells-16603'>Jingle Bells #16603</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>124593</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>11:41 15.08.2025</code>
  <b>Подробнее о подарке:</b> <code>gift JingleBells-16603</code>

<emoji document_id=5235954665882937901>🔔</emoji> <a href='https://t.me/nft/JingleBells-9215'>Jingle Bells #9215</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>124593</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>20:16 20.02.2025</code>
  <b>Подробнее о подарке:</b> <code>gift JingleBells-9215</code>

<emoji document_id=5238024608191373985>🔔</emoji> <a href='https://t.me/nft/JingleBells-17958'>Jingle Bells #17958</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>124593</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>09:26 01.06.2025</code>
  <b>Подробнее о подарке:</b> <code>gift JingleBells-17958</code>

<emoji document_id=5271519159757335148>🔔</emoji> <a href='https://t.me/nft/SleighBell-4522'>Sleigh Bell #4522</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>28000</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>06:01 17.03.2025</code>
  <b>Подробнее о подарке:</b> <code>gift SleighBell-4522</code>

<emoji document_id=5237951344639237728>🔔</emoji> <a href='https://t.me/nft/JingleBells-59897'>Jingle Bells #59897</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>124593</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>22:09 25.07.2025</code>
  <b>Подробнее о подарке:</b> <code>gift JingleBells-59897</code>

<emoji document_id=5238102914035111848>🔔</emoji> <a href='https://t.me/nft/JingleBells-44012'>Jingle Bells #44012</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>124593</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>13:09 06.06.2025</code>
  <b>Подробнее о подарке:</b> <code>gift JingleBells-44012</code>

<emoji document_id=5404336062698910779>💐</emoji> <a href='https://t.me/nft/LushBouquet-40198'>Lush Bouquet #40198</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>140116</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>09:38 04.07.2025</code>
  <b>Подробнее о подарке:</b> <code>gift LushBouquet-40198</code>

<emoji document_id=5238134258706440526>🎇</emoji> <a href='https://t.me/nft/PartySparkler-75381'>Party Sparkler #75381</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>243771</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>16:07 24.07.2025</code>
  <b>Подробнее о подарке:</b> <code>gift PartySparkler-75381</code>

<emoji document_id=5339089560942963056>🍭</emoji> <a href='https://t.me/nft/CandyCane-16993'>Candy Cane #16993</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>320622</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>18:34 28.03.2025</code>
  <b>Подробнее о подарке:</b> <code>gift CandyCane-16993</code>

<emoji document_id=5233665362414823287>🗓</emoji> <a href='https://t.me/nft/DeskCalendar-151454'>Desk Calendar #151454</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>374077</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>07:54 18.03.2025</code>
  <b>Подробнее о подарке:</b> <code>gift DeskCalendar-151454</code>

<emoji document_id=5433945588712368149>❤️</emoji> <a href='https://t.me/nft/RestlessJar-24368'>Restless Jar #24368</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>120184</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>14:26 13.06.2025</code>
  <b>Подробнее о подарке:</b> <code>gift RestlessJar-24368</code>

<emoji document_id=5449868651681317077>🗡</emoji> <a href='https://t.me/nft/LightSword-41117'>Light Sword #41117</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>131222</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>10:13 10.06.2025</code>
  <b>Подробнее о подарке:</b> <code>gift LightSword-41117</code>

<emoji document_id=5271766584233322889>💎</emoji> <a href='https://t.me/nft/DiamondRing-22428'>Diamond Ring #22428</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>32924</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>19:31 08.03.2025</code>
  <b>Подробнее о подарке:</b> <code>gift DiamondRing-22428</code>

<emoji document_id=5208791630550688494>🧁</emoji> <a href='https://t.me/nft/BunnyMuffin-38724'>Bunny Muffin #38724</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>66655</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>20:18 12.07.2025</code>
  <b>Подробнее о подарке:</b> <code>gift BunnyMuffin-38724</code>

<emoji document_id=5393320781549693514>🐍</emoji> <a href='https://t.me/nft/PetSnake-31511'>Pet Snake #31511</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>279106</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>09:46 06.06.2025</code>
  <b>Подробнее о подарке:</b> <code>gift PetSnake-31511</code>

<emoji document_id=5264996732227317864>🚀</emoji> <a href='https://t.me/nft/StellarRocket-1182'>Stellar Rocket #1182</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>156318</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>20:58 01.09.2025</code>
  <b>Подробнее о подарке:</b> <code>gift StellarRocket-1182</code>

<emoji document_id=5447496734517262441>🐒</emoji> <a href='https://t.me/nft/JollyChimp-5500'>Jolly Chimp #5500</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>132155</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>02:46 02.09.2025</code>
  <b>Подробнее о подарке:</b> <code>gift JollyChimp-5500</code>

<emoji document_id=5217891858797066356>🌙</emoji> <a href='https://t.me/nft/MoonPendant-3013'>Moon Pendant #3013</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>111080</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>02:48 02.09.2025</code>
  <b>Подробнее о подарке:</b> <code>gift MoonPendant-3013</code>

<emoji document_id=5465454576897389164>🌙</emoji> <a href='https://t.me/nft/MoonPendant-28192'>Moon Pendant #28192</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>111080</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>06:31 02.09.2025</code>
  <b>Подробнее о подарке:</b> <code>gift MoonPendant-28192</code>

<emoji document_id=5465308049793120765>🌙</emoji> <a href='https://t.me/nft/MoonPendant-3012'>Moon Pendant #3012</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>111080</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>02:48 02.09.2025</code>
  <b>Подробнее о подарке:</b> <code>gift MoonPendant-3012</code>

<emoji document_id=5210984889960134992>🌙</emoji> <a href='https://t.me/nft/MoonPendant-28223'>Moon Pendant #28223</a>
  <emoji document_id=5794314463200940940>📌</emoji> <b>Не закреплено</b>
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>111080</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>06:32 02.09.2025</code>
  <b>Подробнее о подарке:</b> <code>gift MoonPendant-28223</code>
</blockquote>
<emoji document_id=6032644646587338669>🎁</emoji> <b>Подарки (72) - 12600 <emoji document_id=5951810621887484519>⭐️</emoji>:</b>
<blockquote expandable>[x13] <emoji document_id=5397915559037785261>🧸</emoji> — 195 <emoji document_id=5951810621887484519>⭐️</emoji>

[x7] <emoji document_id=5465263910414195580>💝</emoji> — 105 <emoji document_id=5951810621887484519>⭐️</emoji>

[x2] <emoji document_id=5445284980978621387>🚀</emoji> — 100 <emoji document_id=5951810621887484519>⭐️</emoji>

[x12] <emoji document_id=5256234380468193852>🎁</emoji> — 1800 <emoji document_id=5951810621887484519>⭐️</emoji>

[x4] <emoji document_id=5255734132742324362>🎁</emoji> — 1200 <emoji document_id=5951810621887484519>⭐️</emoji>

[x3] <emoji document_id=5256140105936044145>🎁</emoji> — 1500 <emoji document_id=5951810621887484519>⭐️</emoji>

[x2] <emoji document_id=5256243683367356869>🎁</emoji> — 5000 <emoji document_id=5951810621887484519>⭐️</emoji>

[x5] <emoji document_id=5440911110838425969>🌹</emoji> — 125 <emoji document_id=5951810621887484519>⭐️</emoji>

[x4] <emoji document_id=5424672908939130073>🎁</emoji> — 600 <emoji document_id=5951810621887484519>⭐️</emoji>

[x2] <emoji document_id=5203996991054432397>🎁</emoji> — 50 <emoji document_id=5951810621887484519>⭐️</emoji>

[x2] <emoji document_id=5402100905883488232>💍</emoji> — 200 <emoji document_id=5951810621887484519>⭐️</emoji>

[x2] <emoji document_id=5253730706592394486>🎁</emoji> — 300 <emoji document_id=5951810621887484519>⭐️</emoji>

[x1] <emoji document_id=5253505577291641700>🎁</emoji> — 300 <emoji document_id=5951810621887484519>⭐️</emoji>

[x1] <emoji document_id=5253618204219046524>🎁</emoji> — 100 <emoji document_id=5951810621887484519>⭐️</emoji>

[x2] <emoji document_id=5253982443215547954>🎁</emoji> — 200 <emoji document_id=5951810621887484519>⭐️</emoji>

[x3] <emoji document_id=5199430298357507333>🎁</emoji> — 225 <emoji document_id=5951810621887484519>⭐️</emoji>

[x1] <emoji document_id=5197639967009961348>🎁</emoji> — 150 <emoji document_id=5951810621887484519>⭐️</emoji>

[x2] <emoji document_id=5429354096874253649>🎁</emoji> — 100 <emoji document_id=5951810621887484519>⭐️</emoji>

[x3] <emoji document_id=5427103310672853316>🎁</emoji> — 300 <emoji document_id=5951810621887484519>⭐️</emoji>

[x1] <emoji document_id=5395347834314696158>💐</emoji> — 50 <emoji document_id=5951810621887484519>⭐️</emoji>

</blockquote>"""

parse_mode = herokutl.utils.sanitize_parse_mode(
        "html"
    )
text, entities = parse_mode.parse(textm)

for t in list(smart_split(text, entities)):
  print(t)

