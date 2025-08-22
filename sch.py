__version__ = (1,1,0)
#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███

# Team: 'H:Mods'
# meta developer: @nullmod


from .. import loader, utils
import re
from datetime import datetime, timedelta, timezone


@loader.tds
class SchedulePlus(loader.Module):
    """Планирование периодичных сообщений"""
    strings = {"name": "SchedulePlus",
               "no_args": "<emoji document_id=5019523782004441717>❌</emoji> Неверные аргументы",
               "too_many": "<emoji document_id=5019523782004441717>❌</emoji> Максимальное число отложенных сообщений - 100.",
               "scheduled": "<emoji document_id=5062291541624619917>✈️</emoji> Сообщения будут запланированы"}

    @loader.command()
    async def sch(self, message):
        """Используй .sch <периодичность в секундах> <количество отправок> <текст/содержимое из ответа>

Проф. режим: .sch 15 3 test{x=1;x*2}/{y=0;y+1}
Запланирует три сообщения: test2/1, test4/2, test8/3"""
        args = utils.get_args_raw(message.text).split(' ', 2)
        resp = (await message.get_reply_message()) if len(args) < 3 and message.is_reply else message
        if not resp or not args[0].isdigit() or not args[1].isdigit():
            return await utils.answer(message, self.strings["no_args"])

        interval, count, text = int(args[0]), int(args[1]), args[2] if len(args) > 2 else resp.text
        if count > 100:
            return await utils.answer(message, self.strings["too_many"])

        chat_id = message.chat_id
        reply_message_id = message.reply_to.reply_to_msg_id if len(args) == 3 else None
        await utils.answer(message, self.strings["scheduled"])

        variables = {}

        for i in range(count):
            send_time = datetime.now(timezone.utc) + timedelta(seconds=interval * i)
            formatted_text = self.process_text(text, variables)
            await self.client.send_message(chat_id, formatted_text, file=resp.media, schedule=send_time, reply_to=reply_message_id)

    def process_text(self, text, variables):
        """Process text okay?"""
        def replace_match(match):
            return self.eval_expr(match.group(1), variables)
        
        return re.sub(r"\{(.*?)\}", replace_match, text)

    def eval_expr(self, expr, variables):
        """eval()"""
        parts = expr.split(";")
        last_value = None
        var_name = None
        for part in parts:
            part = part.strip()
            if "=" in part and part.count("=") == 1:
                var, value = part.split("=")
                var = var.strip()
                if var not in variables:
                    variables[var] = eval(value, {"__builtins__": {}}, variables)
                last_value = variables[var]
                var_name = var
            else:
                last_value = eval(part, {"__builtins__": {}}, variables)

                if var_name is not None:
                    variables[var_name] = last_value
        return str(last_value)
