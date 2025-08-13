from GramAddict.core.plugin_loader import Plugin
from GramAddict.core.views import TabBarView
from GramAddict.core.utils import random_sleep
from GramAddict.core.decorators import run_safely
from GramAddict.core.resources import ResourceID as resources
from colorama import Style
import logging
from random import randint, choice, random, uniform
import time

logger = logging.getLogger(__name__)

class InteractReels(Plugin):
    """Interact with Reels by liking and/or commenting (stealth + randomized + throttling)."""

    def __init__(self):
        super().__init__()
        self.description = "Interact with Reels by liking and/or commenting."
        self.arguments = [
            {
                "arg": "--reels",
                "nargs": None,
                "help": "interact with reels by commenting/liking",
                "metavar": None,
                "default": None,
                "operation": True,
            },
            {
                "arg": "--reels-count",
                "nargs": None,
                "help": "number of reels to interact with (default: 100)",
                "metavar": None,
                "default": 100,
                "operation": False,
            },
            {
                "arg": "--reels-comment-prob",
                "nargs": None,
                "help": "probability [0..1] to comment on a non-ad reel (default: 0.12)",
                "metavar": None,
                "default": 0.12,
                "operation": False,
            },
            {
                "arg": "--reels-like-prob",
                "nargs": None,
                "help": "probability [0..1] to like a non-ad reel (default: 0.35)",
                "metavar": None,
                "default": 0.35,
                "operation": False,
            },
            {
                "arg": "--reels-min-watch",
                "nargs": None,
                "help": "min seconds to watch each reel (default: 4)",
                "metavar": None,
                "default": 4,
                "operation": False,
            },
            {
                "arg": "--reels-max-watch",
                "nargs": None,
                "help": "max seconds to watch each reel (default: 15)",
                "metavar": None,
                "default": 15,
                "operation": False,
            },
            {
                "arg": "--reels-max-comments",
                "nargs": None,
                "help": "max comments in one run before stopping (default: 20)",
                "metavar": None,
                "default": 20,
                "operation": False,
            },
            {
                "arg": "--reels-max-likes",
                "nargs": None,
                "help": "max likes in one run before stopping (default: 40)",
                "metavar": None,
                "default": 40,
                "operation": False,
            },
        ]

        self._recent_comments = []
        self._comments_done = 0
        self._likes_done = 0
        self._start_time = None

    def run(self, device, configs, storage, sessions, profile_filter, plugin):
        self.args = configs.args
        self.device_id = configs.args.device
        self.session_state = sessions[-1]
        self.sessions = sessions
        self.unfollow_type = plugin
        self.ResourceID = resources(self.args.app_id)

        reels_count = int(getattr(self.args, "reels_count", 100) or 100)
        comment_prob = float(getattr(self.args, "reels_comment_prob", 0.12) or 0.12)
        like_prob = float(getattr(self.args, "reels_like_prob", 0.35) or 0.35)
        min_watch = int(getattr(self.args, "reels_min_watch", 4) or 4)
        max_watch = int(getattr(self.args, "reels_max_watch", 15) or 15)
        max_comments = int(getattr(self.args, "reels_max_comments", 20) or 20)
        max_likes = int(getattr(self.args, "reels_max_likes", 40) or 40)

        if max_watch < min_watch:
            max_watch = min_watch + 1

        info = device.get_info()
        center_x = info["displayWidth"] // 2
        y_up = int(info["displayHeight"] * 0.25)
        y_down = int(info["displayHeight"] * 0.75)

        next_refresh_in = randint(7, 15)
        self._start_time = time.time()

        @run_safely(
            device=device,
            device_id=self.device_id,
            sessions=self.sessions,
            session_state=self.session_state,
            screen_record=self.args.screen_record,
            configs=configs,
        )
        def job():
            logger.info("Interact with Reels mode started", extra={"color": f"{Style.BRIGHT}"})
            tab_bar = TabBarView(device)
            tab_bar.navigateToReels()
            random_sleep(2, 3)

            for i in range(reels_count):
                # Throttling check
                if self._comments_done >= max_comments:
                    logger.info(f"Max comments ({max_comments}) reached. Stopping early.")
                    break
                if self._likes_done >= max_likes:
                    logger.info(f"Max likes ({max_likes}) reached. Stopping early.")
                    break
                if self._too_fast():
                    logger.info("Interaction rate too high — stopping to avoid detection.")
                    break

                nonlocal next_refresh_in
                if i != 0 and next_refresh_in <= 0:
                    logger.info("Refreshing Reels feed…")
                    tab_bar.navigateToReels()
                    random_sleep(1, 2)
                    next_refresh_in = randint(7, 15)

                if self._is_ad(device):
                    logger.info("Ad detected. Skipping…")
                    self._human_watch(min_watch, max_watch)
                    self._swipe_next(device, center_x, y_down, y_up)
                    next_refresh_in -= 1
                    continue

                logger.info("Reel detected.")
                self._human_watch(min_watch, max_watch)
                self._micro_hesitation()

                # Decide actions
                did_like = False
                if random() < like_prob:
                    if self._like_reel(device):
                        self._likes_done += 1
                        did_like = True
                        random_sleep(1.0, 2.5)

                if random() < comment_prob:
                    if self._comment_on_reel(device):
                        self._comments_done += 1
                        random_sleep(2, 4)

                if not did_like and randint(0, 6) == 0:
                    random_sleep(1, 3)

                self._swipe_next(device, center_x, y_down, y_up)
                next_refresh_in -= 1

            logger.info("Interact with Reels mode finished.")

        job()

    # ---------- Throttling Logic ----------

    def _too_fast(self):
        """Return True if interaction rate is too high (suspicious)."""
        elapsed = time.time() - self._start_time
        actions = self._comments_done + self._likes_done
        if actions >= 10 and elapsed < actions * 8:  # avg < 8s per action
            return True
        return False

    # ---------- Helpers ----------

    def _is_ad(self, device):
        patterns = "(Sponsored|Ad|Gesponsert|Publicidad|Sponsorizzato|Sponsorizado|Patrocinado|Реклама|Реклам|إعلان|Annonce|Sponsrad)"
        try:
            if device.find(descriptionMatches=patterns).exists():
                return True
            if device.find(textMatches=patterns).exists():
                return True
        except Exception:
            pass
        return False

    def _human_watch(self, min_watch, max_watch):
        t = uniform(min_watch, max_watch) + uniform(0.0, 1.2)
        random_sleep(t * 0.85, t * 1.15)

    def _micro_hesitation(self):
        if randint(0, 3) == 0:
            random_sleep(0.4, 0.9)

    def _swipe_next(self, device, x, y_from, y_to):
        try:
            device.swipe_points(x, y_from, x, y_to)
        except Exception as e:
            logger.warning(f"Swipe failed: {e}")
            random_sleep(0.8, 1.4)
            try:
                device.swipe_points(x, y_from, x, y_to)
            except Exception as e2:
                logger.error(f"Swipe failed again: {e2}")

    def _get_unique_comment(self):
        comments = [
            "🥵", "😈", "🤤", "🫦", "😏", "😘", "😩", "🥰", "💋", "💦", "❤️", "😍",
            "🔥", "🔥🔥", "Wow 🔥", "So good 😍", "Insane 👏", "Vibes ✨", "Clean 😮‍💨", "Crazy good 🤯"
        ]
        pool = [c for c in comments if c not in self._recent_comments[-6:]] or comments
        cmt = choice(pool)
        self._recent_comments.append(cmt)
        if len(self._recent_comments) > 32:
            self._recent_comments = self._recent_comments[-16:]
        return cmt

    def _safe_back_to_reel(self, device, max_steps=3):
        for _ in range(max_steps):
            device.back()
            random_sleep(0.6, 1.2)
            if device.find(descriptionMatches="Comment").exists():
                return True
        return False

    def _comment_on_reel(self, device):
        try:
            comment_btn = device.find(descriptionMatches="Comment")
            if not comment_btn.exists():
                return False

            comment_btn.click()
            random_sleep(0.8, 1.6)

            comment_box = device.find(resourceId=self.ResourceID.LAYOUT_COMMENT_THREAD_EDITTEXT)
            if not comment_box.exists():
                self._safe_back_to_reel(device)
                return False

            comment = self._get_unique_comment()
            comment_box.set_text(comment)
            random_sleep(0.4, 0.9)

            post_btn = device.find(resourceId=self.ResourceID.LAYOUT_COMMENT_THREAD_POST_BUTTON_CLICK_AREA)
            if not post_btn.exists():
                self._safe_back_to_reel(device)
                return False

            if randint(0, 3) == 0:
                random_sleep(0.6, 1.2)

            post_btn.click()
            logger.info(f"Commented: {comment}")
            random_sleep(1.2, 2.2)
            self._safe_back_to_reel(device)
            return True

        except Exception as e:
            logger.error(f"Failed to comment: {e}")
            self._safe_back_to_reel(device, max_steps=4)
            return False

    def _like_reel(self, device):
        try:
            like_btn = device.find(descriptionMatches="Like")
            if like_btn.exists():
                if randint(0, 1) == 0:
                    like_btn.click()
                    logger.info("Liked reel (button).")
                else:
                    info = device.get_info()
                    device.double_click(info["displayWidth"] // 2, info["displayHeight"] // 2)
                    logger.info("Liked reel (double-tap).")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to like reel: {e}")
            return False

