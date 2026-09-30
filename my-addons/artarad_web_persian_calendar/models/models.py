# -*- coding: utf-8 -*-
from odoo import models
from odoo.orm.models import parse_read_group_spec
from odoo.orm.query import TableSQL
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, SQL
from odoo.tools.misc import get_lang

import logging
_logger = logging.getLogger(__name__)

import jdatetime
import pytz

# granularities for which the groupby is computed on the jalaali calendar
JALAALI_GRANULARITY = ('day', 'week', 'month', 'quarter', 'year')


class artaradBase(models.AbstractModel):
    _inherit = 'base'

    def _artarad_is_jalaali(self):
        """ Whether the current user reads dates on the jalaali calendar. """
        try:
            return self.env.user.calendar_type == 'jalaali'
        except Exception:  # noqa: BLE001 - the field may not exist yet while installing
            return False

    def _read_group_groupby(self, table: TableSQL, groupby_spec: str) -> SQL:
        """ Return <SQL expression> corresponding to the given groupby element.

        For jalaali users, date and datetime fields are truncated on the
        jalaali calendar (using the ``g2j`` SQL function) instead of the
        gregorian one.
        """
        if not self._artarad_is_jalaali():
            return super()._read_group_groupby(table, groupby_spec)

        fname, seq_fnames, granularity = parse_read_group_spec(groupby_spec)
        field = self._fields.get(fname)
        if (
            field is None
            or seq_fnames
            or field.type not in ('date', 'datetime')
            or granularity not in JALAALI_GRANULARITY
        ):
            return super()._read_group_groupby(table, groupby_spec)

        table = table._with_model(table._model.with_context(_generating_sql_for_fields=True))
        sql_expr = table[fname]

        tail = ""
        if field.type == 'datetime':
            tail = " 00:00:00"
            if tz := self.env.context.get('tz'):
                if tz in pytz.all_timezones_set:
                    sql_expr = SQL("timezone(%s, timezone('UTC', %s))", tz, sql_expr)
                else:
                    _logger.warning("Grouping in unknown / legacy timezone %r", tz)

        if granularity == 'day':
            sql_expr = SQL("g2j(%s) || %s", sql_expr, tail)
        elif granularity == 'week':
            first_week_day = int(get_lang(self.env).week_start) - 1
            days_offset = first_week_day and 7 - first_week_day
            interval = f'-{days_offset} DAY'
            sql_expr = SQL(
                "g2j((date_trunc('week', %s::timestamp - INTERVAL %s) + INTERVAL %s)) || %s",
                sql_expr, interval, interval, tail,
            )
        elif granularity == 'month':
            sql_expr = SQL("substring(g2j(%s), 0, 8) || '-01' || %s", sql_expr, tail)
        elif granularity == 'quarter':
            sql_expr = SQL("""case
                                when substring(g2j(%s), 6, 2) < '04' then substring(g2j(%s), 0, 5) || '-01-01' || %s
                                when substring(g2j(%s), 6, 2) < '07' then substring(g2j(%s), 0, 5) || '-04-01' || %s
                                when substring(g2j(%s), 6, 2) < '10' then substring(g2j(%s), 0, 5) || '-07-01' || %s
                                when substring(g2j(%s), 6, 2) < '13' then substring(g2j(%s), 0, 5) || '-10-01' || %s
                            end""", *(sql_expr, sql_expr, tail) * 4)
        elif granularity == 'year':
            sql_expr = SQL("substring(g2j(%s), 0, 5) || '-01-01' || %s", sql_expr, tail)

        return sql_expr

    def _read_group_postprocess_groupby(self, groupby_spec, raw_values):
        """ Convert the given values of ``groupby_spec``
        from PostgreSQL to the format returned by method ``_read_group()``.

        The jalaali groupby expressions above return text values, they are
        converted back to gregorian date/datetime values here.
        """
        if self._artarad_is_jalaali():
            fname, seq_fnames, granularity = parse_read_group_spec(groupby_spec)
            field = self._fields.get(fname)
            if (
                field is not None
                and not seq_fnames
                and field.type in ('date', 'datetime')
                and granularity in JALAALI_GRANULARITY
            ):
                raw_values = tuple(
                    self._artarad_jalaali_to_gregorian(value, field.type)
                    for value in raw_values
                )

        return super()._read_group_postprocess_groupby(groupby_spec, raw_values)

    @staticmethod
    def _artarad_jalaali_to_gregorian(value, field_type):
        if not value:
            return value
        try:
            jvalue = jdatetime.datetime.strptime(value, DEFAULT_SERVER_DATETIME_FORMAT)
        except ValueError:
            jvalue = jdatetime.datetime.strptime(value, DEFAULT_SERVER_DATE_FORMAT)
        return jvalue.togregorian() if field_type == 'datetime' else jvalue.date().togregorian()
