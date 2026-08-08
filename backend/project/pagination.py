from rest_framework.pagination import PageNumberPagination


class StandardResultsPagination(PageNumberPagination):
    """Bounds every list endpoint so no response can dump an unbounded table.

    page_size defaults to 100 -- comfortably above the current catalog/order
    volumes so nothing is silently truncated today -- and clients may request a
    different size via ?page_size= up to max_page_size. Responses become the
    standard {count, next, previous, results} envelope; the frontend already
    unwraps that shape (see lib/api.ts unwrapList / lib/backend.ts).
    """

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 200
