import pytest

from services.cs_attestation_probe import probe


class FakeSocket:
    def __init__(self, *chunks: bytes):
        self.chunks = list(chunks)

    def recv(self, size: int) -> bytes:
        del size
        return self.chunks.pop(0) if self.chunks else b""


def response(headers: str, body: bytes = b"") -> bytes:
    return (
        b"HTTP/1.1 200 OK\r\n"
        + headers.encode("ascii")
        + b"\r\n\r\n"
        + body
    )


def read_response(raw: bytes, *splits: int) -> bytes:
    chunks = []
    start = 0
    for end in splits:
        chunks.append(raw[start:end])
        start = end
    chunks.append(raw[start:])
    return probe._read_response(FakeSocket(*chunks))


def test_read_response_accepts_content_length_and_split_reads() -> None:
    body = b'{"token":"jwt"}'
    raw = response(
        "Content-Type: application/json\r\nContent-Length: " + str(len(body)),
        body,
    )

    assert read_response(raw, 7, 42, len(raw) - 3) == body


def test_read_response_accepts_chunked_body_with_extensions_and_trailers() -> None:
    raw = response(
        "Content-Type: application/json\r\nTransfer-Encoding: chunked",
        b"4;part=one\r\nWiki\r\n5\r\npedia\r\n0\r\nX-Launcher: local\r\n\r\n",
    )

    assert read_response(raw) == b"Wikipedia"


def test_read_response_accepts_chunk_boundaries_split_across_reads() -> None:
    raw = response(
        "Content-Type: application/jwt\r\nTransfer-Encoding: Chunked",
        b"3\r\nabc\r\n3\r\ndef\r\n0\r\n\r\n",
    )

    assert read_response(raw, 91, 94, 97, 100, 103, 106, 109) == b"abcdef"


@pytest.mark.parametrize(
    ("chunked_body", "message"),
    [
        (b"not-hex\r\nbody\r\n0\r\n\r\n", "chunk size is invalid"),
        (b"3;=broken\r\nabc\r\n0\r\n\r\n", "chunk extensions are invalid"),
        (b"3\r\nabcX\r\n0\r\n\r\n", "data terminator is invalid"),
        (b"0\r\nMalformed-Trailer\r\n\r\n", "headers are invalid"),
    ],
)
def test_read_response_rejects_malformed_chunked_framing(chunked_body: bytes, message: str) -> None:
    raw = response(
        "Content-Type: application/json\r\nTransfer-Encoding: chunked",
        chunked_body,
    )

    with pytest.raises(RuntimeError, match=message) as error:
        read_response(raw)
    assert b"body" not in str(error.value).encode()


def test_read_response_rejects_chunked_body_overflow_without_reading_token() -> None:
    raw = response(
        "Content-Type: application/json\r\nTransfer-Encoding: chunked",
        b"10001\r\n",
    )

    with pytest.raises(RuntimeError, match="too large"):
        read_response(raw)


def test_read_response_rejects_content_length_overflow() -> None:
    raw = response(
        "Content-Type: application/json\r\nContent-Length: 65537",
    )

    with pytest.raises(RuntimeError, match="too large"):
        read_response(raw)


def test_read_response_rejects_trailing_data_for_both_framings() -> None:
    content_length = response(
        "Content-Type: application/json\r\nContent-Length: 2",
        b"{}extra",
    )
    chunked = response(
        "Content-Type: application/json\r\nTransfer-Encoding: chunked",
        b"2\r\n{}\r\n0\r\n\r\nextra",
    )

    for raw in (content_length, chunked):
        with pytest.raises(RuntimeError, match="trailing data"):
            read_response(raw)


@pytest.mark.parametrize(
    ("headers", "body"),
    [
        (
            "Content-Type: application/json\r\nContent-Length: 2",
            b"{}",
        ),
        (
            "Content-Type: application/json\r\nTransfer-Encoding: chunked",
            b"2\r\n{}\r\n0\r\n\r\n",
        ),
    ],
)
def test_read_response_rejects_trailing_data_from_later_recv(headers: str, body: bytes) -> None:
    framed = response(headers, body)

    with pytest.raises(RuntimeError, match="trailing data"):
        probe._read_response(FakeSocket(framed, b"extra"))


def test_read_response_rejects_ambiguous_framing() -> None:
    raw = response(
        "Content-Type: application/json\r\n"
        "Transfer-Encoding: chunked\r\nContent-Length: 2",
        b"2\r\n{}\r\n0\r\n\r\n",
    )

    with pytest.raises(RuntimeError, match="transfer_encoding"):
        read_response(raw)


def test_read_response_preserves_status_and_content_type_checks() -> None:
    wrong_status = response("Content-Type: application/json\r\nContent-Length: 2", b"{}")
    wrong_status = wrong_status.replace(b"200 OK", b"403 Forbidden", 1)
    wrong_type = response("Content-Type: text/plain\r\nContent-Length: 2", b"{}")

    with pytest.raises(RuntimeError, match="launcher_response_status_403"):
        read_response(wrong_status)
    with pytest.raises(RuntimeError, match="launcher_header_content_type_text_plain"):
        read_response(wrong_type)



def test_read_response_counts_only_header_bytes_against_header_limit() -> None:
    prefix = (
        b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
        b"Content-Length: 2\r\nX-Padding: "
    )
    padding = b"x" * (probe.MAX_RESPONSE_HEADERS_BYTES - len(prefix) - 4)
    raw = prefix + padding + b"\r\n\r\n{}"

    assert read_response(raw) == b"{}"
