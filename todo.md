# lifespan
httpxはasgiのlifespanに未対応。
httpxの範囲外なので対応しないとのこと。

公式では、これ使えば？と書いてある。
https://github.com/florimondmanca/asgi-lifespan#usage


# もし、lifespanが解決できたなら、
複数のasgiアプリケーションを多重起動すると、二重にlifespanイベントが起動することになる。
アプリケーションの実装によっては、二重起動の弊害があるかもしれない。

また、並列で起動すると実行中のジョブが中断されるかもしれないので、直接参照しないで別プロセスで起動しなければならないと思う。