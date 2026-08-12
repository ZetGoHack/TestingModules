# meta developer: local
# packages: ffmpeg

__version__ = (1, 0, 0)

import asyncio
import logging
import os
import random
import shutil
import time

from telethon import functions, errors
from telethon.tl.types import DocumentAttributeVideo

from .. import loader, utils

logger = logging.getLogger(__name__)

DATA_DIR = "avatarframes_data"


@loader.tds
class AvatarFrames(loader.Module):
    """Ставит на аватарку кадры видео по очереди, с конца к началу"""

    strings = {
        "name": "AvatarFrames",
        "noreply": "❌ Ответьте командой на видео (документ)",
        "notvideo": "❌ В ответном сообщении нет видео",
        "already_running": "❌ Загрузка кадров уже запущена. Используйте <code>.avaframesstop</code>, чтобы остановить",
        "not_running": "❌ Сейчас ничего не загружается",
        "downloading": "⏬ Скачиваю видео...",
        "extracting": "🎞 Разбираю видео на кадры...",
        "ffmpeg_error": "❌ Не удалось разобрать видео на кадры (ошибка ffmpeg). Подробности в логах",
        "no_frames": "❌ Не удалось получить ни одного кадра из видео",
        "started": "▶️ Начинаю установку {} кадров на аватарку (с последнего к первому)",
        "resuming": "▶️ Продолжаю установку кадров с сохранённого места...",
        "need_confirm": "⚠️ Юзербот перезапустился во время установки кадров на аватарку ({}/{} уже установлено).\nИнлайн-форма со статусом после перезапуска не работает, поэтому отправьте <code>.avaframes</code> в этом чате (без ответа на видео), чтобы подтвердить и продолжить с сохранённого места",
        "stopped": "⏹ Загрузка кадров остановлена ({}/{} уже установлено). Прогресс сохранён, продолжить можно командой <code>.avaframes</code> (без ответа на видео)",
        "status": "📊 Загружено {}/{} кадров",
        "progress": "📊 Загружено {}/{} кадров",
        "floodwait": "⏳ Поймал FloodWait на {2} сек. (уже установлено {0}/{1} кадров). Продолжу примерно в {3}",
        "done": "✅ Готово! Установлено {} кадров",
    }

    strings_ru = {
        "_cls_doc": "Ставит на аватарку кадры видео по очереди, с конца к началу",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "delay",
                2.0,
                "Задержка между загрузкой кадров (в секундах)",
                validator=loader.validators.Float(minimum=0),
            ),
            loader.ConfigValue(
                "flood_extra_wait",
                10,
                "Доп. время ожидания сверх FloodWait (в секундах), чтобы не словить его снова",
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "max_retries",
                5,
                "Сколько раз пытаться загрузить один кадр перед тем, как пропустить его",
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "status_update_every",
                5,
                "Обновлять сообщение о прогрессе раз в N установленных кадров (реже - меньше редактирований)",
                validator=loader.validators.Integer(minimum=1),
            ),
        )
        self._task = None

    async def client_ready(self):
        if not self.get("running", False):
            return

        # Инлайн-формы выгружаются при перезапуске юзербота, поэтому старое
        # статусное сообщение больше не отвечает на правки. Не запускаем
        # загрузку молча в фоне - вместо этого просим подтвердить продолжение
        # командой, чтобы можно было создать новую инлайн-форму
        total_frames = self.get("total_frames", 0)
        last_frame = self.get("last_frame")
        done = (total_frames - last_frame + 1) if last_frame else 0

        logger.info(
            "Обнаружена незавершённая загрузка кадров (%d/%d), жду подтверждения командой .avaframes",
            done, total_frames,
        )

        chat_id = self.get("chat_id")
        if chat_id is not None:
            try:
                await self.client.send_message(chat_id, self.strings["need_confirm"].format(done, total_frames))
            except Exception as e:
                logger.warning("Не удалось отправить уведомление о незавершённой загрузке: %s", e)

    async def on_unload(self):
        if self._task and not self._task.done():
            self._task.cancel()

    def _reset_state(self):
        self.set("running", False)
        self.set("video_path", None)
        self.set("frames_dir", None)
        self.set("total_frames", None)
        self.set("last_frame", None)
        self.set("chat_id", None)

    @loader.command(ru_doc="[ответ на видео] Начинает установку кадров видео на аватарку. Без ответа на видео - подтверждает продолжение после перезапуска юзербота")
    async def avaframes(self, message):
        """[reply to video] Start setting video frames as avatar. Without a reply - confirm resuming after a userbot restart"""
        if self.get("running", False):
            if self._task and not self._task.done():
                await utils.answer(message, self.strings["already_running"])
                return

            # Задача была прервана перезапуском юзербота (инлайн-форма со
            # статусом уже выгружена) - эта команда подтверждает продолжение
            frames_dir = self.get("frames_dir")
            if frames_dir and os.path.isdir(frames_dir):
                self.set("chat_id", message.chat_id)
                status = await self.inline.form(self.strings["resuming"], message)
                logger.info("Продолжаю установку кадров после подтверждения командой")
                self._task = asyncio.ensure_future(self._upload_loop(status))
                return

            logger.warning("Папка с кадрами не найдена, сбрасываю сохранённый прогресс")
            self._reset_state()

        reply = await message.get_reply_message()
        if not reply or not reply.document:
            await utils.answer(message, self.strings["noreply"])
            return

        is_video = bool(reply.document.mime_type and reply.document.mime_type.startswith("video/"))
        if not is_video:
            is_video = any(
                isinstance(attr, DocumentAttributeVideo)
                for attr in reply.document.attributes
            )

        if not is_video:
            await utils.answer(message, self.strings["notvideo"])
            return

        # Инлайн-форма вместо обычного сообщения: правки такого сообщения не
        # засоряют историю правок сообщения так, как это делают обычные
        # отредактированные сообщения при частых обновлениях прогресса
        status = await self.inline.form(self.strings["downloading"], message)

        data_dir = os.path.join(DATA_DIR, str(message.chat_id), str(reply.id))
        frames_dir = os.path.join(data_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        video_path = os.path.join(data_dir, "source.mp4")

        await reply.download_media(file=video_path)

        await utils.answer(status, self.strings["extracting"])

        total_frames = await self._extract_frames(video_path, frames_dir)
        if total_frames is None:
            await utils.answer(status, self.strings["ffmpeg_error"])
            return

        if total_frames == 0:
            await utils.answer(status, self.strings["no_frames"])
            return

        self.set("video_path", video_path)
        self.set("frames_dir", frames_dir)
        self.set("total_frames", total_frames)
        self.set("last_frame", None)
        self.set("chat_id", message.chat_id)
        self.set("running", True)

        logger.info("Начинаю установку %d кадров на аватарку (от последнего к первому)", total_frames)
        await utils.answer(status, self.strings["started"].format(total_frames))

        self._task = asyncio.ensure_future(self._upload_loop(status))

    @loader.command(ru_doc="Останавливает установку кадров на аватарку")
    async def avaframesstop(self, message):
        """Stop setting video frames as avatar"""
        if not self.get("running", False):
            await utils.answer(message, self.strings["not_running"])
            return

        # Флаг "running" НЕ сбрасываем - он означает "есть незавершённая
        # задача", и по нему .avaframes понимает, что нужно резюмировать
        # с сохранённого кадра, а не требовать новый реплай на видео
        if self._task and not self._task.done():
            self._task.cancel()

        total_frames = self.get("total_frames", 0)
        last_frame = self.get("last_frame")
        done = (total_frames - last_frame + 1) if last_frame else 0

        await utils.answer(message, self.strings["stopped"].format(done, total_frames))

    @loader.command(ru_doc="Показывает прогресс установки кадров на аватарку")
    async def avaframesstatus(self, message):
        """Show progress of setting video frames as avatar"""
        if not self.get("running", False):
            await utils.answer(message, self.strings["not_running"])
            return

        total_frames = self.get("total_frames", 0)
        last_frame = self.get("last_frame")
        done = (total_frames - last_frame + 1) if last_frame else 0

        await utils.answer(message, self.strings["status"].format(done, total_frames))

    async def _extract_frames(self, video_path: str, frames_dir: str):
        if shutil.which("ffmpeg") is None:
            logger.error("ffmpeg не найден в системе, установите его для работы модуля")
            return None

        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", video_path, "-qscale:v", "2",
            os.path.join(frames_dir, "frame_%06d.jpg"),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.error("ffmpeg завершился с ошибкой: %s", stderr.decode(errors="ignore"))
            return None

        return len([f for f in os.listdir(frames_dir) if f.startswith("frame_")])

    async def _upload_loop(self, status=None):
        frames_dir = self.get("frames_dir")
        total_frames = self.get("total_frames", 0)
        chat_id = self.get("chat_id")
        last_frame = self.get("last_frame")
        update_every = self.config["status_update_every"]

        # last_frame - номер последнего успешно загруженного кадра.
        # Продолжаем со следующего (более раннего) кадра, а не с начала
        start_idx = (last_frame - 1) if last_frame else total_frames

        for idx in range(start_idx, 0, -1):
            if not self.get("running", False):
                logger.info(
                    "Загрузка кадров остановлена пользователем на кадре %d/%d",
                    total_frames - idx, total_frames,
                )
                return

            frame_path = os.path.join(frames_dir, f"frame_{idx:06d}.jpg")
            if not os.path.isfile(frame_path):
                logger.warning("Кадр №%d не найден по пути %s, пропускаю", idx, frame_path)
                continue

            if not await self._upload_frame(frame_path, idx, total_frames, status):
                continue

            self.set("last_frame", idx)
            done = total_frames - idx + 1
            logger.info("Загружено %d/%d кадров (кадр №%d установлен на аватарку)", done, total_frames, idx)

            if status is not None and (done % update_every == 0 or idx == 1):
                try:
                    await utils.answer(status, self.strings["progress"].format(done, total_frames))
                except Exception as e:
                    logger.warning("Не удалось обновить сообщение о прогрессе: %s", e)

            await asyncio.sleep(self.config["delay"])

        await self._finish(chat_id, total_frames)

    async def _upload_frame(self, frame_path: str, idx: int, total_frames: int, status=None) -> bool:
        attempt = 0
        while attempt < self.config["max_retries"]:
            try:
                uploaded = await self.client.upload_file(frame_path)
                await self.client(functions.photos.UploadProfilePhotoRequest(file=uploaded))
                return True
            except errors.FloodWaitError as e:
                wait_time = e.seconds + random.randint(0, self.config["flood_extra_wait"])
                done = total_frames - idx
                resume_at = time.strftime("%H:%M:%S", time.localtime(time.time() + wait_time))

                logger.warning(
                    "FloodWait на %d сек. при загрузке кадра №%d (загружено %d/%d), жду %d сек. (продолжу в %s)",
                    e.seconds, idx, done, total_frames, wait_time, resume_at,
                )

                if status is not None:
                    try:
                        await utils.answer(
                            status,
                            self.strings["floodwait"].format(done, total_frames, wait_time, resume_at),
                        )
                    except Exception as ex:
                        logger.warning("Не удалось обновить сообщение о FloodWait: %s", ex)

                await asyncio.sleep(wait_time)

                if status is not None:
                    try:
                        await utils.answer(status, self.strings["progress"].format(done, total_frames))
                    except Exception as ex:
                        logger.warning("Не удалось обновить сообщение после FloodWait: %s", ex)
            except Exception as e:
                attempt += 1
                logger.error(
                    "Ошибка загрузки кадра №%d (попытка %d/%d): %s",
                    idx, attempt, self.config["max_retries"], e,
                )
                await asyncio.sleep(5)

        logger.error("Кадр №%d пропущен после %d неудачных попыток", idx, self.config["max_retries"])
        return False

    async def _finish(self, chat_id, total_frames):
        self.set("running", False)
        self.set("last_frame", None)

        logger.info("Установка всех %d кадров на аватарку завершена", total_frames)

        try:
            if chat_id is not None:
                await self.client.send_message(chat_id, self.strings["done"].format(total_frames))
        except Exception as e:
            logger.warning("Не удалось отправить итоговое сообщение: %s", e)

        frames_dir = self.get("frames_dir")
        video_path = self.get("video_path")
        try:
            if frames_dir and os.path.isdir(frames_dir):
                shutil.rmtree(frames_dir)
            if video_path and os.path.isfile(video_path):
                os.remove(video_path)
        except Exception as e:
            logger.warning("Ошибка при очистке временных файлов: %s", e)
