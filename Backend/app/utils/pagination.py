from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
	items: Sequence[T]
	total: int
	page: int
	page_size: int


def paginate_sequence(
	*,
	items: Sequence[T],
	total: int,
	page: int,
	page_size: int,
) -> Page[T]:
	return Page[T](items=items, total=total, page=page, page_size=page_size)
