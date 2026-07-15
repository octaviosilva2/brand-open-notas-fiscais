import pytest
from pydantic import ValidationError

from app.core.pagination.schemas import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)


class TestPaginationParams:
    def test_default_page_is_1(self):
        params = PaginationParams()

        assert params.page == 1

    def test_default_page_size_is_10(self):
        params = PaginationParams()

        assert params.page_size == 10

    def test_offset_first_page_is_zero(self):
        params = PaginationParams(page=1, page_size=10)

        assert params.offset == 0

    def test_offset_second_page(self):
        params = PaginationParams(page=2, page_size=10)

        assert params.offset == 10

    def test_offset_formula(self):
        params = PaginationParams(page=3, page_size=20)

        assert params.offset == 40

    def test_offset_large_page(self):
        params = PaginationParams(page=10, page_size=5)

        assert params.offset == 45

    def test_rejects_page_less_than_1(self):
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

    def test_rejects_page_size_less_than_1(self):
        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)

    def test_rejects_page_size_greater_than_100(self):
        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)

    def test_accepts_page_size_of_100(self):
        params = PaginationParams(page_size=100)

        assert params.page_size == 100

    def test_accepts_page_size_of_1(self):
        params = PaginationParams(page_size=1)

        assert params.page_size == 1


class TestPaginatedResponse:
    def test_total_pages_zero_when_no_items(self):
        response = PaginatedResponse[str](data=[], total=0, page=1, page_size=10)

        assert response.total_pages == 0

    def test_total_pages_one_when_items_fit_one_page(self):
        response = PaginatedResponse[str](data=[], total=10, page=1, page_size=10)

        assert response.total_pages == 1

    def test_total_pages_rounds_up_when_not_divisible(self):
        response = PaginatedResponse[str](data=[], total=11, page=1, page_size=10)

        assert response.total_pages == 2

    def test_total_pages_exact_division(self):
        response = PaginatedResponse[str](data=[], total=20, page=1, page_size=10)

        assert response.total_pages == 2

    def test_total_pages_one_item(self):
        response = PaginatedResponse[str](data=[], total=1, page=1, page_size=10)

        assert response.total_pages == 1

    def test_data_holds_items(self):
        items = ["x", "y", "z"]
        response = PaginatedResponse[str](data=items, total=3, page=1, page_size=10)

        assert response.data == items

    def test_rejects_negative_total(self):
        with pytest.raises(ValidationError):
            PaginatedResponse[str](data=[], total=-1, page=1, page_size=10)

    def test_rejects_page_less_than_1(self):
        with pytest.raises(ValidationError):
            PaginatedResponse[str](data=[], total=0, page=0, page_size=10)

    def test_rejects_page_size_less_than_1(self):
        with pytest.raises(ValidationError):
            PaginatedResponse[str](data=[], total=0, page=1, page_size=0)

    def test_accepts_total_zero(self):
        response = PaginatedResponse[str](data=[], total=0, page=1, page_size=10)

        assert response.total == 0


class TestBuildPaginatedResponse:
    def test_returns_paginated_response(self):
        result = build_paginated_response(items=[], total=0, page=1, page_size=10)

        assert isinstance(result, PaginatedResponse)

    def test_data_matches_items(self):
        items = ["a", "b", "c"]
        result = build_paginated_response(items=items, total=3, page=1, page_size=10)

        assert result.data == items

    def test_converts_sequence_to_list(self):
        result = build_paginated_response(
            items=("a", "b"), total=2, page=1, page_size=10
        )

        assert isinstance(result.data, list)

    def test_total_from_argument(self):
        result = build_paginated_response(items=[], total=99, page=1, page_size=10)

        assert result.total == 99

    def test_page_from_argument(self):
        result = build_paginated_response(items=[], total=0, page=5, page_size=10)

        assert result.page == 5

    def test_page_size_from_argument(self):
        result = build_paginated_response(items=[], total=0, page=1, page_size=25)

        assert result.page_size == 25

    def test_works_with_empty_items(self):
        result = build_paginated_response(items=[], total=0, page=1, page_size=10)

        assert result.data == []
        assert result.total_pages == 0

    def test_total_pages_is_computed(self):
        result = build_paginated_response(items=[], total=15, page=1, page_size=10)

        assert result.total_pages == 2
