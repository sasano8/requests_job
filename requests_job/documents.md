# auth
- requests.auth:HTTPBasicAuth
- requests.auth:HTTPDigestAuth
- requests.auth:HTTPProxyAuth

# transport
- httpx:WSGITransport
- httpx:ASGITransport
- httpx:MockTransport
- httpx:HTTPTransport

# cert

# verify
httpx.create_ssl_context(verify="/tmp/client.pem")
httpx.get('https://example.org', verify=context)

# CertificateとVerificationの違い

基本はcertを使う。
verifyはクライアント証明書をサーバに送信して、アクセスを許可してもらう。
クライアント証明書は、CA証明書

- certificationは判断による認証
- verifyは事実による認証