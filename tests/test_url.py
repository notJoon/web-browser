import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile

from url import URL


class TestURL:
    def test_http_scheme_parsing(self):
        """HTTP URL 파싱 테스트"""
        url = URL("http://example.com/path")
        assert url.scheme == "http"
        assert url.host == "example.com"
        assert url.path == "/path"
        assert url.port == 80

    def test_https_scheme_parsing(self):
        """HTTPS URL 파싱 테스트"""
        url = URL("https://secure.example.com/secure/path")
        assert url.scheme == "https"
        assert url.host == "secure.example.com"
        assert url.path == "/secure/path"
        assert url.port == 443

    def test_file_scheme_parsing(self):
        """File 스킴 URL 파싱 테스트"""
        url = URL("file:///Users/test/document.html")
        assert url.scheme == "file"
        assert url.path == "/Users/test/document.html"

    def test_port_parsing(self):
        """포트 번호가 명시된 URL 파싱 테스트"""
        url = URL("http://example.com:8080/api")
        assert url.host == "example.com"
        assert url.port == 8080
        assert url.path == "/api"


class TestHTTPRequest:
    @patch("socket.socket")
    def test_http11_headers(self, mock_socket):
        """HTTP/1.1 요청과 헤더 테스트"""
        # Mock 설정
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance

        # Mock response 설정
        mock_response = MagicMock()
        mock_response.readline.side_effect = [
            "HTTP/1.1 200 OK\r\n",
            "Content-Type: text/html\r\n",
            "\r\n",
        ]
        mock_response.read.return_value = "<html><body>Test</body></html>"
        mock_sock_instance.makefile.return_value = mock_response

        # 테스트 실행
        url = URL("http://example.com/test")
        url.request()

        # HTTP/1.1 요청 검증
        sent_data = mock_sock_instance.send.call_args[0][0].decode("utf-8")

        # HTTP/1.1 사용 확인
        assert "GET /test HTTP/1.1\r\n" in sent_data

        # 필수 헤더 확인
        assert "Host: example.com\r\n" in sent_data
        assert "Connection: close\r\n" in sent_data
        assert "User-Agent: SimpleWebBrowser/1.0\r\n" in sent_data


class TestFileRequest:
    def test_file_request_success(self):
        """로컬 파일 읽기 성공 테스트"""
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write("<html><body>Test Content</body></html>")
            temp_path = f.name

        try:
            # file:// URL로 파일 읽기
            url = URL(f"file://{temp_path}")
            content = url.request()

            assert "<html><body>Test Content</body></html>" in content
        finally:
            # 임시 파일 삭제
            os.unlink(temp_path)

    def test_file_request_not_found(self):
        """존재하지 않는 파일 처리 테스트"""
        url = URL("file:///nonexistent/path/to/file.html")
        content = url.request()

        assert "404 Not Found" in content
        assert "File not found" in content
        assert "/nonexistent/path/to/file.html" in content

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_file_request_permission_error(self, mock_open):
        """파일 읽기 권한 오류 테스트"""
        url = URL("file:///protected/file.html")
        content = url.request()

        assert "Error" in content
        assert "Error reading file" in content
