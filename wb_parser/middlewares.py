import time
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """Wait and retry when WB returns 429."""

    WAIT_TIMES = [5, 10, 20, 30, 60]

    def process_response(self, request, response, spider):
        if response.status == 429:
            retry_count = request.meta.get("retry_429_count", 0)

            if retry_count < len(self.WAIT_TIMES):
                wait = self.WAIT_TIMES[retry_count]
                logger.warning(
                    f"429 for {request.url[:80]}... waiting {wait}s "
                    f"(attempt {retry_count + 1}/{len(self.WAIT_TIMES)})"
                )
                time.sleep(wait)

                new_request = request.copy()
                new_request.meta["retry_429_count"] = retry_count + 1
                new_request.dont_filter = True
                return new_request

            logger.error(f"429 retry limit reached for {request.url[:80]}")

        return response
