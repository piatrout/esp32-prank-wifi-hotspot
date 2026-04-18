import network
import socket
import os
import time

SSID = "FreeWiFi"
AP_IP = "192.168.4.1"

HTML = """\
HTTP/1.1 200 OK\r
Content-Type: text/html\r
\r
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Welcome</title>
  <style>
    body {
      font-family: sans-serif;
      text-align: center;
      padding: 40px 20px;
      background: #111;
      color: #fff;
      margin: 0;
    }
    h1 { margin-bottom: 40px; font-size: 2em; }
    button {
      background: #1db954;
      color: white;
      border: none;
      padding: 18px 48px;
      font-size: 1.3em;
      border-radius: 50px;
      cursor: pointer;
      transition: transform 0.1s, background 0.2s;
    }
    button:active { transform: scale(0.95); }
    button:disabled { background: #555; cursor: default; }
    #status { margin-top: 24px; font-size: 0.95em; color: #aaa; }
    audio { display: none; }
  </style>
</head>
<body>
  <h1>Welcome</h1>
  <button id="btn" onclick="play()">&#9654; Connect</button>
  <p id="status"></p>
  <audio id="player" src="/sound.mp3"></audio>
  <script>
    function play() {
      var btn = document.getElementById('btn');
      var status = document.getElementById('status');
      var audio = document.getElementById('player');
      btn.disabled = true;
      btn.textContent = 'Loading...';
      status.textContent = 'Connecting...';
      audio.load();
      audio.play().then(function() {
        btn.textContent = '\\u25B6 Playing';
        status.textContent = '';
      }).catch(function(e) {
        btn.disabled = false;
        btn.textContent = '\\u25B6 Connect';
        status.textContent = 'Error: ' + e.message;
      });
    }
  </script>
</body>
</html>
"""

REDIRECT = """\
HTTP/1.1 302 Found\r
Location: http://{}/\r
\r
""".format(AP_IP)


def setup_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=SSID, authmode=network.AUTH_OPEN)
    while not ap.active():
        time.sleep(0.1)
    print("AP started:", ap.ifconfig())


def send_file(conn, path, content_type):
    try:
        size = os.stat(path)[6]
        header = "HTTP/1.1 200 OK\r\nContent-Type: {}\r\nContent-Length: {}\r\nAccept-Ranges: bytes\r\nConnection: close\r\n\r\n".format(
            content_type, size
        )
        conn.send(header.encode())
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                conn.send(chunk)
    except Exception as e:
        print("File error:", e)
        conn.send(b"HTTP/1.1 404 Not Found\r\n\r\n")


def run_dns():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setblocking(False)
    udp.bind(("0.0.0.0", 53))
    return udp


def handle_dns(udp):
    try:
        data, addr = udp.recvfrom(512)
        response = data[:2]
        response += b"\x81\x80"
        response += data[4:6]
        response += data[4:6]
        response += b"\x00\x00\x00\x00"
        response += data[12:]
        response += b"\xc0\x0c"
        response += b"\x00\x01"
        response += b"\x00\x01"
        response += b"\x00\x00\x00\x3c"
        response += b"\x00\x04"
        response += bytes(int(x) for x in AP_IP.split("."))
        udp.sendto(response, addr)
    except:
        pass


def run_http():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp.setblocking(False)
    tcp.bind(("0.0.0.0", 80))
    tcp.listen(5)
    return tcp


def handle_http(tcp):
    try:
        conn, addr = tcp.accept()
        conn.settimeout(3)
        try:
            request = conn.recv(1024).decode("utf-8", "ignore")
            print("Request:", request.split("\n")[0])

            if "GET /sound.mp3" in request:
                send_file(conn, "/sound.mp3", "audio/mpeg")
            elif "GET /image.jpg" in request:
                send_file(conn, "/image.jpg", "image/jpeg")
            elif "GET / " in request or "GET /index" in request:
                conn.send(HTML.encode())
            elif "generate_204" in request or "gen_204" in request:
                # Android captive portal detection — ожидает 204, мы редиректим
                conn.send(b"HTTP/1.1 302 Found\r\nLocation: http://" + AP_IP.encode() + b"/\r\n\r\n")
            elif "hotspot-detect" in request or "success.html" in request or "ncsi.txt" in request:
                # iOS и Windows captive portal detection
                conn.send(b"HTTP/1.1 302 Found\r\nLocation: http://" + AP_IP.encode() + b"/\r\n\r\n")
            else:
                conn.send(REDIRECT.encode())
        except Exception as e:
            print("Conn error:", e)
        finally:
            conn.close()
    except:
        pass


setup_ap()
dns = run_dns()
http = run_http()
print("Running captive portal on", AP_IP)

while True:
    handle_dns(dns)
    handle_http(http)
