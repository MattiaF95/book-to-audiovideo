import anyio
import httpx

from book_to_audiovideo.web.app import create_app


async def _post_empty_file() -> httpx.Response:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(
            "/api/jobs",
            files={"file": ("vuoto.txt", b"", "text/plain")},
        )


def test_create_job_rejects_empty_upload() -> None:
    response = anyio.run(_post_empty_file)
    assert response.status_code == 400
    assert response.json()["detail"] == "File vuoto"
