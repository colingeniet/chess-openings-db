from django.db.models import Lookup


class ChessStartsWith(Lookup):
    lookup_name = 'chs_startswith'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params + rhs_params
        sql_code = "%s BETWEEN %s AND (%s::bytea || E'\\\\xff'::bytea)"
        return sql_code % (lhs, rhs, rhs), params


class ChessStartsOf(Lookup):
    lookup_name = 'chs_startof'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = rhs_params + lhs_params + lhs_params
        sql_code = "%s BETWEEN %s AND (%s::bytea || E'\\\\xff'::bytea)"
        return sql_code % (rhs, lhs, lhs), params
