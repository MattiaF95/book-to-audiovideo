from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


def retryable(attempts: int = 3):
    return retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
