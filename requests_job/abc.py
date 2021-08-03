from pydantic import BaseModel as BaseModelBase


class BaseModel(BaseModelBase):
    def dict(
        self,
        *,
        include: set = None,
        exclude: set = None,
        by_alias: bool = True,  # modify False to True
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ):
        return super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
