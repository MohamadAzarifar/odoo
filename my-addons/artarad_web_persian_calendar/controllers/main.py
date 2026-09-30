# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from odoo.addons.web.controllers.export import CSVExport, ExcelExport
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.http import request

import datetime
import jdatetime


def _to_jalaali(value):
    if isinstance(value, datetime.datetime):
        return jdatetime.datetime.fromgregorian(datetime=value).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    if isinstance(value, datetime.date):
        return jdatetime.datetime.fromgregorian(date=value).strftime(DEFAULT_SERVER_DATE_FORMAT)
    return value


class CSVExportInherit(CSVExport):

    def from_data(self, fields, columns_headers, rows):
        if request.env.user.calendar_type == 'jalaali':
            rows = [[_to_jalaali(value) for value in row] for row in rows]
        return super().from_data(fields, columns_headers, rows)


class ExcelExportInherit(ExcelExport):

    def from_group_data(self, fields, columns_headers, groups):
        if request.env.user.calendar_type == 'jalaali':
            for group_name, group in groups.children.items():
                if group.children:
                    self.from_group_data(fields, columns_headers, groups)

                for data in group.data:
                    for i in range(len(data)):
                        if isinstance(data[i], datetime.datetime):
                            data[i] = jdatetime.datetime.fromgregorian(datetime=data[i]).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        elif isinstance(data[i], datetime.date):
                            data[i] = jdatetime.datetime.fromgregorian(date=data[i]).strftime(DEFAULT_SERVER_DATE_FORMAT)

        return super().from_group_data(fields, columns_headers, groups)


    def from_data(self, fields, columns_headers, rows):
        if request.env.user.calendar_type == 'jalaali':
            for data in rows:
                for i in range(len(data)):
                    if isinstance(data[i], datetime.datetime):
                        data[i] = jdatetime.datetime.fromgregorian(datetime=data[i]).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    elif isinstance(data[i], datetime.date):
                        data[i] = jdatetime.datetime.fromgregorian(date=data[i]).strftime(DEFAULT_SERVER_DATE_FORMAT)
        return super().from_data(fields, columns_headers, rows)