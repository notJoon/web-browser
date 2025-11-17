import socket, ssl

CLRF = "\r\n"

class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ("http", "https")
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        # 호스트와 경로 분리
        # 첫 번째 슬래시("/")를 기준으로 앞의 문자열은 호스트, 뒤의 문자열은 경로로 간주
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        # 호스트에 포트 번호가 명시된 경우 처리
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM, # 임의의 양의 데이터를 전송
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # HTTP/1.1 요청 생성
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        
        # 헤더를 딕셔너리로 관리하여 쉽게 추가 가능
        headers = {
            "Host": self.host,
            "Connection": "close",
            "User-Agent": "SimpleWebBrowser/1.0"
        }
        
        # 헤더 추가
        for header, value in headers.items():
            request += "{}: {}\r\n".format(header, value)
        
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
    import sys
    load(URL(sys.argv[1]))
