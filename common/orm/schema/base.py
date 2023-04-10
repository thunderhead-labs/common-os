from sqlalchemy.inspection import inspect


class Base:
    def __to_dict__(self):
        return {
            column.key: getattr(self, column.key)
            for column in inspect(self).mapper.column_attrs
        }
