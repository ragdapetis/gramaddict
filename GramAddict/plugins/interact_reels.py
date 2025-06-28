from GramAddict.core.plugin_loader import Plugin
from GramAddict.core.views import TabBarView, MediaType, LikeMode
from GramAddict.core.utils import random_sleep
from colorama import Style
import logging

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
        ]

    def run(self, device, configs, storage, sessions, profile_filter, plugin):
        logger.info("Interact with Reels mode started", extra={"color": f"{Style.BRIGHT}"})
        tab_bar = TabBarView(device)
        tab_bar.navigateToReels()
        random_sleep(2, 3)
        # Scroll and interact with reels
        for _ in range(20):  # Limit to 20 reels for demo
            media, content_desc = self._get_media_container(device)
            if content_desc and "Reel" in content_desc:
                logger.info("Found a Reel. Commenting...")
                self._comment_on_reel(device)
            else:
                logger.info("Not a Reel. Skipping...")
            device.swipe_points(device.get_info()["displayWidth"] // 2, device.get_info()["displayHeight"] * 3 // 4, device.get_info()["displayWidth"] // 2, device.get_info()["displayHeight"] // 4)
            random_sleep(1, 2)

    def _get_media_container(self, device):
        from GramAddict.core.views import PostsViewList
        media = device.find(resourceIdMatches=device.ResourceID.CAROUSEL_AND_MEDIA_GROUP)
        content_desc = media.get_desc() if media.exists() else None
        return media, content_desc

    def _comment_on_reel(self, device):
        try:
            comment_button = device.find(resourceIdMatches=device.ResourceID.ROW_FEED_BUTTON_COMMENT)
            if comment_button.exists():
                comment_button.click()
                random_sleep(1, 2)
                comment_box = device.find(resourceIdMatches=device.ResourceID.COMMENT_TEXT_INPUT)
                if comment_box.exists():
                    comment_box.set_text("🔥 Nice reel!")
                    post_button = device.find(resourceIdMatches=device.ResourceID.COMMENT_POST_BUTTON)
                    if post_button.exists():
                        post_button.click()
                        logger.info("Commented on reel.")
                    else:
                        logger.warning("Post button not found.")
                else:
                    logger.warning("Comment box not found.")
            else:
                logger.warning("Comment button not found.")
        except Exception as e:
            logger.error(f"Failed to comment on reel: {e}")
