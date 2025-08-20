from GramAddict.core.plugin_loader import Plugin
from GramAddict.core.views import TabBarView
from GramAddict.core.utils import random_sleep
from GramAddict.core.decorators import run_safely
from GramAddict.core.resources import ResourceID as resources
from colorama import Style
import logging
from random import randint, choice
import datetime
import sqlite3

logger = logging.getLogger(__name__)

class PostStatus(Plugin):
    """Post status (story) from user's own posts."""

    def __init__(self):
        super().__init__()
        self.description = "Post status (story) from user's own posts with daily limits."
        self.arguments = [
            {
                "arg": "--post-status",
                "nargs": None,
                "help": "post status from your own posts",
                "metavar": None,
                "default": None,
                "operation": True,
            },
            {
                "arg": "--status-per-day",
                "nargs": None,
                "help": "maximum number of status posts per day (default: 3)",
                "metavar": None,
                "default": 3,
                "operation": False,
            }
        ]
        self.status_posted_today = 0
        self._db_path = "status_count.db"
        self._ensure_db()

    def _ensure_db(self):
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS status_count (
                date TEXT PRIMARY KEY,
                count INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def run(self, device, configs, storage, sessions, profile_filter, plugin):
        self.args = configs.args
        self.device_id = configs.args.device
        self.session_state = sessions[-1]
        self.sessions = sessions
        self.storage = storage
        self.ResourceID = resources(self.args.app_id)
        
        max_status_per_day = int(getattr(self.args, "status_per_day", 3) or 3)
        
        info = device.get_info()
        center_x = info["displayWidth"] // 2
        center_y = info["displayHeight"] // 2
        
        @run_safely(
            device=device,
            device_id=self.device_id,
            sessions=self.sessions,
            session_state=self.session_state,
            screen_record=self.args.screen_record,
            configs=configs,
        )
        def job():
            """Main job function to post status."""
            if self._check_daily_limit(max_status_per_day):
                logger.info("Daily status limit reached. Stopping.", extra={"color": f"{Style.BRIGHT}"})
                return

            logger.info("Post Status mode started", extra={"color": f"{Style.BRIGHT}"})
            
            # Navigate to profile
            tab_bar = TabBarView(device)
            tab_bar.navigateToProfile()
            random_sleep(2, 3)
            
            # Click on the on random 1 of top 6 posts
            first_post = device.find(descriptionMatches=f"^Reel by (.+?) at row {randint(1,2)}, column {randint(1,3)}$")
            if not first_post.exists():
                logger.error("No posts found in profile")
                return
            
            first_post.click()

            random_sleep(2, 3)

            # Swipe down to ensure the share/send button is visible
            self._swipe_down(device, center_x, center_y, center_y // 4)

            # Try to find the share/send button (resourceId or text fallback)
            share_button = device.find(resourceId=f"{self.args.app_id}/row_feed_button_share")
            if not share_button.exists():
                share_button = device.find(descriptionMatches="Send Post|Send post")
            if not share_button.exists():
                logger.error("Could not find share/send button")
                return
            share_button.click()
            random_sleep(3, 4)
            
            
            # Click "Add to Story"
            # Try to find the share/send button (resourceId or text fallback)
            add_to_story = device.find(descriptionMatches="Add to story")
            if not add_to_story.exists():
                add_to_story = device.find(textMatches="Add to story")
            if not add_to_story.exists():
                logger.error("Could not find Add to Story button")
                return
            add_to_story.click()
            random_sleep(3, 4)
        

            # Try to find the share/send button (resourceId or text fallback)
            add_to_story = device.find(descriptionMatches="Your story|Add to story|Share to story")
            if not add_to_story.exists():
                add_to_story = device.find(textMatches="Your story|Add to story|Share to story")
            if not add_to_story.exists():
                logger.error("Could not find Your story button")
                return
            add_to_story.click()
            random_sleep(3, 4)

            # Update status count in storage
            self._update_status_count()
            logger.info("Successfully posted status!", extra={"color": f"{Style.BRIGHT}"})

            device.back()
            random_sleep(1, 2)
            
        job()

    def _check_daily_limit(self, max_per_day):
        """Check if we've hit the daily limit for posting status."""
        today = datetime.date.today().isoformat()
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute("SELECT count FROM status_count WHERE date=?", (today,))
        row = c.fetchone()
        count = row[0] if row else 0
        conn.close()
        return count >= max_per_day

    def _update_status_count(self):
        """Update the count of status posted today."""
        today = datetime.date.today().isoformat()
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute("SELECT count FROM status_count WHERE date=?", (today,))
        row = c.fetchone()
        if row:
            c.execute("UPDATE status_count SET count = count + 1 WHERE date=?", (today,))
        else:
            c.execute("INSERT INTO status_count (date, count) VALUES (?, 1)", (today,))
        conn.commit()
        conn.close()

    def _swipe_down(self, device, x, y_from, y_to):
        try:
            device.swipe_points(x, y_from, x, y_to)
        except Exception as e:
            logger.warning(f"Swipe failed: {e}")
            random_sleep(0.8, 1.4)
            try:
                device.swipe_points(x, y_from, x, y_to)
            except Exception as e2:
                logger.error(f"Swipe failed again: {e2}")