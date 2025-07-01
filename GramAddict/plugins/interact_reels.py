from GramAddict.core.plugin_loader import Plugin
from GramAddict.core.views import TabBarView, MediaType, LikeMode
from GramAddict.core.utils import random_sleep
from GramAddict.core.decorators import run_safely
from GramAddict.core.resources import ResourceID as resources
from colorama import Style
import logging
from random import randint, choice

logger = logging.getLogger(__name__)

class InteractReels(Plugin):
    """Interact with Reels by commenting only on Reels."""

    def __init__(self):
        super().__init__()
        self.description = "Interact with Reels by commenting only on Reels."
        self.arguments = [
            {
                "arg": "--reels",
                "nargs": None,
                "help": "interact with reels by commenting",
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
        ]

    def run(self, device, configs, storage, sessions, profile_filter, plugin):
        self.args = configs.args
        self.device_id = configs.args.device
        self.session_state = sessions[-1]
        self.sessions = sessions
        self.unfollow_type = plugin
        self.ResourceID = resources(self.args.app_id)
        reels_count = int(getattr(self.args, 'reels_count', 100)) or 100
        
        @run_safely(
            device=device,
            device_id=self.device_id,
            sessions=self.sessions,
            session_state=self.session_state,
            screen_record=self.args.screen_record,
            configs=configs,
        )
        def job():
            """Main job function to interact with Reels."""
            logger.info("Interact with Reels mode started", extra={"color": f"{Style.BRIGHT}"})
            tab_bar = TabBarView(device)
            tab_bar.navigateToReels()
            random_sleep(2, 3)
            # Scroll and interact with reels
            for i in range(reels_count):
                if i % 10 == 0: #TODO Dosent look good
                    logger.info(f"Refreshing Reels feed...")
                    tab_bar.navigateToReels()

                #media, content_desc = self._get_media_container(device)
                #print(content_desc)
                #self._comment_on_reel(device)
                if not device.find(descriptionMatches="Sponsored").exists():
                    logger.info("Found a Reel.")
                    if randint(1,10) == randint(1,10):
                        self._comment_on_reel(device)
                else:
                    logger.info("Ad. Skipping...")
                device.swipe_points(device.get_info()["displayWidth"] // 2, device.get_info()["displayHeight"] * 3 // 4, device.get_info()["displayWidth"] // 2, device.get_info()["displayHeight"] // 4)
                random_sleep(1, 2)

        job()

    def _get_media_container(self, device):
        from GramAddict.core.views import PostsViewList
        media = device.find(resourceId=self.ResourceID.CAROUSEL_AND_MEDIA_GROUP)
        logger.debug(dir(media))
        logger.debug(f"Media container found: {media}")
        content_desc = media.get_desc() if media.exists() else None
        return media, content_desc

    def _comment_on_reel(self, device):
        try:
            # Horny emoji comments from emojidb.org
            horny_comments = [
                "🥵", "😈", "🤤", "🤭", "🍆👅💦🤤", "🫦", "😏", "😘", "😩", "🥰", "🍆🍑👉👌😩💦", "💋", "💦", "❤️", "🔞🥵🍑👉👌", "😍", "🍑💦👅😋"
            ]
            comment_button = device.find(descriptionMatches="Comment")
            if comment_button.exists():
                comment_button.click()
                random_sleep(1, 2)
                comment_box = device.find(resourceId=self.ResourceID.LAYOUT_COMMENT_THREAD_EDITTEXT)
                if comment_box.exists():
                    comment = choice(horny_comments)
                    comment_box.set_text(comment)
                    post_button = device.find(resourceId=self.ResourceID.LAYOUT_COMMENT_THREAD_POST_BUTTON_CLICK_AREA)
                    if post_button.exists():
                        post_button.click()
                        logger.info("Commented on reel.")
                    else:
                        logger.warning("Post button not found.")
                    device.back()  # Go back to reels
                    device.back()  # Go back to reels
                else:
                    logger.warning("Comment box not found.")
            else:
                logger.warning("Comment button not found.")
        except Exception as e:
            logger.error(f"Failed to comment on reel: {e}")
