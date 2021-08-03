import httpx


def debug_request(request):
    print(request.__dict__)


def debug_response(response):
    request = response.request
    print(f"[{response.status_code}]: {request.__dict__}")
