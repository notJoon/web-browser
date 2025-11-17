import socket
import ssl
import urllib.parse

CLRF = "\r\n"


class URL:
    def __init__(self, url):
        # data 스킴은 : 뒤에 //가 없음
        if url.startswith("data:"):
            self.scheme = "data"
            self.data = url[5:]  # "data:" 이후의 내용
        else:
            self.scheme, url = url.split("://", 1)
            assert self.scheme in ("http", "https", "file", "data")

        if self.scheme == "file":
            # file:// 스킴의 경우 경로만 저장
            self.path = url
        elif self.scheme == "data":
            # data 스킴은 이미 처리됨
            pass
        else:
            # http/https 스킴 처리
            if self.scheme == "http":
                self.port = 80
            elif self.scheme == "https":
                self.port = 443

            # 호스트와 경로 분리
            # 첫 번째 슬래시("/")를 기준으로 앞은 호스트, 뒤는 경로
            if "/" not in url:
                url = url + "/"
            self.host, url = url.split("/", 1)
            self.path = "/" + url

            # 호스트에 포트 번호가 명시된 경우 처리
            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)

    def request(self):
        if self.scheme == "data":
            # data URL 처리
            # 형식: data:[<mediatype>][;base64],<data>
            # 참고: https://datatracker.ietf.org/doc/html/rfc2397#section-2
            if "," in self.data:
                header, content = self.data.split(",", 1)
                # URL 디코딩
                content = urllib.parse.unquote(content)
                return content
            else:
                # 콤마가 없으면 전체를 컨텐츠로 간주
                return urllib.parse.unquote(self.data)
        elif self.scheme == "file":
            # 로컬 파일 읽기
            try:
                with open(self.path, encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                return (
                    f"<html><body><h1>404 Not Found</h1>"
                    f"<p>File not found: {self.path}</p></body></html>"
                )
            except Exception as e:
                return (
                    f"<html><body><h1>Error</h1>"
                    f"<p>Error reading file: {str(e)}</p></body></html>"
                )

        # HTTP/HTTPS 요청 처리
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,  # 임의의 양의 데이터를 전송
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # HTTP/1.1 요청 생성
        request = f"GET {self.path} HTTP/1.1\r\n"

        # 헤더를 딕셔너리로 관리하여 쉽게 추가 가능
        headers = {
            "Host": self.host,
            "Connection": "close",
            "User-Agent": "SimpleWebBrowser/1.0",
        }

        # 헤더 추가
        for header, value in headers.items():
            request += f"{header}: {value}\r\n"

        request += "\r\n"
        s.send(request.encode("utf-8"))

        response = s.makefile("r", encoding="utf-8", newline=CLRF)

        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline()
            if line == CLRF:
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        body = response.read()
        s.close()

        return body


def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")


def load(url):
    body = url.request()
    show(body)


if __name__ == "__main__":
    import os
    import sys

    if len(sys.argv) > 1:
        # URL이 제공된 경우
        load(URL(sys.argv[1]))
    else:
        # URL이 없는 경우 기본 파일 열기
        default_file = os.path.join(os.path.dirname(__file__), "default.html")
        load(URL("file://" + default_file))
